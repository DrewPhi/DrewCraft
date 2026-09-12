package dev.drewcraft.strategic.routing;

import static org.junit.jupiter.api.Assertions.assertEquals;

import dev.drewcraft.service.terrain.TerrainSample;
import java.util.List;
import net.minecraft.core.BlockPos;
import org.junit.jupiter.api.Test;

class StrategicTerrainCaptureTest {
    @Test
    void classifiesWaterFromRealizedSurfaceMetadata() {
        TerrainSample water = TerrainSample.available("test", BlockPos.ZERO, 63,
                "minecraft:river", "minecraft:water", 63, "ok");
        assertEquals(StrategicTerrainClass.WATER, StrategicTerrainCapture.classify(List.of(water)));
    }

    @Test
    void classifiesLargeElevationSpreadAsDifficult() {
        TerrainSample low = TerrainSample.available("test", BlockPos.ZERO, 64,
                "minecraft:plains", "minecraft:grass_block", 63, "ok");
        TerrainSample high = TerrainSample.available("test", BlockPos.ZERO, 100,
                "minecraft:stony_peaks", "minecraft:stone", 63, "ok");
        assertEquals(StrategicTerrainClass.DIFFICULT, StrategicTerrainCapture.classify(List.of(low, high)));
    }

    @Test
    void classifiesOrdinaryLandAsNormal() {
        TerrainSample a = TerrainSample.available("test", BlockPos.ZERO, 70,
                "minecraft:plains", "minecraft:grass_block", 63, "ok");
        TerrainSample b = TerrainSample.available("test", BlockPos.ZERO, 74,
                "minecraft:plains", "minecraft:dirt", 63, "ok");
        assertEquals(StrategicTerrainClass.NORMAL, StrategicTerrainCapture.classify(List.of(a, b)));
    }
}
