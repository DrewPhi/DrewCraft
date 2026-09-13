package dev.drewcraft.strategic.siege;

/** Local loaded-world cell semantics used by the bounded BP6 breach planner. */
public enum SiegeCellKind {
    OPEN(false, 1.0),
    DOOR(true, 3.0),
    GATE(true, 2.5),
    WEAK_BARRIER(true, 5.0),
    SOLID_BARRIER(true, 18.0),
    DECORATIVE(true, 80.0),
    PROTECTED(false, Double.POSITIVE_INFINITY);

    private final boolean breachable;
    private final double baseCost;

    SiegeCellKind(boolean breachable, double baseCost) {
        this.breachable = breachable;
        this.baseCost = baseCost;
    }

    public boolean breachable() { return breachable; }
    public boolean traversable() { return this == OPEN || breachable; }
    public double baseCost() { return baseCost; }
}
