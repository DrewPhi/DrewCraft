package dev.drewcraft.persistence;

import dev.drewcraft.strategic.encounter.StrategicEncounter;
import dev.drewcraft.strategic.encounter.StrategicEncounterState;
import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.persistence.StrategicEncounterNbt;
import dev.drewcraft.strategic.persistence.StrategicGroupNbt;
import dev.drewcraft.strategic.source.SourceCorePosition;
import dev.drewcraft.strategic.source.SourceDescriptor;
import dev.drewcraft.strategic.source.SourceRecord;
import dev.drewcraft.strategic.source.SourceRecordNbt;
import dev.drewcraft.strategic.source.SourceState;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.saveddata.SavedData;

public final class DrewCraftSavedData extends SavedData {
    public static final int CURRENT_SCHEMA_VERSION = 4;
    private static final String DATA_NAME = "drewcraft_world_state";
    private static final String TAG_SCHEMA_VERSION = "SchemaVersion";
    private static final String TAG_LAST_TOUCHED_GAME_TIME = "LastTouchedGameTime";
    private static final String TAG_STRATEGIC_GROUPS = "StrategicGroups";
    private static final String TAG_STRATEGIC_ENCOUNTERS = "StrategicEncounters";
    private static final String TAG_STRATEGIC_SOURCES = "StrategicSources";

    private long lastTouchedGameTime;
    private final Map<UUID, StrategicGroup> strategicGroups;
    private final Map<UUID, StrategicEncounter> strategicEncounters;
    private final Map<UUID, SourceRecord> strategicSources;

    private DrewCraftSavedData() {
        this(0L, new LinkedHashMap<>(), new LinkedHashMap<>(), new LinkedHashMap<>());
    }

    private DrewCraftSavedData(long lastTouchedGameTime, Map<UUID, StrategicGroup> strategicGroups,
                               Map<UUID, StrategicEncounter> strategicEncounters,
                               Map<UUID, SourceRecord> strategicSources) {
        this.lastTouchedGameTime = lastTouchedGameTime;
        this.strategicGroups = new LinkedHashMap<>(strategicGroups);
        this.strategicEncounters = new LinkedHashMap<>(strategicEncounters);
        this.strategicSources = new LinkedHashMap<>(strategicSources);
        validateEncounterIndex();
        validateSourceIndex();
    }

    public static Factory<DrewCraftSavedData> factory() {
        return new Factory<>(DrewCraftSavedData::new, DrewCraftSavedData::load);
    }

    public static DrewCraftSavedData get(MinecraftServer server) {
        return server.overworld().getDataStorage().computeIfAbsent(factory(), DATA_NAME);
    }

    static DrewCraftSavedData load(CompoundTag tag, HolderLookup.Provider registries) {
        int storedSchema = tag.contains(TAG_SCHEMA_VERSION) ? tag.getInt(TAG_SCHEMA_VERSION) : 0;
        if (storedSchema > CURRENT_SCHEMA_VERSION) {
            throw new IllegalStateException(
                    "DrewCraft world state schema " + storedSchema
                            + " is newer than supported schema " + CURRENT_SCHEMA_VERSION
            );
        }

        long lastTouched = tag.getLong(TAG_LAST_TOUCHED_GAME_TIME);
        LinkedHashMap<UUID, StrategicGroup> groups = new LinkedHashMap<>();
        LinkedHashMap<UUID, StrategicEncounter> encounters = new LinkedHashMap<>();
        LinkedHashMap<UUID, SourceRecord> sources = new LinkedHashMap<>();

        // Schemas 0-1 predate strategic-group persistence and migrate as an empty group registry.
        if (storedSchema >= 2 && tag.contains(TAG_STRATEGIC_GROUPS, Tag.TAG_LIST)) {
            ListTag groupTags = tag.getList(TAG_STRATEGIC_GROUPS, Tag.TAG_COMPOUND);
            for (int i = 0; i < groupTags.size(); i++) {
                StrategicGroup group = StrategicGroupNbt.load(groupTags.getCompound(i));
                StrategicGroup previous = groups.put(group.groupId(), group);
                if (previous != null) {
                    throw new IllegalStateException("Duplicate StrategicGroup id in SavedData: " + group.groupId());
                }
            }
        }

        // Schema 3 introduces durable materialization encounters. Schema 2 migrates with none.
        if (storedSchema >= 3 && tag.contains(TAG_STRATEGIC_ENCOUNTERS, Tag.TAG_LIST)) {
            ListTag encounterTags = tag.getList(TAG_STRATEGIC_ENCOUNTERS, Tag.TAG_COMPOUND);
            for (int i = 0; i < encounterTags.size(); i++) {
                StrategicEncounter encounter = StrategicEncounterNbt.load(encounterTags.getCompound(i));
                StrategicEncounter previous = encounters.put(encounter.encounterId(), encounter);
                if (previous != null) {
                    throw new IllegalStateException("Duplicate StrategicEncounter id in SavedData: " + encounter.encounterId());
                }
            }
        }

        // Schema 4 introduces hostile strategic sources. Schema 3 migrates with none.
        if (storedSchema >= 4 && tag.contains(TAG_STRATEGIC_SOURCES, Tag.TAG_LIST)) {
            ListTag sourceTags = tag.getList(TAG_STRATEGIC_SOURCES, Tag.TAG_COMPOUND);
            for (int i = 0; i < sourceTags.size(); i++) {
                SourceRecord source = SourceRecordNbt.load(sourceTags.getCompound(i));
                SourceRecord previous = sources.put(source.sourceId(), source);
                if (previous != null) {
                    throw new IllegalStateException("Duplicate SourceRecord id in SavedData: " + source.sourceId());
                }
            }
        }
        return new DrewCraftSavedData(lastTouched, groups, encounters, sources);
    }

