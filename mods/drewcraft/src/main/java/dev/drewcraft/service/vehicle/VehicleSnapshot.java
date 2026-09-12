package dev.drewcraft.service.vehicle;

import java.util.UUID;
import net.minecraft.world.phys.Vec3;

/**
 * Upstream-neutral vehicle state used by aviation, radar and later gameplay systems.
 */
public record VehicleSnapshot(
        UUID id,
        Vec3 position,
        Vec3 velocity,
        double yawDegrees,
        double pitchDegrees,
        double rollDegrees,
        boolean aircraft
) {
}
