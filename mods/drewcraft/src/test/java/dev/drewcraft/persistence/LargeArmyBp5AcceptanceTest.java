package dev.drewcraft.persistence;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.strategic.encounter.StrategicEncounter;
import dev.drewcraft.strategic.encounter.StrategicEncounterPlanner;
import dev.drewcraft.strategic.faction.StrategicFactionCatalog;
import dev.drewcraft.strategic.faction.StrategicForceTemplate;
import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.model.StrategicMission;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicRoute;
import dev.drewcraft.strategic.model.StrategicTargetKnowledge;
import dev.drewcraft.strategic.source.SourceClass;
import dev.drewcraft.strategic.source.SourceCorePosition;
import dev.drewcraft.strategic.source.SourceDescriptor;
import dev.drewcraft.strategic.source.SourceProductionScheduler;
import dev.drewcraft.strategic.source.SourceRecord;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.UUID;
import net.minecraft.nbt.CompoundTag;
import org.junit.jupiter.api.Test;

class LargeArmyBp5AcceptanceTest {
    @Test
    void largeArmyStaysMostlyAbstractAndKeepsMissionCasualtiesAcrossRestart() {
        DrewCraftSavedData data = emptyData();
        SourceDescriptor descriptor = new SourceDescriptor(
                "minecraft:overworld", "drewcraft:test_stronghold", 0, 64, 0,
                new SourceCorePosition("minecraft:overworld", 1, 65, 1),
                SourceClass.STRONGHOLD, "drewcraft:undead"
        );
        SourceRecord source = data.discoverSource(descriptor, 0L).source();
        StrategicForceTemplate armyTemplate = StrategicFactionCatalog.defaultCatalog()
                .byRole("drewcraft:undead", SourceClass.STRONGHOLD, StrategicGroupType.ARMY)
                .orElseThrow();
        int armyStrength = armyTemplate.desiredStrength(source.launchStrength());
        assertEquals(256, armyStrength);

        StrategicPosition start = new StrategicPosition(source.dimension(), 0.5, 0.5);
        StrategicPosition target = new StrategicPosition(source.dimension(), 4096.5, 0.5);
        StrategicMission mission = new StrategicMission(
                armyTemplate.id(),
                StrategicTargetKnowledge.SCOUTED_REGION,
                "acceptance-test scouted regional objective; no player lookup",
                target,
                source.nextActionGameTime()
        );
        UUID groupId = UUID.nameUUIDFromBytes("bp5-large-army".getBytes(StandardCharsets.UTF_8));
        StrategicGroup army = new StrategicGroup(
                groupId, source.factionId(), StrategicGroupType.ARMY, source.sourceId(),
                start, StrategicRoute.between(start, target), mission,
                source.movementSpeedBlocksPerSecond(), armyTemplate.compositionForStrength(armyStrength),
                armyStrength, StrategicGroupState.TRAVELING, source.nextActionGameTime()
        );

        long generation = source.generation();
        assertTrue(SourceProductionScheduler.commitPlannedLaunch(
                data, source.sourceId(), generation, army, source.nextActionGameTime()
        ));
        assertEquals(128, source.populationBudget());
        assertEquals(256, army.totalStrength());

        DrewCraftSavedData.BeginEncounterResult begin = data.beginStrategicEncounter(groupId, source.nextActionGameTime());
        StrategicEncounter encounter = begin.encounter();
        List<String> firstWave = StrategicEncounterPlanner.nextWave(army, encounter, 64);
        assertEquals(64, firstWave.size());

        UUID[] tacticalIds = new UUID[firstWave.size()];
        for (int i = 0; i < firstWave.size(); i++) {
            tacticalIds[i] = UUID.nameUUIDFromBytes(("bp5-tactical-" + i).getBytes(StandardCharsets.UTF_8));
            data.registerEncounterEntity(encounter.encounterId(), tacticalIds[i], firstWave.get(i));
        }
        data.markEncounterMaterialized(encounter.encounterId());
        assertEquals(64, encounter.activeEntityCount());
        assertTrue(encounter.activeEntityCount() < army.totalStrength());

        for (int i = 0; i < 37; i++) assertTrue(data.recordStrategicCasualty(encounter.encounterId(), tacticalIds[i]));
        assertEquals(219, army.totalStrength());
        assertEquals(27, encounter.activeEntityCount());
        assertEquals(37, StrategicEncounterPlanner.nextWave(army, encounter, 64).size());

        DrewCraftSavedData restored = DrewCraftSavedData.load(data.save(new CompoundTag(), null), null);
        StrategicGroup restoredArmy = restored.strategicGroup(groupId).orElseThrow();
        StrategicEncounter restoredEncounter = restored.strategicEncounterForGroup(groupId).orElseThrow();

        assertEquals(219, restoredArmy.totalStrength());
        assertEquals(StrategicGroupType.ARMY, restoredArmy.groupType());
        assertEquals(armyTemplate.id(), restoredArmy.mission().templateId());
        assertEquals(StrategicTargetKnowledge.SCOUTED_REGION, restoredArmy.mission().targetKnowledge());
        assertEquals(target, restoredArmy.mission().target());
        assertEquals(27, restoredEncounter.activeEntityCount());
        assertEquals(37, StrategicEncounterPlanner.nextWave(restoredArmy, restoredEncounter, 64).size());
        assertTrue(restoredEncounter.activeEntityCount() < restoredArmy.totalStrength());
    }

    private static DrewCraftSavedData emptyData() {
        CompoundTag tag = new CompoundTag();
        tag.putInt("SchemaVersion", DrewCraftSavedData.CURRENT_SCHEMA_VERSION);
        return DrewCraftSavedData.load(tag, null);
    }
}
