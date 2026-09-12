package dev.drewcraft.persistence;

import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.saveddata.SavedData;

public final class DrewCraftSavedData extends SavedData {
    public static final int CURRENT_SCHEMA_VERSION = 1;
    private static final String DATA_NAME = "drewcraft_world_state";
    private static final String TAG_SCHEMA_VERSION = "SchemaVersion";
    private static final String TAG_LAST_TOUCHED_GAME_TIME = "LastTouchedGameTime";

    private long lastTouchedGameTime;

    private DrewCraftSavedData() {
        this.lastTouchedGameTime = 0L;
    }

    private DrewCraftSavedData(long lastTouchedGameTime) {
        this.lastTouchedGameTime = lastTouchedGameTime;
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

        // Schema 0 is the pre-versioned/empty state. Schema migrations will be added here as needed.
        return new DrewCraftSavedData(tag.getLong(TAG_LAST_TOUCHED_GAME_TIME));
    }

    @Override
    public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
        tag.putInt(TAG_SCHEMA_VERSION, CURRENT_SCHEMA_VERSION);
        tag.putLong(TAG_LAST_TOUCHED_GAME_TIME, lastTouchedGameTime);
        return tag;
    }

    public long lastTouchedGameTime() {
        return lastTouchedGameTime;
    }

    public void touch(long gameTime) {
        lastTouchedGameTime = gameTime;
        setDirty();
    }
}
