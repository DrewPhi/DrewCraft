package dev.drewcraft.flak;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Optional;
import java.util.Random;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

final class FlakMathTest {
    @Test
    void predictionLeadsAlongVelocity() {
        Vec3 predicted = FlakMath.predict(new Vec3(0, 100, 0), new Vec3(20, 0, 0), 1.5);
        assertEquals(30.0, predicted.x, 1.0e-9);
        assertEquals(100.0, predicted.y, 1.0e-9);
    }

    @Test
    void accuracyFallsWithAltitudeAndStaysBounded() {
        double low = FlakMath.hitProbability(70.0, 1.0);
        double high = FlakMath.hitProbability(300.0, 1.0);
        assertTrue(low > high);
        assertTrue(low <= 0.5 && high >= 0.02);
    }

    @Test
    void damageFallsToZeroAtRadius() {
        assertEquals(FlakMath.MAX_BURST_DAMAGE, FlakMath.damageForDistance(0.0), 1.0e-9);
        assertEquals(0.0, FlakMath.damageForDistance(FlakMath.DAMAGE_RADIUS_BLOCKS + 1.0), 1.0e-9);
    }

    @Test
    void nullBridgesDegradeToEmpty() {
        assertEquals(Optional.empty(), FlakMath.rollBurst(null, new Vec3(1, 0, 0), 1.0, 6.0, new Random(1)));
        assertEquals(Optional.empty(), FlakMath.rollBurst(new Vec3(0, 0, 0), null, 1.0, 6.0, new Random(1)));
    }

    @Test
    void cadenceGateBoundsEvents() {
        assertTrue(FlakMath.shouldFire(40L, 20));
        assertFalse(FlakMath.shouldFire(41L, 20));
        assertFalse(FlakMath.shouldFire(40L, 0));
    }

    @Test
    void zoneCoverageIsSpherical() {
        FlakZone zone = new FlakZone("z1", "closed_wing_bastion", new Vec3(0, 64, 0), 128.0, 1.0, 20, 1.0, 6.0);
        assertTrue(zone.covers(new Vec3(100, 64, 0)));
        assertFalse(zone.covers(new Vec3(200, 64, 0)));
    }
}
