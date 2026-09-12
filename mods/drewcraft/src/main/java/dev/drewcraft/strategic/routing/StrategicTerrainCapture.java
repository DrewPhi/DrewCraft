package dev.drewcraft.strategic.routing;

import dev.drewcraft.service.DrewCraftServices;
import dev.drewcraft.service.terrain.TerrainSample;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;

/**
 * Optional producer for the coarse cost cache. It only asks DrewCraft's terrain service for
 * samples; the selected Terrain Diffusion adapter returns unavailable for unloaded chunks rather
 * than loading/generating them. Strategic route search never invokes this class automatically.
 */
public final class StrategicTerrainCapture {
    private StrategicTerrainCapture() {
    }

    public static CaptureResult captureLoadedCell(
            ServerLevel level,
            StrategicCell cell,
            StrategicTerrainCostMap costs
    ) {
        String levelDimension = level.dimension().location().toString();
        if (!levelDimension.equals(cell.dimension())) {
            return new CaptureResult(false, StrategicTerrainClass.UNKNOWN, "dimension_mismatch");
        }
        int size = costs.cellSizeBlocks();
        int centerX = cell.x() * size + size / 2;
        int centerZ = cell.z() * size + size / 2;
        int offset = Math.max(4, size / 4);
        int[][] points = {
                {centerX, centerZ},
                {centerX + offset, centerZ},
                {centerX - offset, centerZ},
                {centerX, centerZ + offset},
                {centerX, centerZ - offset}
        };

        List<TerrainSample> available = new ArrayList<>();
        for (int[] point : points) {
            TerrainSample sample = DrewCraftServices.terrain().sample(level, new BlockPos(point[0], 0, point[1]));
            if (sample.available()) available.add(sample);
        }
        if (available.isEmpty()) {
            return new CaptureResult(false, StrategicTerrainClass.UNKNOWN, "no_loaded_samples");
        }

        StrategicTerrainClass terrainClass = classify(available);
        costs.put(cell, terrainClass);
        return new CaptureResult(true, terrainClass, "captured_" + available.size() + "_samples");
    }

    static StrategicTerrainClass classify(List<TerrainSample> samples) {
        TerrainSample center = samples.getFirst();
        String block = center.surfaceBlockId().orElse("").toLowerCase(Locale.ROOT);
        String biome = center.biomeId().orElse("").toLowerCase(Locale.ROOT);
        if (block.contains("water") || biome.contains("ocean") || biome.contains("river")) {
            return StrategicTerrainClass.WATER;
        }

        int minY = Integer.MAX_VALUE;
        int maxY = Integer.MIN_VALUE;
        for (TerrainSample sample : samples) {
            if (sample.surfaceY().isPresent()) {
                int y = sample.surfaceY().getAsInt();
                minY = Math.min(minY, y);
                maxY = Math.max(maxY, y);
            }
        }
        if (minY != Integer.MAX_VALUE && maxY - minY >= 24) {
            return StrategicTerrainClass.DIFFICULT;
        }
        return StrategicTerrainClass.NORMAL;
    }

    public record CaptureResult(boolean captured, StrategicTerrainClass terrainClass, String status) {
    }
}
