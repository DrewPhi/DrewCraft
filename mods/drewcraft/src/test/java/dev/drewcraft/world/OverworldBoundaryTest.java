package dev.drewcraft.world;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

final class OverworldBoundaryTest {
    @Test
    void clampsOutsidePositionsInsideCircularGeneratedArea() {
        OverworldBoundary boundary = new OverworldBoundary(-5120.0, 5120.0, 1024.0);
        assertTrue(boundary.contains(-5120.0, 6144.0));
        assertFalse(boundary.contains(-5120.0, 6144.01));

        OverworldBoundary.Position safe = boundary.clampInside(-5120.0, 7000.0);
        assertEquals(-5120.0, safe.x(), 0.0001);
        assertEquals(6136.0, safe.z(), 0.0001);
        assertTrue(boundary.contains(safe.x(), safe.z()));
    }

    @Test
    void rejectsInvalidBoundary() {
        assertThrows(IllegalArgumentException.class, () -> new OverworldBoundary(0.0, 0.0, 8.0));
    }
}
