package dev.drewcraft.strategic.siege;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.strategic.model.StrategicGroupType;
import org.junit.jupiter.api.Test;

class SiegeRolePolicyTest {
    @Test
    void onlyRaidAndArmyRolesMayInitiateBreaches() {
        assertTrue(SiegeRolePolicy.groupMaySiege(StrategicGroupType.RAID));
        assertTrue(SiegeRolePolicy.groupMaySiege(StrategicGroupType.ARMY));
        assertFalse(SiegeRolePolicy.groupMaySiege(StrategicGroupType.PATROL));
        assertFalse(SiegeRolePolicy.groupMaySiege(StrategicGroupType.HORDE));
        assertFalse(SiegeRolePolicy.groupMaySiege(StrategicGroupType.REINFORCEMENT));
        assertFalse(SiegeRolePolicy.groupMaySiege(StrategicGroupType.HERD));
    }

    @Test
    void onlyDesignatedHeavyOrMeleeEntitiesMayBreak() {
        assertTrue(SiegeRolePolicy.entityMayBreach("minecraft:zombie"));
        assertTrue(SiegeRolePolicy.entityMayBreach("minecraft:husk"));
        assertTrue(SiegeRolePolicy.entityMayBreach("minecraft:vindicator"));
        assertTrue(SiegeRolePolicy.entityMayBreach("minecraft:ravager"));
        assertFalse(SiegeRolePolicy.entityMayBreach("minecraft:skeleton"));
        assertFalse(SiegeRolePolicy.entityMayBreach("minecraft:pillager"));
        assertFalse(SiegeRolePolicy.entityMayBreach("minecraft:witch"));
    }
}
