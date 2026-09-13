package dev.drewcraft.persistence;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.strategic.encounter.StrategicEncounter;
import dev.drewcraft.strategic.encounter.StrategicEncounterPlanner;
import dev.drewcraft.strategic.herd.WildHerdDescriptor;
import dev.drewcraft.strategic.herd.WildHerdRegistration;
import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.model.StrategicRoute;
import dev.drewcraft.strategic.model.StrategicTargetKnowledge;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import net.minecraft.nbt.CompoundTag;
import org.junit.jupiter.api.Test;

class WildHerdBp7AcceptanceTest {
    @Test
    void herdMovesMaterializesTakesCasualtiesAndSurvivesRestartWithoutAbsorbingLiveAnimals() {
        DrewCraftSavedData data = emptyData();
        WildHerdDescriptor descriptor = new WildHerdDescriptor(
                "minecraft:overworld", "minecraft:cow",
                0, 0, 2048, 0,
                80, 1.25
        );

        WildHerdRegistration.RegistrationResult created = WildHerdRegistration.register(
                data, descriptor, 100L,
                (start, destination) -> Optional.of(StrategicRoute.between(start, destination))
        );
        assertTrue(created.success());
        assertTrue(created.created());
        StrategicGroup herd = created.group();
        assertEquals(StrategicGroupType.HERD, herd.groupType());
        assertEquals(WildHerdDescriptor.WILDLIFE_FACTION_ID, herd.factionId());
        assertTrue(herd.sourceId().isEmpty());
        assertEquals(StrategicTargetKnowledge.MIGRATION_ROUTE, herd.mission().targetKnowledge());
        assertTrue(herd.mission().knowledgeDetail().contains("no live animal was absorbed"));
        assertEquals(80, herd.totalStrength());
        assertEquals(80, herd.composition().get("minecraft:cow"));

        herd.advanceBySeconds(120.0, 300.0);
        double movedX = herd.position().x();
        assertTrue(movedX > descriptor.origin().x());

        // Idempotent re-registration must not reroute/reset a living herd. The planner must not run.
        WildHerdRegistration.RegistrationResult rediscovered = WildHerdRegistration.register(
                data, descriptor, 500L,
                (start, destination) -> { throw new AssertionError("existing herd must not be replanned"); }
        );
        assertFalse(rediscovered.created());
        assertSame(herd, rediscovered.group());
        assertEquals(movedX, rediscovered.group().position().x());

        DrewCraftSavedData.BeginEncounterResult begin = data.beginStrategicEncounter(herd.groupId(), 600L);
        StrategicEncounter encounter = begin.encounter();
        List<String> firstWave = StrategicEncounterPlanner.nextWave(herd, encounter, 64);
        assertEquals(64, firstWave.size());
        for (int i = 0; i < firstWave.size(); i++) {
            UUID entityId = UUID.nameUUIDFromBytes(("bp7-cow-" + i).getBytes(StandardCharsets.UTF_8));
            data.registerEncounterEntity(encounter.encounterId(), entityId, firstWave.get(i));
        }
        data.markEncounterMaterialized(encounter.encounterId());
        assertEquals(64, encounter.activeEntityCount());
        assertTrue(encounter.activeEntityCount() < herd.totalStrength());

        List<UUID> active = encounter.activeEntityIds();
        for (int i = 0; i < 10; i++) assertTrue(data.recordStrategicCasualty(encounter.encounterId(), active.get(i)));
        assertEquals(70, herd.totalStrength());
        assertEquals(54, encounter.activeEntityCount());
        assertEquals(16, StrategicEncounterPlanner.nextWave(herd, encounter, 64).size());

        DrewCraftSavedData restored = DrewCraftSavedData.load(data.save(new CompoundTag(), null), null);
        StrategicGroup restoredHerd = restored.strategicGroup(descriptor.stableHerdId()).orElseThrow();
        StrategicEncounter restoredEncounter = restored.strategicEncounterForGroup(restoredHerd.groupId()).orElseThrow();
        assertEquals(StrategicGroupType.HERD, restoredHerd.groupType());
        assertEquals(StrategicTargetKnowledge.MIGRATION_ROUTE, restoredHerd.mission().targetKnowledge());
        assertEquals(70, restoredHerd.totalStrength());
        assertEquals(54, restoredEncounter.activeEntityCount());
        assertEquals(16, StrategicEncounterPlanner.nextWave(restoredHerd, restoredEncounter, 64).size());

        restored.completeStrategicEncounter(restoredEncounter.encounterId());
        assertEquals(StrategicGroupState.TRAVELING, restoredHerd.state());
        assertEquals(70, restoredHerd.totalStrength());
    }

    private static DrewCraftSavedData emptyData() {
        CompoundTag tag = new CompoundTag();
        tag.putInt("SchemaVersion", DrewCraftSavedData.CURRENT_SCHEMA_VERSION);
        return DrewCraftSavedData.load(tag, null);
    }
}
