package dev.drewcraft.progression;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Map;
import org.junit.jupiter.api.Test;

final class CovenantProgressionTest {
    @Test
    void clearIsIdempotentAndArchivesClue() {
        CovenantProgression progression = new CovenantProgression();
        assertTrue(progression.applyClear("ashen_gate", "Seal I"));
        assertFalse(progression.applyClear("ashen_gate", "Seal I duplicate"));
        assertEquals(1, progression.clearedCount());
        assertEquals(1, progression.flightstoneMarkers());
        assertEquals("Seal I", progression.archivedClues().get("ashen_gate"));
    }

    @Test
    void capitalRevealsAfterEightClears() {
        CovenantProgression progression = new CovenantProgression();
        for (int i = 1; i <= 8; i++) {
            progression.applyClear("site_" + i, "seal_" + i);
        }
        assertTrue(progression.isCapitalRevealed());
    }

    @Test
    void stateSurvivesMapRoundTrip() {
        CovenantProgression progression = new CovenantProgression();
        progression.applyClear("cairnwatch", "Seal VII");
        Map<String, Object> saved = progression.toMap();
        CovenantProgression restored = new CovenantProgression();
        restored.loadMap(saved);
        assertTrue(restored.isCleared("cairnwatch"));
        assertFalse(restored.isCapitalRevealed());
        // Duplicate replay after restart stays idempotent.
        assertFalse(restored.applyClear("cairnwatch", "Seal VII replay"));
    }
}
