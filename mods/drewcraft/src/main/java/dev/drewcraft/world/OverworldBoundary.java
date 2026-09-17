package dev.drewcraft.world;

/** Circular temporary exploration boundary used only in the Overworld. */
public record OverworldBoundary(double centerX, double centerZ, double radiusBlocks) {
    private static final double SAFE_MARGIN_BLOCKS = 8.0;

    public OverworldBoundary {
        if (!Double.isFinite(centerX) || !Double.isFinite(centerZ)
                || !Double.isFinite(radiusBlocks) || radiusBlocks <= SAFE_MARGIN_BLOCKS) {
            throw new IllegalArgumentException("invalid overworld boundary");
        }
    }

    public boolean contains(double x, double z) {
        double dx = x - centerX;
        double dz = z - centerZ;
        return dx * dx + dz * dz <= radiusBlocks * radiusBlocks;
    }

    public Position clampInside(double x, double z) {
        if (contains(x, z)) {
            return new Position(x, z);
        }
        double dx = x - centerX;
        double dz = z - centerZ;
        double distance = Math.hypot(dx, dz);
        double safeRadius = radiusBlocks - SAFE_MARGIN_BLOCKS;
        return new Position(centerX + dx / distance * safeRadius, centerZ + dz / distance * safeRadius);
    }

    public record Position(double x, double z) {
    }
}
