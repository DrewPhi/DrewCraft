package dev.drewcraft.strategic.siege;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Set;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;

class BoundedSiegePlannerTest {
    @Test
    void openGateRouteWinsWithoutBreakingAnything() {
        SiegeGrid.Builder builder = SiegeGrid.builder(9, 5).start(1, 2).goal(7, 2);
        for (int z = 0; z < 5; z++) builder.set(4, z, new SiegeCell(SiegeCellKind.SOLID_BARRIER, 2.0));
        builder.set(4, 2, SiegeCell.open()); // open gate / doorway

        SiegePlan plan = BoundedSiegePlanner.plan(builder.build(), 256, 4);
        assertEquals(SiegePlan.Status.OPEN_ROUTE, plan.status());
        assertTrue(plan.breaches().isEmpty());
        assertTrue(plan.path().contains(new SiegePlan.Point(4, 2)));
    }

    @Test
    void sealedFortChoosesUsefulWeakBarrierInsteadOfRandomWall() {
        SiegeGrid.Builder builder = SiegeGrid.builder(9, 7).start(1, 3).goal(7, 3);
        for (int z = 0; z < 7; z++) builder.set(4, z, new SiegeCell(SiegeCellKind.SOLID_BARRIER, 4.0));
        builder.set(4, 3, new SiegeCell(SiegeCellKind.WEAK_BARRIER, 0.5));

        SiegePlan plan = BoundedSiegePlanner.plan(builder.build(), 512, 3);
        assertEquals(SiegePlan.Status.BREACH_ROUTE, plan.status());
        assertEquals(1, plan.breaches().size());
        assertEquals(new SiegePlan.Point(4, 3), new SiegePlan.Point(plan.breaches().getFirst().x(), plan.breaches().getFirst().z()));
        assertEquals(SiegeCellKind.WEAK_BARRIER, plan.breaches().getFirst().kind());
    }

    @Test
    void nearbyDecorationIsNotSelectedMerelyBecauseItIsClose() {
        SiegeGrid.Builder builder = SiegeGrid.builder(9, 7).start(1, 3).goal(7, 3);
        for (int z = 0; z < 7; z++) builder.set(4, z, new SiegeCell(SiegeCellKind.SOLID_BARRIER, 4.0));
        builder.set(4, 3, new SiegeCell(SiegeCellKind.WEAK_BARRIER, 1.0));
        builder.set(2, 2, new SiegeCell(SiegeCellKind.DECORATIVE, 0.1)); // tempting by proximity, useless to objective
        builder.set(3, 2, new SiegeCell(SiegeCellKind.DECORATIVE, 0.1));

        SiegePlan plan = BoundedSiegePlanner.plan(builder.build(), 512, 4);
        Set<SiegePlan.Point> breached = plan.breaches().stream()
                .map(step -> new SiegePlan.Point(step.x(), step.z()))
                .collect(Collectors.toSet());
        assertEquals(SiegePlan.Status.BREACH_ROUTE, plan.status());
        assertFalse(breached.contains(new SiegePlan.Point(2, 2)));
        assertFalse(breached.contains(new SiegePlan.Point(3, 2)));
        assertTrue(breached.contains(new SiegePlan.Point(4, 3)));
    }

    @Test
    void protectedBarrierCannotBeBreachedAndSearchIsHardBounded() {
        SiegeGrid.Builder builder = SiegeGrid.builder(31, 31).start(1, 15).goal(29, 15);
        for (int z = 0; z < 31; z++) builder.set(15, z, SiegeCell.protectedCell());

        SiegePlan bounded = BoundedSiegePlanner.plan(builder.build(), 20, 10);
        assertEquals(SiegePlan.Status.BOUNDED_OUT, bounded.status());
        assertTrue(bounded.expandedNodes() <= 20);

        SiegePlan exhausted = BoundedSiegePlanner.plan(builder.build(), 2000, 10);
        assertEquals(SiegePlan.Status.NO_ROUTE, exhausted.status());
        assertTrue(exhausted.breaches().isEmpty());
    }
}
