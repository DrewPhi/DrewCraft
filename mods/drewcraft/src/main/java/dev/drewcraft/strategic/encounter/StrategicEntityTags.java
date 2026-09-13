package dev.drewcraft.strategic.encounter;

import java.util.Optional;
import java.util.UUID;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.Entity;

/** Durable entity tags used to reconcile tactical mobs back to strategic authority. */
public final class StrategicEntityTags {
    private static final String TAG_GROUP = "drewcraftStrategicGroup";
    private static final String TAG_ENCOUNTER = "drewcraftStrategicEncounter";
    private static final String TAG_TYPE = "drewcraftStrategicEntityType";

    private StrategicEntityTags() {
    }

    public static void tag(Entity entity, UUID groupId, UUID encounterId, String entityTypeId) {
        CompoundTag data = entity.getPersistentData();
        data.putUUID(TAG_GROUP, groupId);
        data.putUUID(TAG_ENCOUNTER, encounterId);
        data.putString(TAG_TYPE, entityTypeId);
    }

    public static Optional<TaggedEntity> read(Entity entity) {
        CompoundTag data = entity.getPersistentData();
        if (!data.hasUUID(TAG_GROUP) || !data.hasUUID(TAG_ENCOUNTER) || !data.contains(TAG_TYPE)) {
            return Optional.empty();
        }
        String type = data.getString(TAG_TYPE);
        if (type.isBlank()) return Optional.empty();
        return Optional.of(new TaggedEntity(data.getUUID(TAG_GROUP), data.getUUID(TAG_ENCOUNTER), type));
    }

    public record TaggedEntity(UUID groupId, UUID encounterId, String entityTypeId) {
    }
}
