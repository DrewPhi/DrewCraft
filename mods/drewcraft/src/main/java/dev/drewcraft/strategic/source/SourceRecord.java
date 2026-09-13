package dev.drewcraft.strategic.source;

import java.util.Objects;
import java.util.Optional;
import java.util.UUID;

/** Persistent authority for one generated hostile source. The physical core is never authoritative. */
public final class SourceRecord {
    public static final int CURRENT_SCHEMA_VERSION = 1;

    private final UUID sourceId;
    private final String dimension;
    private final String structureId;
    private final int anchorX;
    private final int anchorY;
    private final int anchorZ;
    private final SourceCorePosition corePosition;
    private final SourceClass sourceClass;
    private final String factionId;
    private final int launchStrength;
    private final long launchCooldownTicks;
    private final double movementSpeedBlocksPerSecond;

    private SourceState state;
    private int populationBudget;
    private long nextActionGameTime;
    private long launchSerial;
    private long generation;
    private Long clearedAtGameTime;
    private String clearCause;
    private String clearedBy;

    public SourceRecord(UUID sourceId, String dimension, String structureId,
                        int anchorX, int anchorY, int anchorZ,
                        SourceCorePosition corePosition, SourceClass sourceClass, String factionId,
                        SourceState state, int populationBudget, int launchStrength,
                        long launchCooldownTicks, double movementSpeedBlocksPerSecond,
                        long nextActionGameTime, long launchSerial, long generation,
                        Long clearedAtGameTime, String clearCause, String clearedBy) {
        this.sourceId = Objects.requireNonNull(sourceId, "sourceId");
        this.dimension = requireNonBlank(dimension, "dimension");
        this.structureId = requireNonBlank(structureId, "structureId");
        this.anchorX = anchorX;
        this.anchorY = anchorY;
        this.anchorZ = anchorZ;
        this.corePosition = Objects.requireNonNull(corePosition, "corePosition");
        this.sourceClass = Objects.requireNonNull(sourceClass, "sourceClass");
        this.factionId = requireNonBlank(factionId, "factionId");
        this.state = Objects.requireNonNull(state, "state");
        if (!dimension.equals(corePosition.dimension())) throw new IllegalArgumentException("core/source dimension mismatch");
        if (populationBudget < 0) throw new IllegalArgumentException("populationBudget must be non-negative");
        if (launchStrength <= 0) throw new IllegalArgumentException("launchStrength must be positive");
        if (launchCooldownTicks <= 0) throw new IllegalArgumentException("launchCooldownTicks must be positive");
        if (!Double.isFinite(movementSpeedBlocksPerSecond) || movementSpeedBlocksPerSecond <= 0.0) throw new IllegalArgumentException("movement speed must be finite and positive");
        this.populationBudget = populationBudget;
        this.launchStrength = launchStrength;
        this.launchCooldownTicks = launchCooldownTicks;
        this.movementSpeedBlocksPerSecond = movementSpeedBlocksPerSecond;
        this.nextActionGameTime = Math.max(0L, nextActionGameTime);
        this.launchSerial = Math.max(0L, launchSerial);
        this.generation = Math.max(0L, generation);
        this.clearedAtGameTime = clearedAtGameTime;
        this.clearCause = normalizeOptional(clearCause);
        this.clearedBy = normalizeOptional(clearedBy);
        if (state == SourceState.CLEARED && clearedAtGameTime == null) {
            throw new IllegalArgumentException("cleared source requires clearedAtGameTime");
        }
    }

    public static SourceRecord discovered(SourceDescriptor descriptor, long gameTime) {
        SourcePolicy policy = SourcePolicy.forClass(descriptor.sourceClass());
        return new SourceRecord(
                descriptor.stableSourceId(), descriptor.dimension(), descriptor.structureId(),
                descriptor.anchorX(), descriptor.anchorY(), descriptor.anchorZ(), descriptor.corePosition(),
                descriptor.sourceClass(), descriptor.factionId(), SourceState.INTACT,
                policy.initialBudget(), policy.launchStrength(), policy.cooldownTicks(),
                policy.movementSpeedBlocksPerSecond(), Math.max(0L, gameTime) + policy.cooldownTicks(),
                0L, 0L, null, null, null
        );
    }

    public UUID sourceId() { return sourceId; }
    public String dimension() { return dimension; }
    public String structureId() { return structureId; }
    public int anchorX() { return anchorX; }
    public int anchorY() { return anchorY; }
    public int anchorZ() { return anchorZ; }
    public SourceCorePosition corePosition() { return corePosition; }
    public SourceClass sourceClass() { return sourceClass; }
    public String factionId() { return factionId; }
    public SourceState state() { return state; }
    public int populationBudget() { return populationBudget; }
    public int launchStrength() { return launchStrength; }
    public long launchCooldownTicks() { return launchCooldownTicks; }
    public double movementSpeedBlocksPerSecond() { return movementSpeedBlocksPerSecond; }
    public long nextActionGameTime() { return nextActionGameTime; }
    public long launchSerial() { return launchSerial; }
    public long generation() { return generation; }
    public Optional<Long> clearedAtGameTime() { return Optional.ofNullable(clearedAtGameTime); }
    public Optional<String> clearCause() { return Optional.ofNullable(clearCause); }
    public Optional<String> clearedBy() { return Optional.ofNullable(clearedBy); }

    public boolean canLaunch(long gameTime) {
        return state != SourceState.CLEARED
                && populationBudget >= launchStrength
                && gameTime >= nextActionGameTime;
    }

    public boolean identityMatches(SourceDescriptor descriptor) {
        return sourceId.equals(descriptor.stableSourceId())
                && dimension.equals(descriptor.dimension())
                && structureId.equals(descriptor.structureId())
                && anchorX == descriptor.anchorX()
                && anchorY == descriptor.anchorY()
                && anchorZ == descriptor.anchorZ()
                && corePosition.equals(descriptor.corePosition())
                && sourceClass == descriptor.sourceClass()
                && factionId.equals(descriptor.factionId());
    }

    /** Commit one production event after the caller has planned the route against this generation. */
    public boolean commitLaunch(long expectedGeneration, long gameTime) {
        if (generation != expectedGeneration || !canLaunch(gameTime)) return false;
        populationBudget -= launchStrength;
        launchSerial++;
        nextActionGameTime = Math.max(0L, gameTime) + launchCooldownTicks;
        generation++;
        return true;
    }

    public boolean clear(long gameTime, String cause, String actor) {
        if (state == SourceState.CLEARED) return false;
        state = SourceState.CLEARED;
        generation++;
        clearedAtGameTime = Math.max(0L, gameTime);
        clearCause = normalizeOptional(cause);
        clearedBy = normalizeOptional(actor);
        nextActionGameTime = Long.MAX_VALUE;
        return true;
    }

    /** Back off a failed route attempt without consuming population. */
    public void postpone(long gameTime, long delayTicks) {
        if (state == SourceState.CLEARED) return;
        nextActionGameTime = Math.max(nextActionGameTime, Math.max(0L, gameTime) + Math.max(1L, delayTicks));
        generation++;
    }

    private static String requireNonBlank(String value, String name) {
        Objects.requireNonNull(value, name);
        if (value.isBlank()) throw new IllegalArgumentException(name + " must not be blank");
        return value;
    }

    private static String normalizeOptional(String value) {
        return value == null || value.isBlank() ? null : value;
    }
}
