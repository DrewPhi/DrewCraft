package dev.drewcraft.aot;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AotIsolationTest {
    @Test void onlyParadisPermitsTitans() {
        assertTrue(AotIsolation.isParadis("dannys-aot:paradis"));
        for (String dimension : new String[]{"minecraft:overworld", "minecraft:the_nether",
                "minecraft:the_end", "dannys-aot:paths", "other:paradis"}) {
            assertFalse(AotIsolation.isParadis(dimension));
        }
    }
}
