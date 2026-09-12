package dev.drewcraft.strategic.model;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;

/** Persistent authority for an important unloaded population. Contains no Minecraft entities. */
public final class StrategicGroup {
    public static final int CURRENT_SCHEMA_VERSION = 1;

    private final UUID groupId;
    private final String factionId;
    private final StrategicGroupType groupType;
    private final UUID sourceId;
    private final Map<String, Integer> composition;
    private StrategicPosition position;
    private final StrategicRoute route;
    private final double movementSpeedBlocksPerSecond;
    private int totalStrength;
    private StrategicGroupState state;
    private long lastSimulatedGameTime;

    public StrategicGroup(
            UUID groupId,
            String factionId,
            StrategicGroupType groupType,
            UUID sourceId,
            StrategicPosition position,
            StrategicRoute route,
            double movementSpeedBlocksPerSecond,
            Map<String, Integer> composition,
            int totalStrength,
            StrategicGroupState state,
            long lastSimulatedGameTime
    ) {
        this.groupId = Objects.requireNonNull(groupId, "groupId");
        this.factionId = requireNonBlank(factionId, "factionId");
        this.groupType = Objects.requireNonNull(groupType, "groupType");
        this.sourceId = sourceId;
        this.position = Objects.requireNonNull(position, "position");
        this.route = Objects.requireNonNull(route, "route");
        if (!position.dimension().equals(route.destination().dimension())) {
            throw new IllegalArgumentException("group position and route must share a dimension");
        }
        if (!Double.isFinite(movementSpeedBlocksPerSecond) || movementSpeedBlocksPerSecond <= 0.0) {
            throw new IllegalArgumentException("movement speed must be finite and positive");
        }
        this.movementSpeedBlocksPerSecond = movementSpeedBlocksPerSecond;
        this.composition = sanitizeComposition(composition);
        if (totalStrength < 0) {
            throw new IllegalArgumentException("totalStrength must be non-negative");
        }
        this.totalStrength = totalStrength;
        this.state = Objects.requireNonNull(state, "state");
        this.lastSimulatedGameTime = Math.max(0L, lastSimulatedGameTime);
    }

    public static StrategicGroup testGroup(StrategicPosition start, StrategicPosition destination, long gameTime) {
        return new StrategicGroup(
                UUID.randomUUID(),
                "drewcraft:test",
                StrategicGroupType.TEST,
                null,
                start,
                StrategicRoute.between(start, destination),
                2.5,
                Map.of("minecraft:zombie", 20),
                20,
                StrategicGroupState.TRAVELING,
                Math.max(0L, gameTime)
        );
    }

    public UUID groupId() {
        return groupId;
    }

    public String factionId() {
        return factionId;
    }

    public StrategicGroupType groupType() {
        return groupType;
    }

    public Optional<UUID> sourceId() {
        return Optional.ofNullable(sourceId);
    }

    public StrategicPosition position() {
        return position;
    }

    public StrategicPosition destination() {
        return route.destination();
    }

    public StrategicRoute route() {
        return route;
    }

    public double movementSpeedBlocksPerSecond() {
        return movementSpeedBlocksPerSecond;
    }

    public Map<String, Integer> composition() {
        return composition;
    }

    public int totalStrength() {
        return totalStrength;
    }

    public StrategicGroupState state() {
        return state;
    }

    public long lastSimulatedGameTime() {
        return lastSimulatedGameTime;
    }

    public double etaSeconds() {
        if (state != StrategicGroupState.TRAVELING) {
            return 0.0;
        }
        return route.remainingDistanceFrom(position) / movementSpeedBlocksPerSecond;
    }

    /**
     * Advances from the last recorded game-time anchor to {@code currentGameTime}. Excess elapsed
     * time above the catch-up cap is intentionally discarded so a long pause cannot create an
     * unbounded single-cycle workload or surprise teleport.
     */
    public AdvanceResult advanceToGameTime(long currentGameTime, double maxCatchupSeconds) {
        if (!Double.isFinite(maxCatchupSeconds) || maxCatchupSeconds < 0.0) {
            throw new IllegalArgumentException("maxCatchupSeconds must be finite and non-negative");
        }
        if (currentGameTime <= lastSimulatedGameTime) {
            return AdvanceResult.none();
        }

        double rawElapsedSeconds = (currentGameTime - lastSimulatedGameTime) / 20.0;
        double elapsedSeconds = Math.min(rawElapsedSeconds, maxCatchupSeconds);
        boolean clamped = rawElapsedSeconds > maxCatchupSeconds;
        lastSimulatedGameTime = currentGameTime;
        return advanceSecondsInternal(elapsedSeconds, clamped);
    }

    /** Admin/test-only explicit advancement that does not alter the scheduler's game-time anchor. */
    public AdvanceResult advanceBySeconds(double elapsedSeconds, double maxCatchupSeconds) {
        if (!Double.isFinite(elapsedSeconds) || elapsedSeconds < 0.0) {
            throw new IllegalArgumentException("elapsedSeconds must be finite and non-negative");
        }
        if (!Double.isFinite(maxCatchupSeconds) || maxCatchupSeconds < 0.0) {
            throw new IllegalArgumentException("maxCatchupSeconds must be finite and non-negative");
        }
        boolean clamped = elapsedSeconds > maxCatchupSeconds;
        return advanceSecondsInternal(Math.min(elapsedSeconds, maxCatchupSeconds), clamped);
    }

    private AdvanceResult advanceSecondsInternal(double elapsedSeconds, boolean clamped) {
        if (state != StrategicGroupState.TRAVELING || elapsedSeconds <= 0.0) {
            return new AdvanceResult(elapsedSeconds, 0.0, false, clamped);
        }
        double movementBudget = movementSpeedBlocksPerSecond * elapsedSeconds;
        StrategicRoute.AdvanceResult routeAdvance = route.advance(position, movementBudget);
        position = routeAdvance.position();
        boolean arrivedNow = routeAdvance.arrived();
        if (arrivedNow) {
            state = StrategicGroupState.ARRIVED;
        }
        return new AdvanceResult(elapsedSeconds, routeAdvance.distanceMoved(), arrivedNow, clamped);
    }

    private static Map<String, Integer> sanitizeComposition(Map<String, Integer> input) {
        Objects.requireNonNull(input, "composition");
        LinkedHashMap<String, Integer> copy = new LinkedHashMap<>();
        input.forEach((key, count) -> {
            String id = requireNonBlank(key, "composition id");
            if (count == null || count < 0) {
                throw new IllegalArgumentException("composition counts must be non-negative");
            }
            if (count > 0) {
                copy.put(id, count);
            }
        });
        return Collections.unmodifiableMap(copy);
    }

    private static String requireNonBlank(String value, String name) {
        Objects.requireNonNull(value, name);
        if (value.isBlank()) {
            throw new IllegalArgumentException(name + " must not be blank");
        }
        return value;
    }

    public record AdvanceResult(double elapsedSeconds, double distanceMoved, boolean arrived, boolean catchupClamped) {
        public static AdvanceResult none() {
            return new AdvanceResult(0.0, 0.0, false, false);
        }

        public boolean changedPosition() {
            return distanceMoved > 0.0;
        }
    }
}
