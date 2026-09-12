package dev.drewcraft.strategic.routing;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.strategic.model.StrategicPosition;
import org.junit.jupiter.api.Test;

class StrategicRoutePlannerTest {
    @Test
    void routesAroundBlockedCellsWithoutCornerCutting() {
        StrategicTerrainCostMap terrain = new StrategicTerrainCostMap(64);
        String dimension = "minecraft:overworld";
        for (int z = -2; z <= 2; z++) {
            if (z != 2) terrain.put(new StrategicCell(dimension, 3, z), StrategicTerrainClass.BLOCKED);
        }
        StrategicRoutePlanner planner = new StrategicRoutePlanner(terrain, 5000, 8);
        StrategicPosition start = new StrategicPosition(dimension, 32, 32);
        StrategicPosition destination = new StrategicPosition(dimension, 6 * 64 + 32, 32);

        StrategicRoutePlanner.PlanResult result = planner.plan(start, destination);

        assertTrue(result.success(), result.status());
        assertTrue(result.expandedNodes() < 5000);
        assertTrue(result.route().waypoints().stream().anyMatch(p -> p.z() > 64));
    }

    @Test
    void blockedDestinationFailsExplicitly() {
        StrategicTerrainCostMap terrain = new StrategicTerrainCostMap(64);
        StrategicPosition start = new StrategicPosition("minecraft:overworld", 0, 0);
        StrategicPosition destination = new StrategicPosition("minecraft:overworld", 512, 0);
        terrain.put(StrategicCell.fromPosition(destination, 64), StrategicTerrainClass.BLOCKED);

        StrategicRoutePlanner.PlanResult result = new StrategicRoutePlanner(terrain, 1000, 4).plan(start, destination);

        assertFalse(result.success());
        assertEquals("start_or_destination_blocked", result.status());
    }

    @Test
    void terrainCostsChangeEtaAndPhysicalSpeed() {
        String dimension = "minecraft:overworld";
        StrategicTerrainCostMap normal = new StrategicTerrainCostMap(64);
        StrategicTerrainCostMap difficult = new StrategicTerrainCostMap(64);
        StrategicPosition start = new StrategicPosition(dimension, 1, 1);
        StrategicPosition destination = new StrategicPosition(dimension, 257, 1);
        for (int x = 0; x <= 4; x++) {
            difficult.put(new StrategicCell(dimension, x, 0), StrategicTerrainClass.DIFFICULT);
        }

        var normalRoute = new StrategicRoutePlanner(normal, 1000, 4).plan(start, destination).route();
        var difficultRoute = new StrategicRoutePlanner(difficult, 1000, 4).plan(start, destination).route();

        assertTrue(difficultRoute.remainingCostFrom(start) > normalRoute.remainingCostFrom(start));
        double normalMoved = normalRoute.advance(start, 100).distanceMoved();
        double difficultMoved = difficultRoute.advance(start, 100).distanceMoved();
        assertTrue(difficultMoved < normalMoved);
    }
}
