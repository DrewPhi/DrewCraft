package dev.drewcraft.radar;

import java.util.List;
import java.util.Objects;
import java.util.OptionalDouble;

public record RadarScanResult(
        boolean available,
        boolean operational,
        String sensorKey,
        long scanGameTime,
        double maxRangeBlocks,
        OptionalDouble antennaHeightAglBlocks,
        List<RadarContact> contacts,
        String status
) {
    public RadarScanResult {
        Objects.requireNonNull(sensorKey);
        Objects.requireNonNull(antennaHeightAglBlocks);
        contacts = List.copyOf(contacts);
        Objects.requireNonNull(status);
    }

    public static RadarScanResult unavailable(String sensorKey, long gameTime, double maxRange, String status) {
        return new RadarScanResult(false, false, sensorKey, gameTime, maxRange,
                OptionalDouble.empty(), List.of(), status);
    }

    public static RadarScanResult offline(String sensorKey, long gameTime, double maxRange, String status) {
        return new RadarScanResult(true, false, sensorKey, gameTime, maxRange,
                OptionalDouble.empty(), List.of(), status);
    }
}
