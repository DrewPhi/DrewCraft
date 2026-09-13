package dev.drewcraft.strategic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertNotEquals;

import dev.drewcraft.strategic.model.StrategicGroup;
import dev.drewcraft.strategic.model.StrategicPosition;
import dev.drewcraft.strategic.simulation.StrategicScheduler;
import java.util.List;
import org.junit.jupiter.api.Test;

class StrategicSchedulerTest {
    @Test
    void groupCountBudgetDefersExcessWork() {
        StrategicGroup first = groupAt(0.0);
        StrategicGroup second = groupAt(100.0);
        StrategicGroup third = groupAt(200.0);

        StrategicScheduler.CycleStats stats = StrategicScheduler.advanceGroups(
                List.of(first, second, third),
                20L,
                2,
                1000.0,
                100.0
        );

        assertEquals(3, stats.groupsSeen());
        assertEquals(2, stats.groupsProcessed());
        assertEquals(1, stats.groupsDeferred());
        assertEquals(2, stats.groupsUpdated());
        assertEquals(2, stats.groupsMoved());
        assertTrue(stats.elapsedNanos() >= 0L);
    }

    @Test
    void roundRobinCursorEventuallyAdvancesEveryGroup() {
        List<StrategicGroup> groups = List.of(groupAt(0.0), groupAt(100.0), groupAt(200.0));
        StrategicScheduler.CycleStats first = StrategicScheduler.advanceGroupsFromIndex(
                groups, 20L, 2, 1000.0, 100.0, 0
        );
        double initiallyDeferredX = groups.stream()
                .filter(group -> group.lastSimulatedGameTime() == 0L)
                .findFirst().orElseThrow().position().x();

        StrategicScheduler.CycleStats second = StrategicScheduler.advanceGroupsFromIndex(
                groups, 40L, 2, 1000.0, 100.0, first.nextCursor()
        );

        assertNotEquals(0L, second.nextCursor());
        assertTrue(groups.stream().allMatch(group -> group.lastSimulatedGameTime() > 0L));
        assertNotEquals(initiallyDeferredX, groups.stream()
                .filter(group -> group.lastSimulatedGameTime() == 40L)
                .findFirst().orElseThrow().position().x());
    }

    private static StrategicGroup groupAt(double x) {
        return StrategicGroup.testGroup(
                new StrategicPosition("minecraft:overworld", x, 0.0),
                new StrategicPosition("minecraft:overworld", x + 1000.0, 0.0),
                0L
        );
    }
}
