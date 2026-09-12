package dev.drewcraft.strategic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicRoute;
import java.util.List;
import org.junit.jupiter.api.Test;

class StrategicRouteTest {
    @Test
    void advancesAcrossMultipleCachedSegmentsWithoutPathSearch() {
        StrategicPosition start = new StrategicPosition("minecraft:overworld", 0.0, 0.0);
        StrategicPosition corner = new StrategicPosition("minecraft:overworld", 100.0, 0.0);
        StrategicPosition destination = new StrategicPosition("minecraft:overworld", 100.0, 100.0);
        StrategicRoute route = new StrategicRoute(List.of(start, corner, destination), 1);

        StrategicRoute.AdvanceResult first = route.advance(start, 150.0);
        assertEquals(100.0, first.position().x(), 1.0e-9);
        assertEquals(50.0, first.position().z(), 1.0e-9);
        assertEquals(150.0, first.distanceMoved(), 1.0e-9);
        assertFalse(first.arrived());
        assertEquals(2, route.cursor());
        assertEquals(50.0, route.remainingDistanceFrom(first.position()), 1.0e-9);

        StrategicRoute.AdvanceResult second = route.advance(first.position(), 100.0);
        assertTrue(second.arrived());
        assertEquals(destination, second.position());
        assertEquals(50.0, second.distanceMoved(), 1.0e-9);
        assertEquals(3, route.cursor());
    }
}
