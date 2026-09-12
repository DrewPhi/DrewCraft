package dev.drewcraft.strategic.routing;

import dev.drewcraft.strategic.model.StrategicPosition;
import java.util.Objects;

/** Coarse routing cell independent of Minecraft chunk load state. */
public record StrategicCell(String dimension, int x, int z) {
    public StrategicCell {
        Objects.requireNonNull(dimension, "dimension");
        if (dimension.isBlank()) {
            throw new IllegalArgumentException("dimension must not be blank");
        }
    }

    public static StrategicCell fromPosition(StrategicPosition position, int cellSizeBlocks) {
        Objects.requireNonNull(position, "position");
        if (cellSizeBlocks <= 0) {
            throw new IllegalArgumentException("cellSizeBlocks must be positive");
        }
        return new StrategicCell(
                position.dimension(),
                Math.floorDiv((int) Math.floor(position.x()), cellSizeBlocks),
                Math.floorDiv((int) Math.floor(position.z()), cellSizeBlocks)
        );
    }

    public StrategicPosition center(int cellSizeBlocks) {
        if (cellSizeBlocks <= 0) {
            throw new IllegalArgumentException("cellSizeBlocks must be positive");
        }
        double half = cellSizeBlocks / 2.0;
        return new StrategicPosition(
                dimension,
                x * (double) cellSizeBlocks + half,
                z * (double) cellSizeBlocks + half
        );
    }

    public StrategicCell offset(int dx, int dz) {
        return new StrategicCell(dimension, x + dx, z + dz);
    }

    public double centerDistanceCells(StrategicCell other) {
        requireSameDimension(other);
        return Math.hypot(other.x - x, other.z - z);
    }

    private void requireSameDimension(StrategicCell other) {
        Objects.requireNonNull(other, "other");
        if (!dimension.equals(other.dimension)) {
            throw new IllegalArgumentException("routing cells are in different dimensions");
        }
    }
}
