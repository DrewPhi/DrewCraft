package dev.drewcraft.flak;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

final class FlakBatteryRegistryTest {
    @Test
    void registryIsIdempotentAndRemovable() {
        FlakBatteryRegistry.clearForTests();
        FlakZone zone = new FlakZone("z1", "s1", new Vec3(0, 64, 0), 128.0, 1.0, 20, 1.0, 6.0);
        assertTrue(FlakBatteryRegistry.register(zone));
        assertFalse(FlakBatteryRegistry.register(zone));
        assertEquals(1, FlakBatteryRegistry.zones().size());
        assertTrue(FlakBatteryRegistry.remove("z1"));
        assertFalse(FlakBatteryRegistry.remove("z1"));
        assertTrue(FlakBatteryRegistry.zones().isEmpty());
    }
}
