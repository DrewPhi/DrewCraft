package dev.drewcraft.strategic.siege;

import java.util.Objects;

/** Immutable local cell scored by the pure siege planner. */
public record SiegeCell(SiegeCellKind kind, double hardness) {
    public SiegeCell {
        kind = Objects.requireNonNull(kind, "kind");
        if (!Double.isFinite(hardness) || hardness < 0.0) {
            throw new IllegalArgumentException("hardness must be finite and non-negative");
        }
    }

    public static SiegeCell open() { return new SiegeCell(SiegeCellKind.OPEN, 0.0); }
    public static SiegeCell protectedCell() { return new SiegeCell(SiegeCellKind.PROTECTED, 0.0); }

    public double traversalCost() {
        if (!kind.traversable()) return Double.POSITIVE_INFINITY;
        if (kind == SiegeCellKind.OPEN) return kind.baseCost();
        return kind.baseCost() + Math.min(50.0, hardness * 4.0);
    }
}
