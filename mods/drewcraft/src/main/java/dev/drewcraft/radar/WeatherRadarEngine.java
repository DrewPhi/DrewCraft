package dev.drewcraft.radar;

import dev.drewcraft.service.DrewCraftServices;
import dev.drewcraft.service.terrain.TerrainSample;
import dev.drewcraft.service.weather.WeatherSample;
import java.util.Map;
import java.util.OptionalDouble;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.Vec3;

/** Server-authoritative cached Project Atmosphere weather image for physical ground radar. */
public final class WeatherRadarEngine {
    public static final int GRID_SIZE = 9;
    public static final int CACHE_TICKS = 20;
    private static final int MAX_TERRAIN_SAMPLES = 24;
    private static final double TERRAIN_CLEARANCE_BLOCKS = 2.0;
    private static final double WEATHER_ECHO_HEIGHT_BLOCKS = 64.0;
    private static final WeatherRadarEngine INSTANCE = new WeatherRadarEngine();

    private final Map<String, CachedProduct> cache = new ConcurrentHashMap<>();

    private WeatherRadarEngine() {
    }

    public static WeatherRadarEngine get() {
        return INSTANCE;
    }

    public void clearCache() {
        cache.clear();
    }

    public WeatherRadarProduct scanGround(ServerLevel level, BlockPos radarPosition, double rangeBlocks) {
        if (level == null || radarPosition == null || !Double.isFinite(rangeBlocks) || rangeBlocks <= 0.0) {
            return WeatherRadarProduct.unavailable(level == null ? 0L : level.getGameTime(), radarPosition, rangeBlocks, "invalid_request");
        }

        long gameTime = level.getGameTime();
        String key = level.dimension().location() + ":" + radarPosition.asLong() + ":" + Math.round(rangeBlocks);
        CachedProduct cached = cache.get(key);
        if (cached != null && gameTime >= cached.gameTime && gameTime - cached.gameTime <= CACHE_TICKS) {
            return cached.product;
        }

        Vec3 origin = Vec3.atCenterOf(radarPosition).add(0.0, 1.0, 0.0);
        WeatherSample station = DrewCraftServices.weather().sample(level, radarPosition);
        byte[] intensity = new byte[GRID_SIZE * GRID_SIZE];
        byte[] visibility = new byte[GRID_SIZE * GRID_SIZE];
        int inside = 0;
        int sampled = 0;
        int blocked = 0;

        for (int z = 0; z < GRID_SIZE; z++) {
            double nz = normalized(z);
            for (int x = 0; x < GRID_SIZE; x++) {
                double nx = normalized(x);
                int index = z * GRID_SIZE + x;
                if (nx * nx + nz * nz > 1.0) {
                    visibility[index] = WeatherRadarProduct.VIS_OUTSIDE;
                    continue;
                }
                inside++;

                double worldX = origin.x + nx * rangeBlocks;
                double worldZ = origin.z + nz * rangeBlocks;
                BlockPos weatherPos = BlockPos.containing(worldX, origin.y, worldZ);
                WeatherSample weather = DrewCraftServices.weather().sample(level, weatherPos);
                if (weather == null || !weather.available()) {
                    visibility[index] = WeatherRadarProduct.VIS_UNAVAILABLE;
                    continue;
                }
                sampled++;

                Vec3 echo = new Vec3(worldX, origin.y + WEATHER_ECHO_HEIGHT_BLOCKS, worldZ);
                TerrainVisibility terrain = terrainVisibility(level, origin, echo);
                if (terrain == TerrainVisibility.BLOCKED) {
                    visibility[index] = WeatherRadarProduct.VIS_BLOCKED;
                    blocked++;
                    continue;
                }

                visibility[index] = terrain == TerrainVisibility.UNKNOWN
                        ? WeatherRadarProduct.VIS_UNKNOWN
                        : WeatherRadarProduct.VIS_CLEAR;
                intensity[index] = (byte) quantizeSignal(
                        weather.rainIntensity().orElse(0.0),
                        weather.storming().orElse(false)
                );
            }
        }

        WeatherRadarProduct product = new WeatherRadarProduct(
                sampled > 0,
                gameTime,
                radarPosition.immutable(),
                rangeBlocks,
                GRID_SIZE,
                intensity,
                visibility,
                station != null && station.available() ? station.windSpeedMps() : OptionalDouble.empty(),
                station != null && station.available() ? station.windAngleRad() : OptionalDouble.empty(),
                station != null && station.available() ? station.temperatureC() : OptionalDouble.empty(),
                "weather_cells=" + sampled + "/" + inside + ";terrain_blocked=" + blocked
        );

        cache.put(key, new CachedProduct(gameTime, product));
        if (cache.size() > 128) {
            cache.entrySet().removeIf(entry -> gameTime - entry.getValue().gameTime > 400);
        }
        return product;
    }

    static int quantizeSignal(double rainIntensity, boolean storming) {
        double signal = RadarMath.clamp01(rainIntensity);
        if (storming) {
            signal = Math.max(signal, 0.65);
        }
        return (int) Math.round(signal * 255.0);
    }

    private static double normalized(int index) {
        return ((double) index / (GRID_SIZE - 1)) * 2.0 - 1.0;
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

    private record CachedProduct(long gameTime, WeatherRadarProduct product) {
    }
}
