package dev.drewcraft.strategic.source;

import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.strategic.faction.StrategicFactionCatalog;
import dev.drewcraft.strategic.faction.StrategicForceTemplate;
import dev.drewcraft.strategic.faction.StrategicTargetPolicy;
import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.model.StrategicMission;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicTargetKnowledge;
import dev.drewcraft.strategic.routing.StrategicRoutingService;
import java.nio.charset.StandardCharsets;
import java.util.Comparator;
import java.util.UUID;

/** BP5 planner: source -> faction template -> explainable objective -> bounded cached route. */
public final class SourceLaunchPlanner {
    private SourceLaunchPlanner() {
    }

    public static PlanResult plan(SourceRecord source, long gameTime) {
        return plan(null, source, gameTime);
    }

    public static PlanResult plan(DrewCraftSavedData data, SourceRecord source, long gameTime) {
        StrategicForceTemplate template = StrategicFactionCatalog.defaultCatalog()
                .select(source.factionId(), source.sourceClass(), source.launchSerial(),
                        source.populationBudget(), source.launchStrength())
                .orElse(null);
        if (template == null) return new PlanResult(null, "no_affordable_template");

        int strength = template.desiredStrength(source.launchStrength());
        TargetSelection target = chooseTarget(data, source, template);
        StrategicPosition start = new StrategicPosition(
                source.dimension(), source.anchorX() + 0.5, source.anchorZ() + 0.5
        );
        StrategicRoutingService.RoutingResult route = StrategicRoutingService.plan(start, target.position());
        if (!route.success()) return new PlanResult(null, route.stats().status());

        long serial = source.launchSerial();
        UUID groupId = UUID.nameUUIDFromBytes(
                ("drewcraft-source-group-v2|" + source.sourceId() + "|" + serial + "|" + template.id())
                        .getBytes(StandardCharsets.UTF_8)
        );
        StrategicMission mission = new StrategicMission(
                template.id(), target.knowledge(), target.detail(), target.position(), Math.max(0L, gameTime)
        );
        StrategicGroup group = new StrategicGroup(
                groupId,
                source.factionId(),
                template.groupType(),
                source.sourceId(),
                start,
                route.route(),
                mission,
                source.movementSpeedBlocksPerSecond(),
                template.compositionForStrength(strength),
                strength,
                StrategicGroupState.TRAVELING,
                Math.max(0L, gameTime)
        );
        return new PlanResult(group, "ok:" + template.id());
    }

    private static TargetSelection chooseTarget(DrewCraftSavedData data, SourceRecord source,
                                                StrategicForceTemplate template) {
        if (template.targetPolicy() == StrategicTargetPolicy.ALLIED_REINFORCEMENT && data != null) {
            SourceRecord allied = data.sourceRecords().stream()
                    .filter(candidate -> !candidate.sourceId().equals(source.sourceId()))
                    .filter(candidate -> candidate.state() != SourceState.CLEARED)
                    .filter(candidate -> candidate.dimension().equals(source.dimension()))
                    .filter(candidate -> candidate.factionId().equals(source.factionId()))
                    .min(Comparator.comparingDouble(candidate -> distanceSquared(source, candidate)))
                    .orElse(null);
            if (allied != null) {
                return new TargetSelection(
                        new StrategicPosition(allied.dimension(), allied.anchorX() + 0.5, allied.anchorZ() + 0.5),
                        StrategicTargetKnowledge.ALLIED_SOURCE_LOCATION,
                        "persistent allied source " + allied.sourceId()
                );
            }
        }

        StrategicPosition position = deterministicRegionalTarget(source, template);
        return switch (template.targetPolicy()) {
            case LOCAL_PATROL -> new TargetSelection(
                    position, StrategicTargetKnowledge.SOURCE_GEOGRAPHY,
                    "local patrol route derived from source geography"
            );
            case REGIONAL_ROAM -> new TargetSelection(
                    position, StrategicTargetKnowledge.SOURCE_GEOGRAPHY,
                    "regional roaming route derived from source geography"
            );
            case SCOUTED_EXPEDITION -> new TargetSelection(
                    position, StrategicTargetKnowledge.SCOUTED_REGION,
                    "deterministic precomputed scouting waypoint; no player position queried"
            );
            case ALLIED_REINFORCEMENT -> new TargetSelection(
                    position, StrategicTargetKnowledge.SOURCE_GEOGRAPHY,
                    "no allied source available; fallback regional route from source geography"
            );
        };
    }

    private static StrategicPosition deterministicRegionalTarget(SourceRecord source,
                                                                 StrategicForceTemplate template) {
        long seed = source.sourceId().getMostSignificantBits()
                ^ Long.rotateLeft(source.sourceId().getLeastSignificantBits(), 17)
                ^ Long.rotateLeft(source.launchSerial() * 0x9E3779B97F4A7C15L, 9)
                ^ template.id().hashCode();
        double angleUnit = ((seed >>> 11) & ((1L << 53) - 1)) / (double) (1L << 53);
        long mixed = seed * 0xD6E8FEB86659FD93L + 0x9E3779B97F4A7C15L;
        double distanceUnit = ((mixed >>> 11) & ((1L << 53) - 1)) / (double) (1L << 53);
        double angle = angleUnit * Math.PI * 2.0;
        double distance = template.minDistanceBlocks()
                + distanceUnit * (template.maxDistanceBlocks() - template.minDistanceBlocks());
        return new StrategicPosition(
                source.dimension(),
                source.anchorX() + 0.5 + Math.cos(angle) * distance,
                source.anchorZ() + 0.5 + Math.sin(angle) * distance
        );
    }

    private static double distanceSquared(SourceRecord first, SourceRecord second) {
        double dx = first.anchorX() - second.anchorX();
        double dz = first.anchorZ() - second.anchorZ();
        return dx * dx + dz * dz;
    }

    public record PlanResult(StrategicGroup group, String status) {
        public boolean success() { return group != null; }
    }

    private record TargetSelection(StrategicPosition position, StrategicTargetKnowledge knowledge, String detail) {
    }
}
