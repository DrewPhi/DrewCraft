package dev.drewcraft.strategic.faction;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.source.SourceClass;
import java.util.Map;
import org.junit.jupiter.api.Test;

class StrategicFactionCatalogTest {
    @Test
    void packagedCatalogContainsV1HostileRolesAndCompositions() {
        StrategicFactionCatalog catalog = StrategicFactionCatalog.defaultCatalog();
        for (StrategicGroupType role : new StrategicGroupType[]{
                StrategicGroupType.PATROL,
                StrategicGroupType.HORDE,
                StrategicGroupType.RAID,
                StrategicGroupType.ARMY,
                StrategicGroupType.REINFORCEMENT
        }) {
            assertTrue(catalog.byRole("drewcraft:undead", SourceClass.STRONGHOLD, role).isPresent(), role.name());
            assertTrue(catalog.byRole("drewcraft:raiders", SourceClass.STRONGHOLD, role).isPresent(), role.name());
        }
    }

    @Test
    void armyCompositionExactlyConservesRepresentedStrength() {
        StrategicForceTemplate army = StrategicFactionCatalog.defaultCatalog()
                .byRole("drewcraft:undead", SourceClass.STRONGHOLD, StrategicGroupType.ARMY)
                .orElseThrow();
        int strength = army.desiredStrength(32);
        Map<String, Integer> composition = army.compositionForStrength(strength);

        assertEquals(256, strength);
        assertEquals(strength, composition.values().stream().mapToInt(Integer::intValue).sum());
        assertTrue(composition.size() >= 3);
    }

    @Test
    void deterministicSelectionNeverChoosesUnaffordableTemplate() {
        StrategicFactionCatalog catalog = StrategicFactionCatalog.defaultCatalog();
        StrategicForceTemplate selected = catalog.select(
                "drewcraft:undead", SourceClass.STRONGHOLD, 0L, 64, 32
        ).orElseThrow();
        assertTrue(selected.desiredStrength(32) <= 64);
    }
}
