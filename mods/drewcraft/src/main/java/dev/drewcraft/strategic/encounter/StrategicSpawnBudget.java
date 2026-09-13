package dev.drewcraft.strategic.encounter;

/** Mutable per-cycle hard budget shared across all encounter wave fills. */
public final class StrategicSpawnBudget {
    private final int maximum;
    private int consumed;

    public StrategicSpawnBudget(int maximum) {
        if (maximum < 1) throw new IllegalArgumentException("maximum must be positive");
        this.maximum = maximum;
    }

    public int maximum() { return maximum; }
    public int consumed() { return consumed; }
    public int remaining() { return maximum - consumed; }
    public boolean exhausted() { return consumed >= maximum; }

    public boolean tryConsume() {
        if (exhausted()) return false;
        consumed++;
        return true;
    }
}
