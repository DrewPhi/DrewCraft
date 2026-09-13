package dev.drewcraft.persistence;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.strategic.encounter.StrategicEncounter;
import dev.drewcraft.strategic.encounter.StrategicEncounterState;
import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicRoute;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.minecraft.nbt.CompoundTag;
import org.junit.jupiter.api.Test;

class DrewCraftEncounterTransactionTest {
    @Test
    void canonicalHundredFightSixtyThreeUnloadRestartRemainsSixtyThree() {
        DrewCraftSavedData data = emptyData();
        StrategicGroup group = hundredZombieGroup();
        data.upsertStrategicGroup(group);

        DrewCraftSavedData.BeginEncounterResult first = data.beginStrategicEncounter(group.groupId(), 100L);
        DrewCraftSavedData.BeginEncounterResult second = data.beginStrategicEncounter(group.groupId(), 100L);
        assertTrue(first.created());
        assertFalse(second.created());
        assertEquals(first.encounter().encounterId(), second.encounter().encounterId());
        assertEquals(StrategicGroupState.MATERIALIZED, group.state());

        StrategicEncounter encounter = first.encounter();
        List<UUID> entityIds = new ArrayList<>();
        for (int i = 0; i < 64; i++) {
            UUID entityId = UUID.randomUUID();
            entityIds.add(entityId);
            data.registerEncounterEntity(encounter.encounterId(), entityId, "minecraft:zombie");
        }
        data.markEncounterMaterialized(encounter.encounterId());
        assertEquals(64, encounter.activeEntityCount());

        for (int i = 0; i < 37; i++) {
            UUID entityId = entityIds.get(i);
            assertTrue(data.recordStrategicCasualty(encounter.encounterId(), entityId));
            assertFalse(data.recordStrategicCasualty(encounter.encounterId(), entityId));
        }
        assertEquals(63, group.totalStrength());
        assertEquals(63, group.composition().get("minecraft:zombie"));
        assertEquals(27, encounter.activeEntityCount());
        assertEquals(37, encounter.casualtyCount());

        // Player leaves: surviving tactical objects collapse back into the strategic record.
        data.completeStrategicEncounter(encounter.encounterId());
        assertTrue(data.strategicEncounters().isEmpty());
        assertEquals(StrategicGroupState.TRAVELING, group.state());
        assertEquals(63, group.totalStrength());

        // Server restart after unload must not resurrect the 37 casualties.
        DrewCraftSavedData restored = DrewCraftSavedData.load(data.save(new CompoundTag(), null), null);
        StrategicGroup restoredGroup = restored.strategicGroup(group.groupId()).orElseThrow();
        assertEquals(63, restoredGroup.totalStrength());
        assertEquals(63, restoredGroup.composition().get("minecraft:zombie"));
        assertEquals(StrategicGroupState.TRAVELING, restoredGroup.state());
        assertTrue(restored.strategicEncounters().isEmpty());
    }

    @Test
    void materializedRestartRetainsSingleEncounterAndBlocksDuplicateApproach() {
        DrewCraftSavedData data = emptyData();
        StrategicGroup group = hundredZombieGroup();
        data.upsertStrategicGroup(group);
        StrategicEncounter encounter = data.beginStrategicEncounter(group.groupId(), 10L).encounter();
        UUID entityId = UUID.randomUUID();
        data.registerEncounterEntity(encounter.encounterId(), entityId, "minecraft:zombie");
        data.markEncounterMaterialized(encounter.encounterId());

        DrewCraftSavedData restored = DrewCraftSavedData.load(data.save(new CompoundTag(), null), null);
        StrategicEncounter restoredEncounter = restored.strategicEncounter(encounter.encounterId()).orElseThrow();
        assertEquals(StrategicEncounterState.MATERIALIZED, restoredEncounter.state());
        assertTrue(restoredEncounter.expectsEntity(entityId));
        assertEquals(StrategicGroupState.MATERIALIZED,
                restored.strategicGroup(group.groupId()).orElseThrow().state());

        DrewCraftSavedData.BeginEncounterResult duplicate = restored.beginStrategicEncounter(group.groupId(), 20L);
        assertFalse(duplicate.created());
        assertEquals(encounter.encounterId(), duplicate.encounter().encounterId());
        assertEquals(1, restored.strategicEncounters().size());
    }

    @Test
    void interruptedPreparingTransactionRollsBackAfterRestart() {
        DrewCraftSavedData data = emptyData();
        StrategicGroup group = hundredZombieGroup();
        data.upsertStrategicGroup(group);
        StrategicEncounter encounter = data.beginStrategicEncounter(group.groupId(), 10L).encounter();
        UUID partialSpawn = UUID.randomUUID();
        data.registerEncounterEntity(encounter.encounterId(), partialSpawn, "minecraft:zombie");

        DrewCraftSavedData restored = DrewCraftSavedData.load(data.save(new CompoundTag(), null), null);
        assertEquals(StrategicEncounterState.PREPARING,
                restored.strategicEncounter(encounter.encounterId()).orElseThrow().state());
        assertTrue(restored.recoverInterruptedStrategicEncounter(encounter.encounterId()));
        assertTrue(restored.strategicEncounters().isEmpty());
        StrategicGroup restoredGroup = restored.strategicGroup(group.groupId()).orElseThrow();
        assertEquals(100, restoredGroup.totalStrength());
        assertEquals(StrategicGroupState.TRAVELING, restoredGroup.state());
    }

    private static DrewCraftSavedData emptyData() {
        CompoundTag tag = new CompoundTag();
        tag.putInt("SchemaVersion", DrewCraftSavedData.CURRENT_SCHEMA_VERSION);
        return DrewCraftSavedData.load(tag, null);
    }

    private static StrategicGroup hundredZombieGroup() {
        StrategicPosition start = new StrategicPosition("minecraft:overworld", 0.0, 0.0);
        StrategicPosition destination = new StrategicPosition("minecraft:overworld", 1000.0, 0.0);
        return new StrategicGroup(
                UUID.randomUUID(),
                "drewcraft:test",
                StrategicGroupType.TEST,
                null,
                start,
                StrategicRoute.between(start, destination),
                2.5,
                Map.of("minecraft:zombie", 100),
                100,
                StrategicGroupState.TRAVELING,
                0L
        );
    }
}
