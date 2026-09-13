package dev.drewcraft.strategic.routing;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.persistence.StrategicGroupNbt;
import dev.drewcraft.strategic.simulation.StrategicScheduler;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class StrategicUnloadedTravelProofTest {
    @Test
    void tenThousandBlockRoutePersistsMidJourneyAndFinishesThroughCoarseSchedulerWithoutWorldAccess() {
        String dimension = "minecraft:overworld";
        StrategicTerrainCostMap terrain = new StrategicTerrainCostMap(64);
        StrategicPosition start = new StrategicPosition(dimension, 32, 32);
        StrategicPosition destination = new StrategicPosition(dimension, 10032, 32);

        // A difficult band proves route/ETA contain weighted terrain rather than only Euclidean distance.
        for (int x = 60; x <= 70; x++) {
            terrain.put(new StrategicCell(dimension, x, 0), StrategicTerrainClass.DIFFICULT);
        }
        StrategicRoutePlanner.PlanResult planned = new StrategicRoutePlanner(terrain, 20000, 32).plan(start, destination);
        assertTrue(planned.success(), planned.status());
        assertTrue(planned.route().waypoints().size() > 100);

        StrategicGroup original = new StrategicGroup(
                UUID.randomUUID(), "drewcraft:test", StrategicGroupType.TEST, null,
                start, planned.route(), 2.5, Map.of("minecraft:zombie", 100), 100,
                StrategicGroupState.TRAVELING, 0L
        );
        double initialEta = original.etaSeconds();
        StrategicScheduler.CycleStats firstCycle = StrategicScheduler.advanceGroups(
                List.of(original), 24_000L, 10, 100.0, 1200.0
        );
        assertEquals(1, firstCycle.groupsMoved());
        assertTrue(original.position().x() > start.x());
        assertTrue(original.etaSeconds() < initialEta);

        // NBT round-trip represents a server save/restart while no world/chunk/entity object exists in this proof.
        StrategicGroup restored = StrategicGroupNbt.load(StrategicGroupNbt.save(original));
        assertEquals(original.groupId(), restored.groupId());
        assertEquals(original.position().x(), restored.position().x(), 1.0e-9);
        assertEquals(original.route().cursor(), restored.route().cursor());
        assertEquals(original.route().segmentCostMultipliers(), restored.route().segmentCostMultipliers());

        StrategicScheduler.CycleStats secondCycle = StrategicScheduler.advanceGroups(
                List.of(restored), 224_000L, 10, 100.0, 10_000.0
        );
        assertEquals(1, secondCycle.groupsArrived());
        assertEquals(StrategicGroupState.ARRIVED, restored.state());
        assertEquals(destination.x(), restored.position().x(), 1.0e-6);
        assertEquals(destination.z(), restored.position().z(), 1.0e-6);
        assertEquals(0.0, restored.etaSeconds(), 1.0e-9);
    }
}
