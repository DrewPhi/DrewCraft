package dev.drewcraft.flak;

import java.util.Optional;
import java.util.Random;
import net.minecraft.world.phys.Vec3;

/**
 * Pure flak-burst math for Covenant anti-air zones.
 *
 * <p>Deliberately cheap V1 implementation: no turret/ballistics simulation.
 * Given a supported aircraft position + velocity, predict a short lead point,
 * add substantial random error, and decide hits with altitude-dependent
 * accuracy. Flak never damages terrain by construction: this class computes
 * points and damage numbers only and mutates no blocks.
 *
 * <p>All bridge failures must degrade to {@link Optional#empty()} at the call
 * site (missing weather/vehicle snapshot, unsupported aircraft) rather than
 * throwing.
 */
public final class FlakMath {
    /** Maximum damage of a single damaging burst (half-hearts scale agnostic: caller clamps to entity). */
    public static final double MAX_BURST_DAMAGE = 6.0;
    /** Damage falls to zero beyond this distance from the burst point. */
    public static final double DAMAGE_RADIUS_BLOCKS = 8.0;
    /** Reference altitude for accuracy falloff (sea-level-ish Overworld). */
    public static final double REFERENCE_ALTITUDE = 64.0;

    private FlakMath() {}

    /** Velocity-predicted aircraft position after {@code leadSeconds}. */
    public static Vec3 predict(Vec3 position, Vec3 velocity, double leadSeconds) {
        return new Vec3(
                position.x + velocity.x * leadSeconds,
                position.y + velocity.y * leadSeconds,
                position.z + velocity.z * leadSeconds);
    }

    /** Burst point: predicted position plus uniform random error in each axis. */
    public static Vec3 burstPoint(Vec3 predicted, double errorRadiusBlocks,
                                  net.minecraft.util.RandomSource rng) {
        double ex = (rng.nextDouble() * 2.0 - 1.0) * errorRadiusBlocks;
        double ey = (rng.nextDouble() * 2.0 - 1.0) * errorRadiusBlocks;
        double ez = (rng.nextDouble() * 2.0 - 1.0) * errorRadiusBlocks;
        return new Vec3(predicted.x + ex, predicted.y + ey, predicted.z + ez);
    }

    /**
     * Hit probability in [0, 1]. Accuracy falls with altitude: higher flight
     * trades safety against navigation/weather/mission cost. Tier multipliers:
     * minor outpost 0.7, regional 1.0, capital 1.3.
     */
    public static double hitProbability(double altitudeY, double tierMultiplier) {
        double altitudeFactor = Math.exp(-(altitudeY - REFERENCE_ALTITUDE) / 150.0);
        double p = 0.35 * altitudeFactor * tierMultiplier;
        if (p < 0.02) {
            return 0.02;
        }
        return Math.min(p, 0.5);
    }

    /** Bounded damage for an aircraft at {@code distanceBlocks} from the burst. Zero beyond radius. */
    public static double damageForDistance(double distanceBlocks) {
        if (distanceBlocks >= DAMAGE_RADIUS_BLOCKS) {
            return 0.0;
        }
        double falloff = 1.0 - (distanceBlocks / DAMAGE_RADIUS_BLOCKS);
        return MAX_BURST_DAMAGE * falloff;
    }

    /** Deterministic cadence gate so flak events stay bounded under load. */
    public static boolean shouldFire(long tickHash, int periodTicks) {
        if (periodTicks <= 0) {
            return false;
        }
        return (tickHash % periodTicks) == 0;
    }

    /**
     * Full burst roll, or empty when the bridge has nothing valid to shoot at
     * (null inputs degrade safely instead of crashing the tick).
     */
    public static Optional<Vec3> rollBurst(Vec3 aircraftPos, Vec3 aircraftVel,
            double leadSeconds, double errorRadiusBlocks, net.minecraft.util.RandomSource rng) {
        if (aircraftPos == null || aircraftVel == null || rng == null) {
            return Optional.empty();
        }
        if (errorRadiusBlocks < 0) {
            return Optional.empty();
        }
        return Optional.of(burstPoint(predict(aircraftPos, aircraftVel, leadSeconds), errorRadiusBlocks, rng));
    }
}
