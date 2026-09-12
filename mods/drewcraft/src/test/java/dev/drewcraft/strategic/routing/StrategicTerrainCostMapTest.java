package dev.drewcraft.strategic.routing;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class StrategicTerrainCostMapTest {
    @Test
    void unknownCellsUseExplicitConservativePolicy() {
        StrategicTerrainCostMap map = new StrategicTerrainCostMap(64);
        StrategicCell cell = new StrategicCell("minecraft:overworld", 10, 20);
        assertEquals(StrategicTerrainClass.UNKNOWN, map.terrainClass(cell));
        assertEquals(1.25, map.multiplier(cell), 1.0e-9);
        assertTrue(map.traversable(cell));
    }

    @Test
    void mutationsVersionTheCostLayerForEventDrivenRouteInvalidation() {
        StrategicTerrainCostMap map = new StrategicTerrainCostMap(64);
        StrategicCell cell = new StrategicCell("minecraft:overworld", 1, 2);
        long before = map.version();
        assertTrue(map.put(cell, StrategicTerrainClass.WATER));
        assertEquals(before + 1, map.version());
        assertFalse(map.put(cell, StrategicTerrainClass.WATER));
        assertEquals(before + 1, map.version());
        assertTrue(map.put(cell, StrategicTerrainClass.BLOCKED));
        assertEquals(before + 2, map.version());
        assertFalse(map.traversable(cell));
    }
}
