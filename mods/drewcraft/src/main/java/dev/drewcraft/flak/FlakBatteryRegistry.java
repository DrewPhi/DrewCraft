package dev.drewcraft.flak;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.world.phys.Vec3;

/**
 * Server-side registry of live flak zones. Zones are data (see
 * {@link FlakZone}); the physical tower/controller block owns placement and
 * destruction removes the zone through this registry. Bounded by construction:
 * playtest sites number in single digits.
 */
public final class FlakBatteryRegistry {
    private static final Map<String, FlakZone> ZONES = new LinkedHashMap<>();
    private static final Map<String, BurstRecord> LAST_BURST = new LinkedHashMap<>();

    private FlakBatteryRegistry() {
    }

    public static synchronized boolean register(FlakZone zone) {
        if (ZONES.containsKey(zone.zoneId())) {
            return false;
        }
        ZONES.put(zone.zoneId(), zone);
        return true;
    }

    public static synchronized boolean remove(String zoneId) {
        LAST_BURST.remove(zoneId);
        return ZONES.remove(zoneId) != null;
    }

    public static synchronized List<FlakZone> zones() {
        return new ArrayList<>(ZONES.values());
    }

    public static synchronized void clearForTests() {
        ZONES.clear();
        LAST_BURST.clear();
    }

    static synchronized void recordBurst(String zoneId, Vec3 burst, double damage, long gameTime) {
        LAST_BURST.put(zoneId, new BurstRecord(burst, damage, gameTime));
    }

    public static synchronized Map<String, BurstRecord> lastBursts() {
        return new LinkedHashMap<>(LAST_BURST);
    }

    public record BurstRecord(Vec3 burst, double damage, long gameTime) {
    }
}
