package dev.drewcraft.strategic.encounter;

import dev.drewcraft.strategic.model.StrategicGroupState;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

/**
 * Durable authority for one materialized tactical encounter. Active entity UUIDs are persisted so
 * restart/reload cannot create a second copy of the same strategic units.
 */
public final class StrategicEncounter {
    public static final int CURRENT_SCHEMA_VERSION = 1;

    private final UUID encounterId;
    private final UUID groupId;
    private final StrategicGroupState resumeState;
    private final long startedGameTime;
    private long lastPlayerSeenGameTime;
    private StrategicEncounterState state;
    private final LinkedHashMap<UUID, String> activeEntityTypes;
    private final LinkedHashSet<UUID> casualtyEntityIds;

    public StrategicEncounter(UUID encounterId, UUID groupId, StrategicGroupState resumeState,
                              long startedGameTime, long lastPlayerSeenGameTime,
                              StrategicEncounterState state, Map<UUID, String> activeEntityTypes,
                              Set<UUID> casualtyEntityIds) {
        this.encounterId = Objects.requireNonNull(encounterId, "encounterId");
        this.groupId = Objects.requireNonNull(groupId, "groupId");
        this.resumeState = Objects.requireNonNull(resumeState, "resumeState");
        if (resumeState == StrategicGroupState.MATERIALIZED || resumeState == StrategicGroupState.DESTROYED) {
            throw new IllegalArgumentException("invalid resume state: " + resumeState);
        }
        this.startedGameTime = Math.max(0L, startedGameTime);
        this.lastPlayerSeenGameTime = Math.max(this.startedGameTime, lastPlayerSeenGameTime);
        this.state = Objects.requireNonNull(state, "state");
        this.activeEntityTypes = new LinkedHashMap<>();
        Objects.requireNonNull(activeEntityTypes, "activeEntityTypes").entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .forEach(entry -> this.activeEntityTypes.put(
                        Objects.requireNonNull(entry.getKey(), "entity uuid"),
                        requireTypeId(entry.getValue())
                ));
        this.casualtyEntityIds = new LinkedHashSet<>();
        Objects.requireNonNull(casualtyEntityIds, "casualtyEntityIds").stream()
                .sorted()
                .forEach(id -> this.casualtyEntityIds.add(Objects.requireNonNull(id, "casualty uuid")));
    }

    public static StrategicEncounter preparing(UUID groupId, StrategicGroupState resumeState, long gameTime) {
        return new StrategicEncounter(
                UUID.randomUUID(), groupId, resumeState, gameTime, gameTime,
                StrategicEncounterState.PREPARING, Map.of(), Set.of()
        );
    }

    public UUID encounterId() { return encounterId; }
    public UUID groupId() { return groupId; }
    public StrategicGroupState resumeState() { return resumeState; }
    public long startedGameTime() { return startedGameTime; }
    public long lastPlayerSeenGameTime() { return lastPlayerSeenGameTime; }
    public StrategicEncounterState state() { return state; }
    public int activeEntityCount() { return activeEntityTypes.size(); }
    public int casualtyCount() { return casualtyEntityIds.size(); }
    public Map<UUID, String> activeEntityTypes() { return Collections.unmodifiableMap(new LinkedHashMap<>(activeEntityTypes)); }
    public Set<UUID> casualtyEntityIds() { return Collections.unmodifiableSet(new LinkedHashSet<>(casualtyEntityIds)); }

    public void touchPlayerSeen(long gameTime) {
        lastPlayerSeenGameTime = Math.max(lastPlayerSeenGameTime, gameTime);
    }

    public void registerSpawn(UUID entityId, String entityTypeId) {
        Objects.requireNonNull(entityId, "entityId");
        if (state != StrategicEncounterState.PREPARING && state != StrategicEncounterState.MATERIALIZED) {
            throw new IllegalStateException("cannot register spawn while encounter is " + state);
        }
        if (casualtyEntityIds.contains(entityId)) {
            throw new IllegalStateException("casualty UUID cannot be reused as active entity: " + entityId);
        }
        String previous = activeEntityTypes.putIfAbsent(entityId, requireTypeId(entityTypeId));
        if (previous != null && !previous.equals(entityTypeId)) {
            throw new IllegalStateException("entity UUID already registered with another type: " + entityId);
        }
    }

    public void markMaterialized() {
        if (state != StrategicEncounterState.PREPARING) {
            throw new IllegalStateException("encounter is not preparing: " + state);
        }
        state = StrategicEncounterState.MATERIALIZED;
    }

    public void beginReconciliation() {
        if (state == StrategicEncounterState.COMPLETE) return;
        state = StrategicEncounterState.RECONCILING;
    }

    public void markComplete() {
        state = StrategicEncounterState.COMPLETE;
        activeEntityTypes.clear();
    }

    /**
     * Record a death exactly once. The returned type is the authoritative strategic composition
     * member that must be decremented. Duplicate death events return empty.
     */
    public Optional<String> recordDeath(UUID entityId) {
        Objects.requireNonNull(entityId, "entityId");
        if (casualtyEntityIds.contains(entityId)) return Optional.empty();
        String type = activeEntityTypes.remove(entityId);
        if (type == null) return Optional.empty();
        casualtyEntityIds.add(entityId);
        return Optional.of(type);
    }

    /** Keep the strategic unit alive while forgetting a no-longer-loaded tactical object. */
    public Optional<String> detachSurvivor(UUID entityId) {
        return Optional.ofNullable(activeEntityTypes.remove(Objects.requireNonNull(entityId, "entityId")));
    }

    public boolean expectsEntity(UUID entityId) {
        return activeEntityTypes.containsKey(entityId);
    }

    public int activeCountForType(String entityTypeId) {
        String id = requireTypeId(entityTypeId);
        int count = 0;
        for (String type : activeEntityTypes.values()) if (type.equals(id)) count++;
        return count;
    }

    public List<UUID> activeEntityIds() {
        return List.copyOf(new ArrayList<>(activeEntityTypes.keySet()));
    }

    private static String requireTypeId(String value) {
        Objects.requireNonNull(value, "entityTypeId");
        if (value.isBlank()) throw new IllegalArgumentException("entityTypeId must not be blank");
        return value;
    }
}
