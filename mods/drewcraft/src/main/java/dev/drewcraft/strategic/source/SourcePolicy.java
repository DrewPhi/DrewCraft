package dev.drewcraft.strategic.source;

/** V1 production defaults. BP5 may replace composition/target selection with richer faction data. */
public record SourcePolicy(int initialBudget, int launchStrength, long cooldownTicks, double movementSpeedBlocksPerSecond) {
    public SourcePolicy {
        if (initialBudget < 0) throw new IllegalArgumentException("initialBudget must be non-negative");
        if (launchStrength <= 0) throw new IllegalArgumentException("launchStrength must be positive");
        if (cooldownTicks < 1) throw new IllegalArgumentException("cooldownTicks must be positive");
        if (!Double.isFinite(movementSpeedBlocksPerSecond) || movementSpeedBlocksPerSecond <= 0.0) {
            throw new IllegalArgumentException("movement speed must be finite and positive");
        }
    }

    public static SourcePolicy forClass(SourceClass sourceClass) {
        return switch (sourceClass) {
            case TEST -> new SourcePolicy(48, 12, 200L, 2.5);
            case CAMP -> new SourcePolicy(72, 12, 12000L, 2.25);
            case FORT -> new SourcePolicy(144, 18, 18000L, 2.1);
            case CITY -> new SourcePolicy(288, 24, 24000L, 2.0);
            case RUIN -> new SourcePolicy(96, 12, 16000L, 2.15);
            case STRONGHOLD -> new SourcePolicy(384, 32, 30000L, 1.9);
        };
    }
}
