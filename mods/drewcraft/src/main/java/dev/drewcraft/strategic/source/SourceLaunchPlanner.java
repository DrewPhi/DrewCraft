package dev.drewcraft.strategic.source;

import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.routing.StrategicRoutingService;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.UUID;

/**
 * Minimal BP4 launch planner. BP5 owns richer faction composition/objective selection; this planner
 * proves that a persistent source can commit a real routed strategic population.
 */
public final class SourceLaunchPlanner {
    private SourceLaunchPlanner() {
    }

    public static PlanResult plan(SourceRecord source, long gameTime) {
        StrategicPosition start = new StrategicPosition(source.dimension(), source.anchorX() + 0.5, source.anchorZ() + 0.5);
        StrategicPosition destination = deterministicDestination(source);
        StrategicRoutingService.RoutingResult route = StrategicRoutingService.plan(start, destination);
        if (!route.success()) return new PlanResult(null, route.stats().status());

        long serial = source.launchSerial();
        UUID groupId = UUID.nameUUIDFromBytes(
                ("drewcraft-source-group-v1|" + source.sourceId() + "|" + serial).getBytes(StandardCharsets.UTF_8)
        );
        StrategicGroup group = new StrategicGroup(
                groupId,
                source.factionId(),
                StrategicGroupType.PATROL,
                source.sourceId(),
                start,
                route.route(),
                source.movementSpeedBlocksPerSecond(),
                Map.of("minecraft:zombie", source.launchStrength()),
                source.launchStrength(),
                StrategicGroupState.TRAVELING,
                Math.max(0L, gameTime)
        );
        return new PlanResult(group, "ok");
    }

    private static StrategicPosition deterministicDestination(SourceRecord source) {
        long seed = source.sourceId().getMostSignificantBits()
                ^ Long.rotateLeft(source.sourceId().getLeastSignificantBits(), 17)
                ^ Long.rotateLeft(source.launchSerial() * 0x9E3779B97F4A7C15L, 9);
        double unit = ((seed >>> 11) & ((1L << 53) - 1)) / (double) (1L << 53);
        double angle = unit * Math.PI * 2.0;
        double distance = switch (source.sourceClass()) {
            case TEST -> 512.0;
            case CAMP -> 1024.0;
            case RUIN -> 1280.0;
            case FORT -> 1536.0;
            case CITY -> 2048.0;
            case STRONGHOLD -> 2560.0;
        };
        return new StrategicPosition(
                source.dimension(),
                source.anchorX() + 0.5 + Math.cos(angle) * distance,
                source.anchorZ() + 0.5 + Math.sin(angle) * distance
        );
    }

    public record PlanResult(StrategicGroup group, String status) {
        public boolean success() { return group != null; }
    }
}
