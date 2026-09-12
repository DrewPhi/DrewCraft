package dev.drewcraft.strategic.routing;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

import dev.drewcraft.strategic.model.StrategicPosition;
import org.junit.jupiter.api.Test;

class StrategicRoutingBoundsTest {
    @Test
    void nodeExpansionCapFailsInsteadOfSearchingWithoutBound() {
        StrategicTerrainCostMap terrain = new StrategicTerrainCostMap(64);
        StrategicPosition start = new StrategicPosition("minecraft:overworld", 0, 0);
        StrategicPosition destination = new StrategicPosition("minecraft:overworld", 20000, 20000);

        StrategicRoutePlanner.PlanResult result = new StrategicRoutePlanner(terrain, 2, 64).plan(start, destination);

        assertFalse(result.success());
        assertEquals("max_expanded_nodes", result.status());
    }
}
