package dev.drewcraft.strategic.routing;

/** Coarse strategic traversal categories. Multipliers scale effective route cost. */
public enum StrategicTerrainClass {
    ROAD(0.65, true),
    BRIDGE(0.80, true),
    NORMAL(1.00, true),
    UNKNOWN(1.25, true),
    DIFFICULT(1.75, true),
    WATER(2.50, true),
    BLOCKED(Double.POSITIVE_INFINITY, false);

    private final double multiplier;
    private final boolean traversable;

    StrategicTerrainClass(double multiplier, boolean traversable) {
        this.multiplier = multiplier;
        this.traversable = traversable;
    }

    public double multiplier() {
        return multiplier;
    }

    public boolean traversable() {
        return traversable;
    }

    public static double minimumTraversableMultiplier() {
        double minimum = Double.POSITIVE_INFINITY;
        for (StrategicTerrainClass value : values()) {
            if (value.traversable) {
                minimum = Math.min(minimum, value.multiplier);
            }
        }
        return minimum;
    }
}
