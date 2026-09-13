package dev.drewcraft.strategic.model;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;

/** Persistent authority for an important unloaded population. Contains no Minecraft entities. */
public final class StrategicGroup {
    public static final int CURRENT_SCHEMA_VERSION = 3;

    private final UUID groupId;
    private final String factionId;
    private final StrategicGroupType groupType;
    private final UUID sourceId;
    private final LinkedHashMap<String, Integer> composition;
    private StrategicPosition position;
    private StrategicRoute route;
    private StrategicMission mission;
    private final double movementSpeedBlocksPerSecond;
    private int totalStrength;
    private StrategicGroupState state;
    private long lastSimulatedGameTime;

    /** Backward-compatible constructor for pre-BP5 callers; mission is recorded as legacy route knowledge. */
    public StrategicGroup(UUID groupId, String factionId, StrategicGroupType groupType, UUID sourceId,
                          StrategicPosition position, StrategicRoute route, double movementSpeedBlocksPerSecond,
                          Map<String, Integer> composition, int totalStrength, StrategicGroupState state,
                          long lastSimulatedGameTime) {
        this(groupId, factionId, groupType, sourceId, position, route,
                StrategicMission.legacy(route.destination(), lastSimulatedGameTime),
                movementSpeedBlocksPerSecond, composition, totalStrength, state, lastSimulatedGameTime);
    }

    public StrategicGroup(UUID groupId, String factionId, StrategicGroupType groupType, UUID sourceId,
                          StrategicPosition position, StrategicRoute route, StrategicMission mission,
                          double movementSpeedBlocksPerSecond, Map<String, Integer> composition,
                          int totalStrength, StrategicGroupState state, long lastSimulatedGameTime) {
        this.groupId = Objects.requireNonNull(groupId, "groupId");
        this.factionId = requireNonBlank(factionId, "factionId");
        this.groupType = Objects.requireNonNull(groupType, "groupType");
        this.sourceId = sourceId;
        this.position = Objects.requireNonNull(position, "position");
        this.route = Objects.requireNonNull(route, "route");
        this.mission = Objects.requireNonNull(mission, "mission");
        if (!position.dimension().equals(route.destination().dimension())) {
            throw new IllegalArgumentException("group position and route must share a dimension");
        }
        if (!mission.target().dimension().equals(position.dimension())) {
            throw new IllegalArgumentException("mission target dimension must match group dimension");
        }
        if (!mission.target().equals(route.destination())) {
            throw new IllegalArgumentException("mission target must equal route destination");
        }
        if (!Double.isFinite(movementSpeedBlocksPerSecond) || movementSpeedBlocksPerSecond <= 0.0) {
            throw new IllegalArgumentException("movement speed must be finite and positive");
        }
        this.movementSpeedBlocksPerSecond = movementSpeedBlocksPerSecond;
        this.composition = sanitizeComposition(composition);
        if (totalStrength < 0) throw new IllegalArgumentException("totalStrength must be non-negative");
        int compositionTotal = this.composition.values().stream().mapToInt(Integer::intValue).sum();
        if (compositionTotal != totalStrength) {
            throw new IllegalArgumentException("composition total " + compositionTotal + " != totalStrength " + totalStrength);
        }
        this.totalStrength = totalStrength;
        this.state = Objects.requireNonNull(state, "state");
        this.lastSimulatedGameTime = Math.max(0L, lastSimulatedGameTime);
    }

    public static StrategicGroup testGroup(StrategicPosition start, StrategicPosition destination, long gameTime) {
        return new StrategicGroup(UUID.randomUUID(), "drewcraft:test", StrategicGroupType.TEST, null, start,
                StrategicRoute.between(start, destination), 2.5, Map.of("minecraft:zombie", 20), 20,
                StrategicGroupState.TRAVELING, Math.max(0L, gameTime));
    }

    public UUID groupId() { return groupId; }
    public String factionId() { return factionId; }
    public StrategicGroupType groupType() { return groupType; }
    public Optional<UUID> sourceId() { return Optional.ofNullable(sourceId); }
    public StrategicPosition position() { return position; }
    public StrategicPosition destination() { return route.destination(); }
    public StrategicRoute route() { return route; }
    public StrategicMission mission() { return mission; }
    public double movementSpeedBlocksPerSecond() { return movementSpeedBlocksPerSecond; }
    public Map<String, Integer> composition() { return Collections.unmodifiableMap(new LinkedHashMap<>(composition)); }
    public int totalStrength() { return totalStrength; }
    public StrategicGroupState state() { return state; }
    public long lastSimulatedGameTime() { return lastSimulatedGameTime; }

    public void assignRoute(StrategicRoute solvedRoute, long gameTime) {
        Objects.requireNonNull(solvedRoute, "solvedRoute");
        if (!position.dimension().equals(solvedRoute.destination().dimension())) {
            throw new IllegalArgumentException("new route dimension does not match group position");
        }
        route = solvedRoute;
        mission = StrategicMission.legacy(solvedRoute.destination(), gameTime);
        state = solvedRoute.arrived() ? StrategicGroupState.ARRIVED : StrategicGroupState.TRAVELING;
        lastSimulatedGameTime = Math.max(0L, gameTime);
    }

