package dev.drewcraft.persistence;

import dev.drewcraft.strategic.encounter.StrategicEncounter;
import dev.drewcraft.strategic.encounter.StrategicEncounterState;
import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.persistence.StrategicEncounterNbt;
import dev.drewcraft.strategic.persistence.StrategicGroupNbt;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.saveddata.SavedData;

public final class DrewCraftSavedData extends SavedData {
    public static final int CURRENT_SCHEMA_VERSION = 3;
    private static final String DATA_NAME = "drewcraft_world_state";
    private static final String TAG_SCHEMA_VERSION = "SchemaVersion";
    private static final String TAG_LAST_TOUCHED_GAME_TIME = "LastTouchedGameTime";
    private static final String TAG_STRATEGIC_GROUPS = "StrategicGroups";
    private static final String TAG_STRATEGIC_ENCOUNTERS = "StrategicEncounters";

    private long lastTouchedGameTime;
    private final Map<UUID, StrategicGroup> strategicGroups;
    private final Map<UUID, StrategicEncounter> strategicEncounters;

    private DrewCraftSavedData() {
        this(0L, new LinkedHashMap<>(), new LinkedHashMap<>());
    }

    private DrewCraftSavedData(long lastTouchedGameTime, Map<UUID, StrategicGroup> strategicGroups,
                               Map<UUID, StrategicEncounter> strategicEncounters) {
        this.lastTouchedGameTime = lastTouchedGameTime;
        this.strategicGroups = new LinkedHashMap<>(strategicGroups);
        this.strategicEncounters = new LinkedHashMap<>(strategicEncounters);
        validateEncounterIndex();
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
        return new DrewCraftSavedData(lastTouched, groups, encounters);
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

    private void validateEncounterIndex() {
        LinkedHashMap<UUID, UUID> groupToEncounter = new LinkedHashMap<>();
        for (StrategicEncounter encounter : strategicEncounters.values()) {
            if (encounter.state() == StrategicEncounterState.COMPLETE) continue;
            if (!strategicGroups.containsKey(encounter.groupId())) {
                throw new IllegalStateException("encounter references missing group: " + encounter.groupId());
            }
            UUID previous = groupToEncounter.put(encounter.groupId(), encounter.encounterId());
            if (previous != null) {
                throw new IllegalStateException("multiple active encounters for group " + encounter.groupId());
            }
        }
    }

    public record BeginEncounterResult(StrategicEncounter encounter, boolean created) {
    }
}
