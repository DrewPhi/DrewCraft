package dev.drewcraft.lore;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import net.minecraft.util.RandomSource;
import org.junit.jupiter.api.Test;

final class LoreDropPolicyTest {
    @Test
    void invokerDropsMostOftenAndUnknownTypesNever() {
        assertTrue(LoreDropPolicy.killRate("illagerinvasion:invoker")
                > LoreDropPolicy.killRate("illagerinvasion:basher"));
        assertEquals(0.0, LoreDropPolicy.killRate("minecraft:zombie"));
    }

    @Test
    void fullCoordinatesAreRare() {
        RandomSource rng = new net.minecraft.world.level.levelgen.XoroshiroRandomSource(1234L);
        int full = 0;
        for (int i = 0; i < 4000; i++) {
            if (LoreDropPolicy.rollMode(rng).equals("x_y_z_full")) {
                full++;
            }
        }
        assertTrue(full < 200);
    }

    @Test
    void fieldBooksBiasHomeSite() {
        RandomSource rng = new net.minecraft.world.level.levelgen.XoroshiroRandomSource(7L);
        int home = 0;
        for (int i = 0; i < 1000; i++) {
            if (LoreDropPolicy.chooseSite(rng, "ashen_gate", List.of("cairnwatch")).equals("ashen_gate")) {
                home++;
            }
        }
        assertTrue(home > 600);
    }

    @Test
    void waymarkWithholdsMissingAxesAndKeepsName() {
        List<String> pages = WaymarkRenderer.render("Ashen Gate", -8421, 72, 3910, "x_only");
        String text = String.join("\n", pages);
        assertTrue(text.contains("Ashen Gate"));
        assertTrue(text.contains("X: -8421"));
        assertTrue(text.contains("Y: [withheld]"));
        assertTrue(text.contains("Z: [withheld]"));
    }

    @Test
    void waymarkRejectsUnknownModes() {
        assertThrows(IllegalArgumentException.class,
                () -> WaymarkRenderer.render("Ashen Gate", 0, 0, 0, "everything"));
    }

    @Test
    void sealedBookCarriesCoordinates() {
        List<String> pages = CovenantBooks.sealedArchivePages("ashen_gate", "Seal I", 48, 64, 0);
        String text = String.join("\n", pages);
        assertTrue(text.contains("Seal I"));
        assertTrue(text.contains("X: 48"));
        assertTrue(text.contains("ashen_gate"));
    }
}
