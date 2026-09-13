package dev.drewcraft.radar;

import dev.drewcraft.service.DrewCraftServices;
import dev.drewcraft.service.power.PowerSample;
import dev.drewcraft.service.terrain.TerrainSample;
import dev.drewcraft.service.vehicle.VehicleQueryResult;
import dev.drewcraft.service.vehicle.VehicleSnapshot;
import dev.drewcraft.service.weather.WeatherSample;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.OptionalDouble;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.Vec3;

/** Shared server-authoritative radar sensing pipeline for ground and aircraft sensors. */
public final class RadarEngine {
    public static final int CACHE_TICKS = 10;
    public static final int MAX_TERRAIN_SAMPLES = 32;
    private static final double TERRAIN_CLEARANCE_BLOCKS = 2.0;
    private static final RadarEngine INSTANCE = new RadarEngine();

    private final Map<String, CachedScan> cache = new ConcurrentHashMap<>();

    private RadarEngine() {
    }

    public static RadarEngine get() {
        return INSTANCE;
    }

    public void clearCache() {
        cache.clear();
    }

    public RadarScanResult scanGround(ServerLevel level, BlockPos controllerPos, double maxRangeBlocks) {
        if (level == null || controllerPos == null || !validRange(maxRangeBlocks)) {
            return RadarScanResult.unavailable("ground:invalid", level == null ? 0L : level.getGameTime(), maxRangeBlocks,
                    "invalid_request");
        }
        String key = "ground:" + level.dimension().location() + ":" + controllerPos.asLong() + ":" + Math.round(maxRangeBlocks);
        Vec3 origin = Vec3.atCenterOf(controllerPos).add(0.0, 0.5, 0.0);
        return scan(level, key, origin, maxRangeBlocks, null, controllerPos, true);
    }

    public RadarScanResult scanAircraft(ServerLevel level, UUID aircraftId, Vec3 antennaPosition, double maxRangeBlocks) {
        if (level == null || aircraftId == null || antennaPosition == null || !validRange(maxRangeBlocks)) {
            return RadarScanResult.unavailable("aircraft:invalid", level == null ? 0L : level.getGameTime(), maxRangeBlocks,
                    "invalid_request");
        }
        String key = "aircraft:" + level.dimension().location() + ":" + aircraftId + ":" + Math.round(maxRangeBlocks);
        return scan(level, key, antennaPosition, maxRangeBlocks, aircraftId, null, false);
    }

    public void invalidateGround(ServerLevel level, BlockPos controllerPos) {
        if (level == null || controllerPos == null) return;
        String prefix = "ground:" + level.dimension().location() + ":" + controllerPos.asLong() + ":";
        cache.keySet().removeIf(key -> key.startsWith(prefix));
    }

    private RadarScanResult scan(
            ServerLevel level,
            String sensorKey,
            Vec3 origin,
            double maxRangeBlocks,
            UUID excludedVehicle,
            BlockPos powerPosition,
            boolean requireCreatePower
    ) {
        long gameTime = level.getGameTime();
        CachedScan cached = cache.get(sensorKey);
        if (cached != null && gameTime >= cached.gameTime && gameTime - cached.gameTime <= CACHE_TICKS
                && cached.origin.distanceToSqr(origin) <= 16.0) {
            return cached.result;
        }

        if (requireCreatePower) {
            PowerSample power = DrewCraftServices.power().sample(level, powerPosition);
            if (!power.available()) {
                return store(sensorKey, origin, gameTime,
                        RadarScanResult.unavailable(sensorKey, gameTime, maxRangeBlocks, "create_power_unavailable:" + power.status()));
            }
            if (!power.kineticallyPowered().orElse(false)) {
                return store(sensorKey, origin, gameTime,
                        RadarScanResult.offline(sensorKey, gameTime, maxRangeBlocks, "no_active_create_kinetic_power"));
            }
        }

        VehicleQueryResult vehicles = DrewCraftServices.vehicles().query(level, origin, maxRangeBlocks);
        if (!vehicles.available()) {
            return store(sensorKey, origin, gameTime,
                    RadarScanResult.unavailable(sensorKey, gameTime, maxRangeBlocks, "vehicle_source_unavailable:" + vehicles.status()));
        }

        WeatherSample weather = DrewCraftServices.weather().sample(level, BlockPos.containing(origin));
        double weatherQuality = weatherQuality(weather);
        OptionalDouble antennaHeight = estimateAntennaHeightAgl(level, origin);
        List<RadarContact> contacts = new ArrayList<>();

        for (VehicleSnapshot target : vehicles.vehicles()) {
            if (target.id().equals(excludedVehicle)) continue;
            double range = origin.distanceTo(target.position());
            if (range > maxRangeBlocks || range < 1.0e-6) continue;

            TerrainVisibility visibility = terrainVisibility(level, origin, target.position());
            if (visibility == TerrainVisibility.BLOCKED) continue;

            double distanceFactor = 1.0 - 0.25 * Math.pow(range / maxRangeBlocks, 2.0);
            double terrainFactor = visibility == TerrainVisibility.UNKNOWN ? 0.80 : 1.0;
            double quality = RadarMath.clamp01(weatherQuality * distanceFactor * terrainFactor);
            contacts.add(new RadarContact(
                    target.id(),
                    target.typeId(),
                    target.position(),
                    range,
                    RadarMath.bearingDegrees(origin, target.position()),
                    target.position().y - origin.y,
                    RadarMath.radialVelocity(origin, target.position(), target.velocityBlocksPerTick()),
                    target.aircraft(),
                    visibility,
                    quality
            ));
        }
        contacts.sort(Comparator.comparingDouble(RadarContact::rangeBlocks));

        RadarScanResult result = new RadarScanResult(
                true,
                true,
                sensorKey,
                gameTime,
                maxRangeBlocks,
                antennaHeight,
                contacts,
                "radar_scan_ok"
        );
        if (cache.size() > 256) {
            cache.entrySet().removeIf(entry -> gameTime - entry.getValue().gameTime > 200);
        }
        return store(sensorKey, origin, gameTime, result);
    }

