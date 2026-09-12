package dev.drewcraft.radar;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.OptionalDouble;
import net.minecraft.core.BlockPos;
import org.junit.jupiter.api.Test;

class WeatherRadarProductTest {
    @Test
    void payloadRoundTripsWithoutChangingGridOrReadouts() {
        byte[] intensity = {0, 64, (byte) 255, 12};
        byte[] visibility = {
                WeatherRadarProduct.VIS_CLEAR,
                WeatherRadarProduct.VIS_UNKNOWN,
                WeatherRadarProduct.VIS_BLOCKED,
                WeatherRadarProduct.VIS_OUTSIDE
        };
        WeatherRadarProduct product = new WeatherRadarProduct(
                true,
                1234L,
                new BlockPos(10, 90, -20),
                600.0,
                2,
                intensity,
                visibility,
                OptionalDouble.of(12.5),
                OptionalDouble.of(Math.PI),
                OptionalDouble.of(18.25),
                "ok"
        );

        WeatherRadarProduct decoded = WeatherRadarProduct.fromTag(product.toTag());
        assertTrue(decoded.available());
        assertEquals(product.gameTime(), decoded.gameTime());
        assertEquals(product.radarPosition(), decoded.radarPosition());
        assertEquals(product.rangeBlocks(), decoded.rangeBlocks());
        assertEquals(product.gridSize(), decoded.gridSize());
        assertArrayEquals(product.intensity255(), decoded.intensity255());
        assertArrayEquals(product.visibility(), decoded.visibility());
        assertEquals(12.5, decoded.windSpeedMps().orElseThrow());
        assertEquals(Math.PI, decoded.windAngleRad().orElseThrow());
        assertEquals(18.25, decoded.temperatureC().orElseThrow());
    }

    @Test
    void stormSignalHasAVisibleMinimumAndRainClamps() {
        assertEquals(0, WeatherRadarEngine.quantizeSignal(-1.0, false));
        assertEquals(255, WeatherRadarEngine.quantizeSignal(5.0, false));
        assertTrue(WeatherRadarEngine.quantizeSignal(0.0, true) >= 165);
    }

    @Test
    void invalidPayloadFailsClosed() {
        WeatherRadarProduct decoded = WeatherRadarProduct.fromTag(new net.minecraft.nbt.CompoundTag());
        assertFalse(decoded.available());
        assertEquals("invalid_weather_radar_payload", decoded.status());
    }
}
