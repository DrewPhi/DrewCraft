package dev.drewcraft.strategic.routing;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;

import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicRoute;
import org.junit.jupiter.api.Test;

class StrategicRouteCacheTest {
    @Test
    void terrainVersionChangeInvalidatesWithoutGlobalRescan() {
        StrategicRouteCache cache = new StrategicRouteCache(8);
        StrategicPosition start = new StrategicPosition("minecraft:overworld", 0, 0);
        StrategicPosition destination = new StrategicPosition("minecraft:overworld", 1000, 0);
        StrategicRoute route = StrategicRoute.between(start, destination);

        cache.put(start, destination, 4L, route);
        assertNotNull(cache.get(start, destination, 4L));
        assertNull(cache.get(start, destination, 5L));
        assertEquals(1, cache.hits());
        assertEquals(1, cache.misses());
    }

    @Test
    void returnedRoutesHaveIndependentMutableCursors() {
        StrategicRouteCache cache = new StrategicRouteCache(8);
        StrategicPosition start = new StrategicPosition("minecraft:overworld", 0, 0);
        StrategicPosition destination = new StrategicPosition("minecraft:overworld", 1000, 0);
        cache.put(start, destination, 1L, StrategicRoute.between(start, destination));

        StrategicRoute first = cache.get(start, destination, 1L);
        StrategicRoute second = cache.get(start, destination, 1L);
        first.advance(start, 1000.0);

        assertEquals(2, first.cursor());
        assertEquals(1, second.cursor());
    }
}
