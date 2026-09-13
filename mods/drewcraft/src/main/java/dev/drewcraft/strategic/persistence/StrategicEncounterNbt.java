package dev.drewcraft.strategic.persistence;

import dev.drewcraft.strategic.encounter.StrategicEncounter;
import dev.drewcraft.strategic.encounter.StrategicEncounterState;
import dev.drewcraft.strategic.model.StrategicGroupState;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;

/** Deterministic codec for durable tactical encounter state. */
public final class StrategicEncounterNbt {
    private static final String TAG_SCHEMA = "SchemaVersion";

    private StrategicEncounterNbt() {
    }

    public static CompoundTag save(StrategicEncounter encounter) {
        CompoundTag tag = new CompoundTag();
        tag.putInt(TAG_SCHEMA, StrategicEncounter.CURRENT_SCHEMA_VERSION);
        tag.putUUID("EncounterId", encounter.encounterId());
        tag.putUUID("GroupId", encounter.groupId());
        tag.putString("ResumeState", encounter.resumeState().name());
        tag.putLong("StartedGameTime", encounter.startedGameTime());
        tag.putLong("LastPlayerSeenGameTime", encounter.lastPlayerSeenGameTime());
        tag.putString("State", encounter.state().name());

        ListTag active = new ListTag();
        encounter.activeEntityTypes().entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .forEach(entry -> {
                    CompoundTag item = new CompoundTag();
                    item.putUUID("EntityId", entry.getKey());
                    item.putString("EntityType", entry.getValue());
                    active.add(item);
                });
        tag.put("ActiveEntities", active);

        ListTag casualties = new ListTag();
        encounter.casualtyEntityIds().stream().sorted().forEach(id -> {
            CompoundTag item = new CompoundTag();
            item.putUUID("EntityId", id);
            casualties.add(item);
        });
        tag.put("Casualties", casualties);
        return tag;
    }

    public static StrategicEncounter load(CompoundTag tag) {
        int schema = tag.contains(TAG_SCHEMA, Tag.TAG_INT) ? tag.getInt(TAG_SCHEMA) : 0;
        if (schema <= 0) throw new IllegalStateException("StrategicEncounter is missing a supported schema version");
        if (schema > StrategicEncounter.CURRENT_SCHEMA_VERSION) {
            throw new IllegalStateException(
                    "StrategicEncounter schema " + schema + " is newer than supported schema "
                            + StrategicEncounter.CURRENT_SCHEMA_VERSION
            );
        }

        LinkedHashMap<UUID, String> active = new LinkedHashMap<>();
        ListTag activeTags = tag.getList("ActiveEntities", Tag.TAG_COMPOUND);
        for (int i = 0; i < activeTags.size(); i++) {
            CompoundTag item = activeTags.getCompound(i);
            UUID id = item.getUUID("EntityId");
            String previous = active.put(id, item.getString("EntityType"));
            if (previous != null) throw new IllegalStateException("Duplicate active entity UUID in encounter: " + id);
        }

        Set<UUID> casualties = new LinkedHashSet<>();
        ListTag casualtyTags = tag.getList("Casualties", Tag.TAG_COMPOUND);
        for (int i = 0; i < casualtyTags.size(); i++) {
            UUID id = casualtyTags.getCompound(i).getUUID("EntityId");
            if (!casualties.add(id)) throw new IllegalStateException("Duplicate casualty UUID in encounter: " + id);
        }

        return new StrategicEncounter(
                tag.getUUID("EncounterId"),
                tag.getUUID("GroupId"),
                StrategicGroupState.valueOf(tag.getString("ResumeState")),
                tag.getLong("StartedGameTime"),
                tag.getLong("LastPlayerSeenGameTime"),
                StrategicEncounterState.valueOf(tag.getString("State")),
                active,
                casualties
        );
    }
}
