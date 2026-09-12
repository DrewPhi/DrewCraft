package dev.drewcraft.service.vehicle;

import java.util.Objects;
import java.util.UUID;
import net.minecraft.world.phys.Vec3;

/** Upstream-neutral vehicle state used by aviation, radar and later gameplay systems. */
public record VehicleSnapshot(
        UUID id,
        String typeId,
        Vec3 position,
        Vec3 velocityBlocksPerTick,
        double yawDegrees,
        double pitchDegrees,
        double rollDegrees,
        boolean aircraft
) {
    public VehicleSnapshot {
        Objects.requireNonNull(id);
        Objects.requireNonNull(typeId);
        Objects.requireNonNull(position);
        Objects.requireNonNull(velocityBlocksPerTick);
    }
}
