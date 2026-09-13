package dev.drewcraft.strategic.encounter;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class StrategicSpawnBudgetTest {
    @Test
    void neverAllowsMoreThanConfiguredSuccessfulSpawns() {
        StrategicSpawnBudget budget = new StrategicSpawnBudget(3);
        assertEquals(3, budget.remaining());
        assertTrue(budget.tryConsume());
        assertTrue(budget.tryConsume());
        assertTrue(budget.tryConsume());
        assertTrue(budget.exhausted());
        assertEquals(3, budget.consumed());
        assertEquals(0, budget.remaining());
        assertFalse(budget.tryConsume());
        assertEquals(3, budget.consumed());
    }
}
