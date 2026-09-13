package dev.drewcraft.strategic.siege;

import dev.drewcraft.strategic.model.StrategicGroupType;
import java.util.Set;

/** V1 policy: only raids/armies may intentionally breach, and only designated heavy/melee units do it. */
public final class SiegeRolePolicy {
    private static final Set<String> BREAKER_TYPES = Set.of(
            "minecraft:zombie", "minecraft:husk", "minecraft:vindicator", "minecraft:ravager"
    );

    private SiegeRolePolicy() { }

    public static boolean groupMaySiege(StrategicGroupType type) {
        return type == StrategicGroupType.RAID || type == StrategicGroupType.ARMY;
    }

    public static boolean entityMayBreach(String entityTypeId) {
        return BREAKER_TYPES.contains(entityTypeId);
    }
}
