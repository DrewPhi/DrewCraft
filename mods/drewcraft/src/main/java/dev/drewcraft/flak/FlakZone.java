package dev.drewcraft.flak;

import net.minecraft.world.phys.Vec3;

/** A simple anti-air defense anchor tied to a physical tower/site. */
public record FlakZone(String zoneId, String siteId, Vec3 center, double radiusBlocks,
        double tierMultiplier, int periodTicks, double leadSeconds, double errorRadiusBlocks) {
    public FlakZone {
        if (radiusBlocks <= 0 || periodTicks <= 0 || errorRadiusBlocks < 0) {
            throw new IllegalArgumentException("invalid flak zone bounds");
        }
    }

    public boolean covers(Vec3 aircraftPos) {
        double dx = aircraftPos.x - center.x;
        double dy = aircraftPos.y - center.y;
        double dz = aircraftPos.z - center.z;
        return (dx * dx + dy * dy + dz * dz) <= radiusBlocks * radiusBlocks;
    }
}
