package dev.drewcraft.persistence;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicPosition;
import net.minecraft.nbt.CompoundTag;
import org.junit.jupiter.api.Test;

class DrewCraftSavedDataTest {
    @Test
    void migratesSchemaOneAsEmptyStrategicRegistry() {
        CompoundTag old = new CompoundTag();
        old.putInt("SchemaVersion", 1);
        old.putLong("LastTouchedGameTime", 1234L);

        DrewCraftSavedData migrated = DrewCraftSavedData.load(old, null);
        assertEquals(1234L, migrated.lastTouchedGameTime());
        assertTrue(migrated.strategicGroups().isEmpty());
    }

    @Test
    void strategicGroupsRoundTripThroughWorldState() {
        CompoundTag emptyV2 = new CompoundTag();
        emptyV2.putInt("SchemaVersion", DrewCraftSavedData.CURRENT_SCHEMA_VERSION);
        DrewCraftSavedData data = DrewCraftSavedData.load(emptyV2, null);

        StrategicGroup group = StrategicGroup.testGroup(
                new StrategicPosition("minecraft:overworld", 0.0, 0.0),
                new StrategicPosition("minecraft:overworld", 1000.0, 0.0),
                200L
        );
        group.advanceBySeconds(20.0, 20.0);
        data.upsertStrategicGroup(group);

        CompoundTag saved = data.save(new CompoundTag(), null);
        DrewCraftSavedData restored = DrewCraftSavedData.load(saved, null);

        assertEquals(1, restored.strategicGroups().size());
        StrategicGroup restoredGroup = restored.strategicGroup(group.groupId()).orElseThrow();
        assertEquals(group.position(), restoredGroup.position());
        assertEquals(group.route().cursor(), restoredGroup.route().cursor());
        assertEquals(group.totalStrength(), restoredGroup.totalStrength());
    }

    @Test
    void rejectsFutureWorldStateSchema() {
        CompoundTag future = new CompoundTag();
        future.putInt("SchemaVersion", DrewCraftSavedData.CURRENT_SCHEMA_VERSION + 1);
        assertThrows(IllegalStateException.class, () -> DrewCraftSavedData.load(future, null));
    }
}