    @Override
    public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
        tag.putInt(TAG_SCHEMA_VERSION, CURRENT_SCHEMA_VERSION);
        tag.putLong(TAG_LAST_TOUCHED_GAME_TIME, lastTouchedGameTime);

        ListTag groups = new ListTag();
        strategicGroups.values().stream()
                .sorted(Comparator.comparing(group -> group.groupId().toString()))
                .map(StrategicGroupNbt::save)
                .forEach(groups::add);
        tag.put(TAG_STRATEGIC_GROUPS, groups);

        ListTag encounters = new ListTag();
        strategicEncounters.values().stream()
                .filter(encounter -> encounter.state() != StrategicEncounterState.COMPLETE)
                .sorted(Comparator.comparing(encounter -> encounter.encounterId().toString()))
                .map(StrategicEncounterNbt::save)
                .forEach(encounters::add);
        tag.put(TAG_STRATEGIC_ENCOUNTERS, encounters);

        ListTag sources = new ListTag();
        strategicSources.values().stream()
                .sorted(Comparator.comparing(source -> source.sourceId().toString()))
                .map(SourceRecordNbt::save)
                .forEach(sources::add);
        tag.put(TAG_STRATEGIC_SOURCES, sources);
        return tag;
    }

    public long lastTouchedGameTime() { return lastTouchedGameTime; }

    public void touch(long gameTime) {
        lastTouchedGameTime = gameTime;
        setDirty();
    }

    public synchronized List<StrategicGroup> strategicGroups() {
        ArrayList<StrategicGroup> groups = new ArrayList<>(strategicGroups.values());
        groups.sort(Comparator.comparing(group -> group.groupId().toString()));
        return List.copyOf(groups);
    }

    public synchronized Optional<StrategicGroup> strategicGroup(UUID groupId) {
        return Optional.ofNullable(strategicGroups.get(groupId));
    }

    public synchronized void upsertStrategicGroup(StrategicGroup group) {
        strategicGroups.put(group.groupId(), group);
        setDirty();
    }

    public synchronized boolean removeStrategicGroup(UUID groupId) {
        if (strategicEncounterForGroup(groupId).isPresent()) {
            throw new IllegalStateException("cannot remove group with active encounter: " + groupId);
        }
        if (strategicGroups.remove(groupId) != null) {
            setDirty();
            return true;
        }
        return false;
    }

    public synchronized List<SourceRecord> sourceRecords() {
        ArrayList<SourceRecord> sources = new ArrayList<>(strategicSources.values());
        sources.sort(Comparator.comparing(source -> source.sourceId().toString()));
        return List.copyOf(sources);
    }

    public synchronized Optional<SourceRecord> sourceRecord(UUID sourceId) {
        return Optional.ofNullable(strategicSources.get(sourceId));
    }

    public synchronized Optional<SourceRecord> sourceAtCore(SourceCorePosition corePosition) {
        return strategicSources.values().stream()
                .filter(source -> source.corePosition().equals(corePosition))
                .findFirst();
    }

    /** Idempotent generated-structure discovery. Rediscovery can never reactivate a cleared source. */
    public synchronized DiscoverSourceResult discoverSource(SourceDescriptor descriptor, long gameTime) {
        UUID sourceId = descriptor.stableSourceId();
        SourceRecord existing = strategicSources.get(sourceId);
        if (existing != null) {
            if (!existing.identityMatches(descriptor)) {
                throw new IllegalStateException("stable source id resolved to conflicting generated geography: " + sourceId);
            }
            return new DiscoverSourceResult(existing, false);
        }

        SourceRecord source = SourceRecord.discovered(descriptor, gameTime);
        Optional<SourceRecord> occupiedCore = sourceAtCore(descriptor.corePosition());
        if (occupiedCore.isPresent()) {
            throw new IllegalStateException("source core position already bound to " + occupiedCore.get().sourceId());
        }
        strategicSources.put(source.sourceId(), source);
        setDirty();
        return new DiscoverSourceResult(source, true);
    }

    /** Authoritative, idempotent source-clear transaction. Existing strategic groups are untouched. */
    public synchronized boolean clearSource(UUID sourceId, long gameTime, String cause, String actor) {
        SourceRecord source = requireSource(sourceId);
        boolean changed = source.clear(gameTime, cause, actor);
        if (changed) setDirty();
        return changed;
    }

    /**
     * Atomic launch commit. Route planning may occur outside the lock, but a group cannot commit if
     * the source was cleared or otherwise changed after the planner captured expectedGeneration.
     */
    public synchronized boolean commitSourceLaunch(UUID sourceId, long expectedGeneration,
                                                   StrategicGroup group, long gameTime) {
        SourceRecord source = requireSource(sourceId);
        UUID groupSource = group.sourceId().orElseThrow(() -> new IllegalArgumentException("source launch group is missing sourceId"));
        if (!sourceId.equals(groupSource)) throw new IllegalArgumentException("group/source id mismatch");
        if (strategicGroups.containsKey(group.groupId())) throw new IllegalStateException("duplicate strategic group id: " + group.groupId());
        if (!source.commitLaunch(expectedGeneration, gameTime)) return false;
        strategicGroups.put(group.groupId(), group);
        setDirty();
        return true;
    }

    public synchronized void postponeSourceLaunch(UUID sourceId, long expectedGeneration,
                                                  long gameTime, long delayTicks) {
        SourceRecord source = requireSource(sourceId);
        if (source.generation() != expectedGeneration || source.state() == SourceState.CLEARED) return;
        source.postpone(gameTime, delayTicks);
        setDirty();
    }

    public synchronized List<StrategicEncounter> strategicEncounters() {
        ArrayList<StrategicEncounter> encounters = new ArrayList<>(strategicEncounters.values());
        encounters.sort(Comparator.comparing(encounter -> encounter.encounterId().toString()));
        return List.copyOf(encounters);
    }

    public synchronized Optional<StrategicEncounter> strategicEncounter(UUID encounterId) {
        return Optional.ofNullable(strategicEncounters.get(encounterId));
    }

    public synchronized Optional<StrategicEncounter> strategicEncounterForGroup(UUID groupId) {
        return strategicEncounters.values().stream()
                .filter(encounter -> encounter.state() != StrategicEncounterState.COMPLETE)
                .filter(encounter -> encounter.groupId().equals(groupId))
                .findFirst();
    }

    /**
     * Atomic reservation boundary. The group is frozen before any entity is spawned, and repeated
     * calls for the same group return the existing encounter instead of creating a duplicate.
     */
    public synchronized BeginEncounterResult beginStrategicEncounter(UUID groupId, long gameTime) {
        StrategicEncounter existing = strategicEncounterForGroup(groupId).orElse(null);
        if (existing != null) return new BeginEncounterResult(existing, false);

        StrategicGroup group = strategicGroups.get(groupId);
        if (group == null) throw new IllegalArgumentException("unknown strategic group: " + groupId);
        if (group.totalStrength() <= 0 || group.state() == StrategicGroupState.DESTROYED) {
            throw new IllegalStateException("destroyed/empty group cannot materialize: " + groupId);
        }
        StrategicGroupState resumeState = group.suspendForEncounter();
        StrategicEncounter encounter = StrategicEncounter.preparing(groupId, resumeState, gameTime);
        strategicEncounters.put(encounter.encounterId(), encounter);
        setDirty();
        return new BeginEncounterResult(encounter, true);
    }

    public synchronized void registerEncounterEntity(UUID encounterId, UUID entityId, String entityTypeId) {
        requireEncounter(encounterId).registerSpawn(entityId, entityTypeId);
        setDirty();
    }

    public synchronized void markEncounterMaterialized(UUID encounterId) {
        requireEncounter(encounterId).markMaterialized();
        setDirty();
    }

    /** Apply a tagged entity death once; duplicate death callbacks are harmless. */
    public synchronized boolean recordStrategicCasualty(UUID encounterId, UUID entityId) {
        StrategicEncounter encounter = requireEncounter(encounterId);
        Optional<String> type = encounter.recordDeath(entityId);
        if (type.isEmpty()) return false;
        StrategicGroup group = requireGroup(encounter.groupId());
        if (!group.applyCasualty(type.get())) {
            throw new IllegalStateException(
                    "encounter casualty does not match strategic composition: " + encounterId + " / " + type.get()
            );
        }
        setDirty();
        return true;
    }

    public synchronized void touchEncounterPlayerSeen(UUID encounterId, long gameTime) {
        requireEncounter(encounterId).touchPlayerSeen(gameTime);
        setDirty();
    }

    /**
     * Finish reconciliation. Tactical survivors are not casualties, so the already-decremented
     * strategic strength becomes the resumed group's authoritative population.
     */
    public synchronized void completeStrategicEncounter(UUID encounterId) {
        StrategicEncounter encounter = requireEncounter(encounterId);
        encounter.beginReconciliation();
        StrategicGroup group = requireGroup(encounter.groupId());
        group.resumeAfterEncounter(encounter.resumeState());
        encounter.markComplete();
        strategicEncounters.remove(encounterId);
        setDirty();
    }

    /** Crash recovery for PREPARING/RECONCILING transactions. */
    public synchronized boolean recoverInterruptedStrategicEncounter(UUID encounterId) {
        StrategicEncounter encounter = requireEncounter(encounterId);
        if (encounter.state() != StrategicEncounterState.PREPARING
                && encounter.state() != StrategicEncounterState.RECONCILING) {
            return false;
        }
        completeStrategicEncounter(encounterId);
        return true;
    }

    public synchronized void markStrategicDirty() { setDirty(); }

    private StrategicEncounter requireEncounter(UUID encounterId) {
        StrategicEncounter encounter = strategicEncounters.get(encounterId);
        if (encounter == null) throw new IllegalArgumentException("unknown strategic encounter: " + encounterId);
        return encounter;
    }

    private StrategicGroup requireGroup(UUID groupId) {
        StrategicGroup group = strategicGroups.get(groupId);
        if (group == null) throw new IllegalStateException("encounter references missing strategic group: " + groupId);
        return group;
    }

    private SourceRecord requireSource(UUID sourceId) {
        SourceRecord source = strategicSources.get(sourceId);
        if (source == null) throw new IllegalArgumentException("unknown strategic source: " + sourceId);
        return source;
    }

    private void validateEncounterIndex() {
        LinkedHashMap<UUID, UUID> groupToEncounter = new LinkedHashMap<>();
        for (StrategicEncounter encounter : strategicEncounters.values()) {
            if (encounter.state() == StrategicEncounterState.COMPLETE) continue;
            StrategicGroup group = strategicGroups.get(encounter.groupId());
            if (group == null) throw new IllegalStateException("encounter references missing group: " + encounter.groupId());
            if (group.state() != StrategicGroupState.MATERIALIZED) throw new IllegalStateException("active encounter references non-materialized group: " + group.groupId());
            if (encounter.activeEntityCount() > group.totalStrength()) throw new IllegalStateException("encounter active count exceeds strategic strength: " + group.groupId());
            for (Map.Entry<String, Integer> entry : group.composition().entrySet()) {
                if (encounter.activeCountForType(entry.getKey()) > entry.getValue()) {
                    throw new IllegalStateException("encounter active type count exceeds strategic composition: " + entry.getKey());
                }
            }
            UUID previous = groupToEncounter.put(encounter.groupId(), encounter.encounterId());
            if (previous != null) throw new IllegalStateException("multiple active encounters for group " + encounter.groupId());
        }

        Set<UUID> encounteredGroups = new LinkedHashSet<>(groupToEncounter.keySet());
        for (StrategicGroup group : strategicGroups.values()) {
            if (group.state() == StrategicGroupState.MATERIALIZED && !encounteredGroups.contains(group.groupId())) {
                throw new IllegalStateException("materialized group is missing its durable encounter: " + group.groupId());
            }
        }
    }

    private void validateSourceIndex() {
        Set<SourceCorePosition> boundCores = new LinkedHashSet<>();
        for (SourceRecord source : strategicSources.values()) {
            if (!boundCores.add(source.corePosition())) {
                throw new IllegalStateException("multiple sources share core position: " + source.corePosition());
            }
        }
        for (StrategicGroup group : strategicGroups.values()) {
            group.sourceId().ifPresent(sourceId -> {
                if (!strategicSources.containsKey(sourceId)) {
                    throw new IllegalStateException("strategic group references missing source: " + sourceId);
                }
            });
        }
    }

    public record BeginEncounterResult(StrategicEncounter encounter, boolean created) {
    }

    public record DiscoverSourceResult(SourceRecord source, boolean created) {
    }
}
