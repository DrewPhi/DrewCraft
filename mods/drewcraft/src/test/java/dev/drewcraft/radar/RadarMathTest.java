package dev.drewcraft.radar;

import static org.junit.jupiter.api.Assertions.assertEquals;

import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

final class RadarMathTest {
    @Test
    void bearingUsesProjectPositiveZAsZeroConvention() {
        assertEquals(0.0, RadarMath.bearingDegrees(Vec3.ZERO, new Vec3(0, 0, 10)), 1.0e-9);
        assertEquals(90.0, RadarMath.bearingDegrees(Vec3.ZERO, new Vec3(10, 0, 0)), 1.0e-9);
        assertEquals(180.0, RadarMath.bearingDegrees(Vec3.ZERO, new Vec3(0, 0, -10)), 1.0e-9);
        assertEquals(270.0, RadarMath.bearingDegrees(Vec3.ZERO, new Vec3(-10, 0, 0)), 1.0e-9);
    }

    @Test
    void lineAltitudeInterpolatesForTerrainMasking() {
        assertEquals(75.0, RadarMath.lineAltitude(new Vec3(0, 100, 0), new Vec3(10, 50, 0), 0.5), 1.0e-9);
    }

    @Test
    void radialVelocityProjectsMotionOntoLineOfSight() {
        assertEquals(2.0, RadarMath.radialVelocity(Vec3.ZERO, new Vec3(10, 0, 0), new Vec3(2, 4, 0)), 1.0e-9);
    }
}
