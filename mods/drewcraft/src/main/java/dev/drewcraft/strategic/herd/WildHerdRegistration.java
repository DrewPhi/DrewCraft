package dev.drewcraft.strategic.herd;

import dev.drewcraft.persistence.DrewCraftSavedData;
import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.model.StrategicMission;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicRoute;
import dev.drewcraft.strategic.model.StrategicTargetKnowledge;
import dev.drewcraft.strategic.routing.StrategicRoutingService;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;

/**
 * Explicit BP7 herd registration. This class never scans, absorbs, or mutates ordinary Minecraft
 * animals. Herd authority begins only from an explicit descriptor supplied by world-build tooling,
 * a future structure/biome hook, or an admin command.
 */
public final class WildHerdRegistration {
    private WildHerdRegistration() {
    }

    public static RegistrationResult register(DrewCraftSavedData data, WildHerdDescriptor descriptor,
                                              long gameTime) {
        return register(data, descriptor, gameTime, (start, destination) -> {
            StrategicRoutingService.RoutingResult result = StrategicRoutingService.plan(start, destination);
            return result.success() ? Optional.of(result.route()) : Optional.empty();
        });
    }

    static RegistrationResult register(DrewCraftSavedData data, WildHerdDescriptor descriptor,
                                       long gameTime, RoutePlanner planner) {
        Objects.requireNonNull(data, "data");
        Objects.requireNonNull(descriptor, "descriptor");
        Objects.requireNonNull(planner, "planner");
        UUID herdId = descriptor.stableHerdId();

        StrategicGroup existing = data.strategicGroup(herdId).orElse(null);
        if (existing != null) {
            validateExisting(existing, descriptor);
            return new RegistrationResult(existing, false, "already_registered");
        }

        StrategicPosition start = descriptor.origin();
        StrategicPosition destination = descriptor.destination();
        StrategicRoute route = planner.plan(start, destination).orElse(null);
        if (route == null) return new RegistrationResult(null, false, "route_failed");
        if (!route.destination().equals(destination)) {
            throw new IllegalStateException("herd route destination does not match descriptor destination");
        }

        StrategicMission mission = new StrategicMission(
                descriptor.templateId(),
                StrategicTargetKnowledge.MIGRATION_ROUTE,
                "explicit wild-herd migration seed; no live animal was absorbed",
                destination,
                Math.max(0L, gameTime)
        );
        StrategicGroup candidate = new StrategicGroup(
                herdId,
                WildHerdDescriptor.WILDLIFE_FACTION_ID,
                StrategicGroupType.HERD,
                null,
                start,
                route,
                mission,
                descriptor.movementSpeedBlocksPerSecond(),
                Map.of(descriptor.speciesEntityId(), descriptor.count()),
                descriptor.count(),
                route.arrived() ? StrategicGroupState.ARRIVED : StrategicGroupState.TRAVELING,
                Math.max(0L, gameTime)
        );

        // Route planning deliberately occurs outside the monitor. Re-check under one authority so
        // concurrent explicit registrations cannot reset an already-moving/casualty-bearing herd.
        synchronized (data) {
            existing = data.strategicGroup(herdId).orElse(null);
            if (existing != null) {
                validateExisting(existing, descriptor);
                return new RegistrationResult(existing, false, "already_registered");
            }
            data.upsertStrategicGroup(candidate);
            return new RegistrationResult(candidate, true, "created");
        }
    }

    private static void validateExisting(StrategicGroup group, WildHerdDescriptor descriptor) {
        if (group.groupType() != StrategicGroupType.HERD
                || !group.factionId().equals(WildHerdDescriptor.WILDLIFE_FACTION_ID)
                || !group.mission().templateId().equals(descriptor.templateId())
                || !group.mission().target().equals(descriptor.destination())) {
            throw new IllegalStateException("stable herd id resolves to conflicting herd identity: " + group.groupId());
        }
    }

    @FunctionalInterface
    interface RoutePlanner {
        Optional<StrategicRoute> plan(StrategicPosition start, StrategicPosition destination);
    }

    public record RegistrationResult(StrategicGroup group, boolean created, String status) {
        public boolean success() { return group != null; }
    }
}
