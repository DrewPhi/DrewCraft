package dev.drewcraft.standard;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;

final class FlightstoneMonumentTest {
    @Test
    void describeStaysSparseThroughMilestones() {
        String fresh = FlightstoneMonumentBlock.describe(List.of());
        assertTrue(fresh.contains("Eight chains"));
        String first = FlightstoneMonumentBlock.describe(List.of("ashen_gate"));
        assertTrue(first.contains("1 of 8"));
        String done = FlightstoneMonumentBlock.describe(
                List.of("a", "b", "c", "d", "e", "f", "g", "h"));
        assertTrue(done.contains("Vespera"));
    }
}
