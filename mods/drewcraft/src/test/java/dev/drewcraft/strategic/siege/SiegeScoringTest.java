package dev.drewcraft.strategic.siege;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

import org.junit.jupiter.api.Test;

class SiegeScoringTest {
    @Test
    void closedGateIsPreferredOverHardWallEvenWithSmallDetour() {
        SiegeGrid.Builder builder = SiegeGrid.builder(11, 7).start(1, 3).goal(9, 3);
        for (int z = 0; z < 7; z++) builder.set(5, z, new SiegeCell(SiegeCellKind.SOLID_BARRIER, 5.0));
        builder.set(5, 1, new SiegeCell(SiegeCellKind.GATE, 2.0));

        SiegePlan plan = BoundedSiegePlanner.plan(builder.build(), 1024, 3);
        assertEquals(SiegePlan.Status.BREACH_ROUTE, plan.status());
        assertEquals(SiegeCellKind.GATE, plan.breaches().getFirst().kind());
        assertEquals(5, plan.breaches().getFirst().x());
        assertEquals(1, plan.breaches().getFirst().z());
    }

    @Test
    void protectedCellsNeverAppearInBreachCorridor() {
        SiegeGrid.Builder builder = SiegeGrid.builder(9, 5).start(1, 2).goal(7, 2);
        for (int z = 0; z < 5; z++) builder.set(4, z, new SiegeCell(SiegeCellKind.SOLID_BARRIER, 3.0));
        builder.set(4, 2, SiegeCell.protectedCell());
        builder.set(4, 1, new SiegeCell(SiegeCellKind.WEAK_BARRIER, 1.0));

        SiegePlan plan = BoundedSiegePlanner.plan(builder.build(), 512, 2);
        assertEquals(SiegePlan.Status.BREACH_ROUTE, plan.status());
        assertFalse(plan.breaches().stream().anyMatch(step -> step.x() == 4 && step.z() == 2));
        assertEquals(1, plan.breaches().getFirst().z());
    }
}
