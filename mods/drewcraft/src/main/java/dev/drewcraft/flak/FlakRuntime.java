package dev.drewcraft.flak;

import dev.drewcraft.service.DrewCraftServices;
import dev.drewcraft.service.vehicle.VehicleQueryResult;
import dev.drewcraft.service.vehicle.VehicleSnapshot;
import java.util.List;
import java.util.Optional;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSources;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * Flak tick: for each registered zone on its cadence, query aircraft through
 * {@link dev.drewcraft.service.vehicle.VehicleService} and resolve at most
 * one burst per zone per cycle against the first covered aircraft.
 *
 * <p>Damage applies only to entities near the burst point. Blocks are never
 * touched by construction. Missing bridges, unloaded chunks, and unknown
 * vehicles degrade to doing nothing rather than throwing.
 */
public final class FlakRuntime {
    private FlakRuntime() {
    }

    public static void onServerTick(ServerTickEvent.Post event) {
        MinecraftServer server = event.getServer();
        long gameTime = server.overworld().getGameTime();
        for (ServerLevel level : server.getAllLevels()) {
            tickLevel(level, gameTime);
        }
    }

    static void tickLevel(ServerLevel level, long gameTime) {
        List<FlakZone> zones = FlakBatteryRegistry.zones();
        for (FlakZone zone : zones) {
            if (!FlakMath.shouldFire(gameTime, zone.periodTicks())) {
                continue;
            }
            if (!level.hasChunkAt(new net.minecraft.core.BlockPos(
                    (int) zone.center().x, (int) zone.center().y, (int) zone.center().z))) {
                continue;
            }
            VehicleQueryResult result;
            try {
                result = DrewCraftServices.vehicles().query(level, zone.center(), zone.radiusBlocks());
            } catch (RuntimeException failure) {
                continue;
            }
            if (!result.available()) {
                continue;
            }
            for (VehicleSnapshot snapshot : result.vehicles()) {
                if (!snapshot.aircraft() || !zone.covers(snapshot.position())) {
                    continue;
                }
                fireAt(level, zone, snapshot, gameTime);
                break;
            }
        }
    }

    static void fireAt(ServerLevel level, FlakZone zone, VehicleSnapshot aircraft, long gameTime) {
        double hitChance = FlakMath.hitProbability(aircraft.position().y, zone.tierMultiplier());
        if (level.random.nextDouble() >= hitChance) {
            return;
        }
        // Velocity is per-tick; lead is in seconds (20 ticks).
        Vec3 velocityPerSecond = aircraft.velocityBlocksPerTick().scale(20.0);
        Optional<Vec3> burst = FlakMath.rollBurst(
                aircraft.position(), velocityPerSecond, zone.leadSeconds(),
                zone.errorRadiusBlocks(), level.random);
        if (burst.isEmpty()) {
            return;
        }
        Vec3 point = burst.get();
        double distance = point.distanceTo(aircraft.position());
        double damage = FlakMath.damageForDistance(distance);
        if (damage <= 0.0) {
            return;
        }
        AABB vicinity = new AABB(
                point.x - FlakMath.DAMAGE_RADIUS_BLOCKS, point.y - FlakMath.DAMAGE_RADIUS_BLOCKS,
                point.z - FlakMath.DAMAGE_RADIUS_BLOCKS,
                point.x + FlakMath.DAMAGE_RADIUS_BLOCKS, point.y + FlakMath.DAMAGE_RADIUS_BLOCKS,
                point.z + FlakMath.DAMAGE_RADIUS_BLOCKS);
        DamageSources sources = level.damageSources();
        for (Entity target : level.getEntities((Entity) null, vicinity,
                candidate -> candidate.isAlive() && candidate.position().distanceTo(point)
                        <= FlakMath.DAMAGE_RADIUS_BLOCKS)) {
            target.hurt(sources.magic(), (float) damage);
        }
        FlakBatteryRegistry.recordBurst(zone.zoneId(), point, damage, gameTime);
    }
}