    /** Freeze strategic movement before any tactical entities are created. */
    public StrategicGroupState suspendForEncounter() {
        if (state == StrategicGroupState.DESTROYED) throw new IllegalStateException("destroyed group cannot materialize");
        if (state == StrategicGroupState.MATERIALIZED) throw new IllegalStateException("group is already materialized");
        StrategicGroupState resumeState = state;
        state = StrategicGroupState.MATERIALIZED;
        return resumeState;
    }

    /** Return a surviving encounter to its prior strategic state. */
    public void resumeAfterEncounter(StrategicGroupState resumeState) {
        Objects.requireNonNull(resumeState, "resumeState");
        if (totalStrength == 0) {
            state = StrategicGroupState.DESTROYED;
            return;
        }
        if (resumeState == StrategicGroupState.MATERIALIZED || resumeState == StrategicGroupState.DESTROYED) {
            throw new IllegalArgumentException("invalid encounter resume state: " + resumeState);
        }
        state = resumeState;
    }

    /** Apply one confirmed tactical death exactly once through encounter authority. */
    public boolean applyCasualty(String entityTypeId) {
        String id = requireNonBlank(entityTypeId, "entityTypeId");
        Integer count = composition.get(id);
        if (count == null || count <= 0 || totalStrength <= 0) return false;
        if (count == 1) composition.remove(id); else composition.put(id, count - 1);
        totalStrength--;
        if (totalStrength == 0) state = StrategicGroupState.DESTROYED;
        return true;
    }

    public double etaSeconds() {
        if (state != StrategicGroupState.TRAVELING) return 0.0;
        return route.remainingCostFrom(position) / movementSpeedBlocksPerSecond;
    }

    public AdvanceResult advanceToGameTime(long currentGameTime, double maxCatchupSeconds) {
        if (!Double.isFinite(maxCatchupSeconds) || maxCatchupSeconds < 0.0) {
            throw new IllegalArgumentException("maxCatchupSeconds must be finite and non-negative");
        }
        if (state != StrategicGroupState.TRAVELING || currentGameTime <= lastSimulatedGameTime) return AdvanceResult.none();
        double rawElapsedSeconds = (currentGameTime - lastSimulatedGameTime) / 20.0;
        double elapsedSeconds = Math.min(rawElapsedSeconds, maxCatchupSeconds);
        boolean clamped = rawElapsedSeconds > maxCatchupSeconds;
        lastSimulatedGameTime = currentGameTime;
        return advanceSecondsInternal(elapsedSeconds, clamped);
    }

    public AdvanceResult advanceBySeconds(double elapsedSeconds, double maxCatchupSeconds) {
        if (!Double.isFinite(elapsedSeconds) || elapsedSeconds < 0.0) {
            throw new IllegalArgumentException("elapsedSeconds must be finite and non-negative");
        }
        if (!Double.isFinite(maxCatchupSeconds) || maxCatchupSeconds < 0.0) {
            throw new IllegalArgumentException("maxCatchupSeconds must be finite and non-negative");
        }
        if (state != StrategicGroupState.TRAVELING) return AdvanceResult.none();
        boolean clamped = elapsedSeconds > maxCatchupSeconds;
        return advanceSecondsInternal(Math.min(elapsedSeconds, maxCatchupSeconds), clamped);
    }

    private AdvanceResult advanceSecondsInternal(double elapsedSeconds, boolean clamped) {
        if (elapsedSeconds <= 0.0) return AdvanceResult.none();
        StrategicRoute.AdvanceResult routeAdvance = route.advance(position, movementSpeedBlocksPerSecond * elapsedSeconds);
        position = routeAdvance.position();
        boolean arrivedNow = routeAdvance.arrived();
        if (arrivedNow) state = StrategicGroupState.ARRIVED;
        return new AdvanceResult(elapsedSeconds, routeAdvance.distanceMoved(), arrivedNow, clamped);
    }

    private static LinkedHashMap<String, Integer> sanitizeComposition(Map<String, Integer> input) {
        Objects.requireNonNull(input, "composition");
        LinkedHashMap<String, Integer> copy = new LinkedHashMap<>();
        input.entrySet().stream().sorted(Map.Entry.comparingByKey()).forEach(entry -> {
            String id = requireNonBlank(entry.getKey(), "composition id");
            Integer count = entry.getValue();
            if (count == null || count < 0) throw new IllegalArgumentException("composition counts must be non-negative");
            if (count > 0) copy.put(id, count);
        });
        return copy;
    }

    private static String requireNonBlank(String value, String name) {
        Objects.requireNonNull(value, name);
        if (value.isBlank()) throw new IllegalArgumentException(name + " must not be blank");
        return value;
    }

    public record AdvanceResult(double elapsedSeconds, double distanceMoved, boolean arrived, boolean catchupClamped) {
        public static AdvanceResult none() { return new AdvanceResult(0.0, 0.0, false, false); }
        public boolean changedPosition() { return distanceMoved > 0.0; }
    }
}
