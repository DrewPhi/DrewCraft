package dev.drewcraft.strategic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicGroupState;
import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.model.StrategicRoute;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class StrategicGroupTest {
    @Test
    void catchupIsClampedAndExcessTimeIsDiscarded() {
        StrategicPosition start = new StrategicPosition("minecraft:overworld", 0.0, 0.0);
        StrategicPosition destination = new StrategicPosition("minecraft:overworld", 1000.0, 0.0);
        StrategicGroup group = new StrategicGroup(
                UUID.fromString("00000000-0000-0000-0000-000000000001"),
                "test:faction",
                StrategicGroupType.TEST,
                null,
                start,
                StrategicRoute.between(start, destination),
                10.0,
                Map.of("minecraft:zombie", 10),
                10,
                StrategicGroupState.TRAVELING,
                100L
        );

        StrategicGroup.AdvanceResult result = group.advanceToGameTime(2100L, 10.0);
        assertTrue(result.catchupClamped());
        assertEquals(10.0, result.elapsedSeconds(), 1.0e-9);
        assertEquals(100.0, result.distanceMoved(), 1.0e-9);
        assertEquals(100.0, group.position().x(), 1.0e-9);
        assertEquals(2100L, group.lastSimulatedGameTime());
        assertEquals(90.0, group.etaSeconds(), 1.0e-9);

        StrategicGroup.AdvanceResult sameTime = group.advanceToGameTime(2100L, 10.0);
        assertEquals(0.0, sameTime.elapsedSeconds(), 1.0e-9);
        assertFalse(sameTime.changedPosition());
    }

    @Test
    void arrivalStopsAtDestination() {
        StrategicPosition start = new StrategicPosition("minecraft:overworld", 0.0, 0.0);
        StrategicPosition destination = new StrategicPosition("minecraft:overworld", 25.0, 0.0);
        StrategicGroup group = StrategicGroup.testGroup(start, destination, 0L);

        StrategicGroup.AdvanceResult result = group.advanceBySeconds(100.0, 100.0);
        assertTrue(result.arrived());
        assertEquals(destination, group.position());
        assertEquals(StrategicGroupState.ARRIVED, group.state());
        assertEquals(destination, group.destination());
        assertEquals(0.0, group.etaSeconds(), 1.0e-9);
    }

    @Test
    void patrolTurnsAroundInsteadOfBecomingPermanentlyInert() {
        StrategicPosition start = new StrategicPosition("minecraft:overworld", 0.0, 0.0);
        StrategicPosition destination = new StrategicPosition("minecraft:overworld", 25.0, 0.0);
        StrategicGroup group = new StrategicGroup(
                UUID.randomUUID(), "test:faction", StrategicGroupType.PATROL, null,
                start, StrategicRoute.between(start, destination), 2.5,
                Map.of("minecraft:zombie", 1), 1, StrategicGroupState.TRAVELING, 0L
        );

        assertTrue(group.advanceBySeconds(100.0, 100.0).arrived());
        assertEquals(destination, group.position());
        assertEquals(start, group.destination());
        assertEquals(StrategicGroupState.TRAVELING, group.state());

        group.advanceBySeconds(10.0, 10.0);
        assertEquals(start, group.position());
    }
}