    private RadarScanResult store(String key, Vec3 origin, long gameTime, RadarScanResult result) {
        cache.put(key, new CachedScan(gameTime, origin, result));
        return result;
    }

    private TerrainVisibility terrainVisibility(ServerLevel level, Vec3 from, Vec3 to) {
        double horizontal = Math.hypot(to.x - from.x, to.z - from.z);
        int samples = Math.min(MAX_TERRAIN_SAMPLES, Math.max(1, (int) Math.ceil(horizontal / 64.0)));
        boolean unknown = false;
        for (int i = 1; i <= samples; i++) {
            double fraction = (double) i / (samples + 1.0);
            double x = from.x + (to.x - from.x) * fraction;
            double z = from.z + (to.z - from.z) * fraction;
            BlockPos samplePos = BlockPos.containing(x, from.y, z);
            TerrainSample terrain = DrewCraftServices.terrain().sample(level, samplePos);
            if (!terrain.available() || terrain.surfaceY().isEmpty()) {
                unknown = true;
                continue;
            }
            double rayY = RadarMath.lineAltitude(from, to, fraction);
            if (terrain.surfaceY().getAsInt() + TERRAIN_CLEARANCE_BLOCKS >= rayY) {
                return TerrainVisibility.BLOCKED;
            }
        }
        return unknown ? TerrainVisibility.UNKNOWN : TerrainVisibility.CLEAR;
    }

    private OptionalDouble estimateAntennaHeightAgl(ServerLevel level, Vec3 origin) {
        int[] offsets = {16, -16, 32, -32};
        List<Integer> surfaces = new ArrayList<>();
        for (int offset : offsets) {
            sampleSurface(level, BlockPos.containing(origin.x + offset, origin.y, origin.z), surfaces);
            sampleSurface(level, BlockPos.containing(origin.x, origin.y, origin.z + offset), surfaces);
        }
        if (surfaces.isEmpty()) {
            return OptionalDouble.empty();
        }
        surfaces.sort(Integer::compareTo);
        double median = surfaces.get(surfaces.size() / 2);
        return OptionalDouble.of(Math.max(0.0, origin.y - median));
    }

    private void sampleSurface(ServerLevel level, BlockPos pos, List<Integer> output) {
        TerrainSample sample = DrewCraftServices.terrain().sample(level, pos);
        if (sample.available() && sample.surfaceY().isPresent()) {
            output.add(sample.surfaceY().getAsInt());
        }
    }

    private static double weatherQuality(WeatherSample weather) {
        if (weather == null || !weather.available()) return 0.75;
        double rain = RadarMath.clamp01(weather.rainIntensity().orElse(0.0));
        double stormPenalty = weather.storming().orElse(false) ? 0.10 : 0.0;
        return RadarMath.clamp01(1.0 - rain * 0.20 - stormPenalty);
    }

    private static boolean validRange(double range) {
        return Double.isFinite(range) && range > 0.0;
    }

    private record CachedScan(long gameTime, Vec3 origin, RadarScanResult result) {
    }
}
