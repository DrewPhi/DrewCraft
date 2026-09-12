package dev.drewcraft.radar;

import net.minecraft.world.phys.Vec3;

final class RadarMath {
    private RadarMath() {
    }

    static double bearingDegrees(Vec3 from, Vec3 to) {
        Vec3 delta = to.subtract(from);
        double degrees = Math.toDegrees(Math.atan2(delta.x, delta.z));
        return (degrees + 360.0) % 360.0;
    }

    static double radialVelocity(Vec3 from, Vec3 target, Vec3 targetVelocity) {
        Vec3 line = target.subtract(from);
        if (line.lengthSqr() < 1.0e-12) {
            return 0.0;
        }
        return targetVelocity.dot(line.normalize());
    }

    static double lineAltitude(Vec3 from, Vec3 to, double fraction) {
        return from.y + (to.y - from.y) * fraction;
    }

    static double clamp01(double value) {
        return Math.max(0.0, Math.min(1.0, value));
    }
}
