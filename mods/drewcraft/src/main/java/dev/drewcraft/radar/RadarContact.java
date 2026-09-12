package dev.drewcraft.radar;

import java.util.Objects;
import java.util.UUID;
import net.minecraft.world.phys.Vec3;

public record RadarContact(
        UUID targetId,
        String typeId,
        Vec3 position,
        double rangeBlocks,
        double bearingDegrees,
        double relativeAltitudeBlocks,
        double radialVelocityBlocksPerTick,
        boolean aircraft,
        TerrainVisibility terrainVisibility,
        double quality01
) {
    public RadarContact {
        Objects.requireNonNull(targetId);
        Objects.requireNonNull(typeId);
        Objects.requireNonNull(position);
        Objects.requireNonNull(terrainVisibility);
        quality01 = Math.max(0.0, Math.min(1.0, quality01));
    }
}
