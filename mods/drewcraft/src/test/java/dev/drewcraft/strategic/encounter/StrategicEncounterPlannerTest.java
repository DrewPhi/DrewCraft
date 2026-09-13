package dev.drewcraft.strategic.encounter;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicRoute;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class StrategicEncounterPlannerTest {
    @Test
    void fillsOnlyFreeSlotsAndNeverExceedsStrategicComposition() {
        StrategicPosition start = new StrategicPosition("minecraft:overworld", 0.0, 0.0);
        StrategicGroup group = new StrategicGroup(
                UUID.randomUUID(), "drewcraft:test", StrategicGroupType.TEST, null,
                start, StrategicRoute.between(start, new StrategicPosition("minecraft:overworld", 100, 0)),
                2.5, Map.of("minecraft:zombie", 80, "minecraft:skeleton", 20), 100,
                StrategicGroupState.TRAVELING, 0L
        );
        StrategicGroupState resume = group.suspendForEncounter();
        StrategicEncounter encounter = StrategicEncounter.preparing(group.groupId(), resume, 0L);
        for (int i = 0; i < 10; i++) encounter.registerSpawn(UUID.randomUUID(), "minecraft:zombie");
        encounter.markMaterialized();

        List<String> wave = StrategicEncounterPlanner.nextWave(group, encounter, 64);
        assertEquals(54, wave.size());
        assertTrue(wave.stream().allMatch(id -> id.equals("minecraft:zombie") || id.equals("minecraft:skeleton")));

        for (String type : wave) encounter.registerSpawn(UUID.randomUUID(), type);
        assertEquals(64, encounter.activeEntityCount());
        assertTrue(StrategicEncounterPlanner.nextWave(group, encounter, 64).isEmpty());
    }
}
