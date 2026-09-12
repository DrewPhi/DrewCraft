package dev.drewcraft.strategic.model;

import java.util.Objects;

/** Dimension-aware continuous strategic position that does not require a loaded chunk. */
public record StrategicPosition(String dimension, double x, double z) {
    public StrategicPosition {
        Objects.requireNonNull(dimension, "dimension");
        if (dimension.isBlank()) {
            throw new IllegalArgumentException("dimension must not be blank");
        }
        if (!Double.isFinite(x) || !Double.isFinite(z)) {
            throw new IllegalArgumentException("strategic coordinates must be finite");
        }
    }

    public double distanceTo(StrategicPosition other) {
        requireSameDimension(other);
        return Math.hypot(other.x - x, other.z - z);
    }

    public StrategicPosition moveToward(StrategicPosition target, double distance) {
        requireSameDimension(target);
        if (!Double.isFinite(distance) || distance < 0.0) {
            throw new IllegalArgumentException("distance must be finite and non-negative");
        }
        double total = distanceTo(target);
        if (total == 0.0 || distance >= total) {
            return target;
        }
        double fraction = distance / total;
        return new StrategicPosition(
                dimension,
                x + (target.x - x) * fraction,
                z + (target.z - z) * fraction
        );
    }

    private void requireSameDimension(StrategicPosition other) {
        Objects.requireNonNull(other, "other");
        if (!dimension.equals(other.dimension)) {
            throw new IllegalArgumentException("strategic positions are in different dimensions");
        }
    }
}
