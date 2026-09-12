package dev.drewcraft.adapter.atmosphere;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.service.weather.WeatherSample;
import net.minecraft.core.BlockPos;
import org.junit.jupiter.api.Test;

class AtmosphereSnapshotDecoderTest {
    @Test
    void decodesPublicWeatherSnapshotShapeWithoutInventingMissingFields() {
        FakeSnapshot snapshot = new FakeSnapshot(0.7f, 0.4f, 12.5f, 8.0f, 1.25f, true, false);
        WeatherSample decoded = AtmosphereSnapshotDecoder.decode(snapshot, new BlockPos(10, 80, -20));

        assertTrue(decoded.available());
        assertEquals(0.7, decoded.cloudCover().orElseThrow(), 1e-6);
        assertEquals(0.4, decoded.rainIntensity().orElseThrow(), 1e-6);
        assertEquals(12.5, decoded.temperatureC().orElseThrow(), 1e-6);
        assertEquals(8.0, decoded.windSpeedMps().orElseThrow(), 1e-6);
        assertEquals(1.25, decoded.windAngleRad().orElseThrow(), 1e-6);
        assertTrue(decoded.storming().orElseThrow());
        assertFalse(decoded.snowing().orElseThrow());
        assertTrue(decoded.pressureHpa().isEmpty());
        assertTrue(decoded.humidityRelative().isEmpty());
        assertTrue(decoded.visibilityMeters().isEmpty());
        assertTrue(decoded.severity01().isEmpty());
    }

    @Test
    void failsClosedWhenSnapshotShapeChanges() {
        WeatherSample decoded = AtmosphereSnapshotDecoder.decode(new BrokenSnapshot(1.0f), BlockPos.ZERO);
        assertFalse(decoded.available());
        assertTrue(decoded.status().startsWith("snapshot_api_mismatch:"));
    }

    private record FakeSnapshot(
            float cloudCover,
            float rainIntensity,
            float temperatureC,
            float windSpeedMps,
            float windAngleRad,
            boolean isStorming,
            boolean isSnowing
    ) {
    }

    private record BrokenSnapshot(float cloudCover) {
    }
}
