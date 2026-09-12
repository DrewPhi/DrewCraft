package dev.drewcraft.persistence;

import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.persistence.StrategicGroupNbt;
import java.util.ArrayList;
import java.util.Collection;
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
    public static final int CURRENT_SCHEMA_VERSION = 2;
    private static final String DATA_NAME = "drewcraft_world_state";
    private static final String TAG_SCHEMA_VERSION = "SchemaVersion";
    private static final String TAG_LAST_TOUCHED_GAME_TIME = "LastTouchedGameTime";
    private static final String TAG_STRATEGIC_GROUPS = "StrategicGroups";

    private long lastTouchedGameTime;
    private final Map<UUID, StrategicGroup> strategicGroups;

    private DrewCraftSavedData() {
        this(0L, new LinkedHashMap<>());
    }

    private DrewCraftSavedData(long lastTouchedGameTime, Map<UUID, StrategicGroup> strategicGroups) {
        this.lastTouchedGameTime = lastTouchedGameTime;
        this.strategicGroups = new LinkedHashMap<>(strategicGroups);
    }

    public static Factory<DrewCraftSavedData> factory() {
        return new Factory<>(DrewCraftSavedData::new, DrewCraftSavedData::load);
    }

    public static DrewCraftSavedData get(MinecraftServer server) {
        return server.overworld().getDataStorage().computeIfAbsent(factory(), DATA_NAME);
    }

    private static DrewCraftSavedData load(CompoundTag tag, HolderLookup.Provider registries) {
        int storedSchema = tag.contains(TAG_SCHEMA_VERSION) ? tag.getInt(TAG_SCHEMA_VERSION) : 0;
        if (storedSchema > CURRENT_SCHEMA_VERSION) {
            throw new IllegalStateException(
                    "DrewCraft world state schema " + storedSchema
                            + " is newer than supported schema " + CURRENT_SCHEMA_VERSION
            );
        }

        long lastTouched = tag.getLong(TAG_LAST_TOUCHED_GAME_TIME);
        LinkedHashMap<UUID, StrategicGroup> groups = new LinkedHashMap<>();

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
        return new DrewCraftSavedData(lastTouched, groups);
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
        return tag;
    }

    public long lastTouchedGameTime() {
        return lastTouchedGameTime;
    }

    public void touch(long gameTime) {
        lastTouchedGameTime = gameTime;
        setDirty();
    }

    public List<StrategicGroup> strategicGroups() {
        ArrayList<StrategicGroup> groups = new ArrayList<>(strategicGroups.values());
        groups.sort(Comparator.comparing(group -> group.groupId().toString()));
        return List.copyOf(groups);
    }

    public Optional<StrategicGroup> strategicGroup(UUID groupId) {
        return Optional.ofNullable(strategicGroups.get(groupId));
    }

    public void upsertStrategicGroup(StrategicGroup group) {
        strategicGroups.put(group.groupId(), group);
        setDirty();
    }

    public boolean removeStrategicGroup(UUID groupId) {
        if (strategicGroups.remove(groupId) != null) {
            setDirty();
            return true;
        }
        return false;
    }

    public void markStrategicDirty() {
        setDirty();
    }
}
