package dev.drewcraft.strategic.encounter;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.persistence.StrategicEncounterNbt;
import java.util.UUID;
import net.minecraft.nbt.CompoundTag;
import org.junit.jupiter.api.Test;

class StrategicEncounterTest {
    @Test
    void deathIsRecordedExactlyOnce() {
        UUID groupId = UUID.randomUUID();
        StrategicEncounter encounter = StrategicEncounter.preparing(groupId, StrategicGroupState.TRAVELING, 100L);
        UUID entityId = UUID.randomUUID();
        encounter.registerSpawn(entityId, "minecraft:zombie");
        encounter.markMaterialized();

        assertEquals("minecraft:zombie", encounter.recordDeath(entityId).orElseThrow());
        assertTrue(encounter.recordDeath(entityId).isEmpty());
        assertEquals(0, encounter.activeEntityCount());
        assertEquals(1, encounter.casualtyCount());
    }

    @Test
    void roundTripsActiveEntitiesAndCasualties() {
        StrategicEncounter encounter = StrategicEncounter.preparing(
                UUID.randomUUID(), StrategicGroupState.ARRIVED, 100L
        );
        UUID survivor = UUID.randomUUID();
        UUID casualty = UUID.randomUUID();
        encounter.registerSpawn(survivor, "minecraft:zombie");
        encounter.registerSpawn(casualty, "minecraft:skeleton");
        encounter.markMaterialized();
        encounter.recordDeath(casualty);
        encounter.touchPlayerSeen(500L);

        StrategicEncounter restored = StrategicEncounterNbt.load(StrategicEncounterNbt.save(encounter));
        assertEquals(encounter.encounterId(), restored.encounterId());
        assertEquals(encounter.groupId(), restored.groupId());
        assertEquals(StrategicEncounterState.MATERIALIZED, restored.state());
        assertTrue(restored.expectsEntity(survivor));
        assertFalse(restored.expectsEntity(casualty));
        assertTrue(restored.casualtyEntityIds().contains(casualty));
        assertEquals(500L, restored.lastPlayerSeenGameTime());
    }

    @Test
    void rejectsFutureEncounterSchema() {
        StrategicEncounter encounter = StrategicEncounter.preparing(
                UUID.randomUUID(), StrategicGroupState.TRAVELING, 0L
        );
        CompoundTag tag = StrategicEncounterNbt.save(encounter);
        tag.putInt("SchemaVersion", StrategicEncounter.CURRENT_SCHEMA_VERSION + 1);
        assertThrows(IllegalStateException.class, () -> StrategicEncounterNbt.load(tag));
    }
}
