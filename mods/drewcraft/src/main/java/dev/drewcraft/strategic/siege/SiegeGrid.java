package dev.drewcraft.strategic.siege;

import java.util.Arrays;
import java.util.Objects;

/** Small immutable 2D local snapshot. Coordinates are local grid coordinates, never world chunks. */
public final class SiegeGrid {
    private final int width;
    private final int height;
    private final int startX;
    private final int startZ;
    private final int goalX;
    private final int goalZ;
    private final SiegeCell[] cells;

    public SiegeGrid(int width, int height, int startX, int startZ, int goalX, int goalZ, SiegeCell[] cells) {
        if (width < 1 || height < 1 || width > 129 || height > 129) throw new IllegalArgumentException("invalid grid dimensions");
        this.width = width;
        this.height = height;
        requireInside(startX, startZ);
        requireInside(goalX, goalZ);
        this.startX = startX;
        this.startZ = startZ;
        this.goalX = goalX;
        this.goalZ = goalZ;
        Objects.requireNonNull(cells, "cells");
        if (cells.length != width * height) throw new IllegalArgumentException("cell count does not match dimensions");
        this.cells = Arrays.copyOf(cells, cells.length);
        for (SiegeCell cell : this.cells) Objects.requireNonNull(cell, "grid cell");
        if (!cell(startX, startZ).kind().traversable()) throw new IllegalArgumentException("start cell must be traversable");
    }

    public int width() { return width; }
    public int height() { return height; }
    public int startX() { return startX; }
    public int startZ() { return startZ; }
    public int goalX() { return goalX; }
    public int goalZ() { return goalZ; }
    public boolean contains(int x, int z) { return x >= 0 && z >= 0 && x < width && z < height; }
    public SiegeCell cell(int x, int z) { requireInside(x, z); return cells[z * width + x]; }

    public long fingerprint() {
        long hash = 0xcbf29ce484222325L;
        for (SiegeCell cell : cells) {
            hash ^= cell.kind().ordinal() + 1L;
            hash *= 0x100000001b3L;
            hash ^= Double.doubleToLongBits(cell.hardness());
            hash *= 0x100000001b3L;
        }
        hash ^= startX * 31L + startZ;
        hash ^= ((long) goalX << 32) ^ goalZ;
        return hash;
    }

    private void requireInside(int x, int z) {
        if (x < 0 || z < 0 || x >= width || z >= height) throw new IllegalArgumentException("coordinate outside grid: " + x + "," + z);
    }

    public static Builder builder(int width, int height) { return new Builder(width, height); }

    public static final class Builder {
        private final int width;
        private final int height;
        private final SiegeCell[] cells;
        private int startX;
        private int startZ;
        private int goalX;
        private int goalZ;

        private Builder(int width, int height) {
            if (width < 1 || height < 1) throw new IllegalArgumentException("dimensions must be positive");
            this.width = width;
            this.height = height;
            this.cells = new SiegeCell[width * height];
            Arrays.fill(cells, SiegeCell.open());
            this.goalX = width - 1;
            this.goalZ = height - 1;
        }

        public Builder start(int x, int z) { this.startX = x; this.startZ = z; return this; }
        public Builder goal(int x, int z) { this.goalX = x; this.goalZ = z; return this; }
        public Builder set(int x, int z, SiegeCell cell) {
            if (x < 0 || z < 0 || x >= width || z >= height) throw new IllegalArgumentException("coordinate outside grid");
            cells[z * width + x] = Objects.requireNonNull(cell, "cell");
            return this;
        }
        public SiegeGrid build() { return new SiegeGrid(width, height, startX, startZ, goalX, goalZ, cells); }
    }
}
