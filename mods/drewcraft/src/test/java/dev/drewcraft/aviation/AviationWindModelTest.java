package dev.drewcraft.aviation;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.service.terrain.TerrainSample;
import dev.drewcraft.service.weather.WeatherSample;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

final class AviationWindModelTest {
    @Test
    void projectAtmosphereAngleZeroBlowsTowardPositiveZ() {
        WeatherSample weather = WeatherSample.available(
                "projectatmosphere", BlockPos.ZERO,
                0.2, 0.0, 20.0, 10.0, 0.0, false, false, "test");
        TerrainSample terrain = TerrainSample.available(
                "terrain", BlockPos.ZERO, 64, "minecraft:plains", "minecraft:grass_block", 63, "test");

        AviationAirflowSample sample = AviationWindModel.calculate(
                weather, terrain, new UUID(0, 0), new Vec3(0, 200, 0), 0L);

        assertTrue(sample.available());
        assertEquals(0.0, sample.steadyWindMps().x, 1.0e-6);
        assertEquals(10.0, sample.steadyWindMps().z, 1.0e-6);
    }

    @Test
    void turbulenceIsBoundedAndTerrainAware() {
        WeatherSample weather = WeatherSample.available(
                "projectatmosphere", BlockPos.ZERO,
                1.0, 1.0, 10.0, 45.0, Math.PI / 2.0, true, false, "test");
        TerrainSample terrain = TerrainSample.available(
                "terrain", BlockPos.ZERO, 70, "minecraft:plains", "minecraft:grass_block", 63, "test");

        AviationAirflowSample sample = AviationWindModel.calculate(
                weather, terrain, new UUID(123, 456), new Vec3(0, 76, 0), 1000L);

        assertTrue(sample.turbulenceMps().length() <= AviationWindModel.MAX_TURBULENCE_MPS + 1.0e-9);
        assertEquals(6.0, sample.aboveGroundLevelBlocks().orElseThrow(), 1.0e-6);
        assertTrue(sample.turbulenceAmplitudeMps() <= AviationWindModel.MAX_TURBULENCE_MPS);
    }

    @Test
    void convertsMetersPerSecondToMtsInternalMotion() {
        Vec3 internal = AviationWindModel.toMtsMotion(new Vec3(20, 0, -10), 2.0);
        assertEquals(0.5, internal.x, 1.0e-9);
        assertEquals(-0.25, internal.z, 1.0e-9);
    }
}
