package dev.drewcraft.service.weather;

import java.util.Objects;
import java.util.Optional;
import java.util.OptionalDouble;
import net.minecraft.core.BlockPos;

public record WeatherSample(
        boolean available,
        String providerId,
        BlockPos requestedPosition,
        OptionalDouble cloudCover,
        OptionalDouble rainIntensity,
        OptionalDouble temperatureC,
        OptionalDouble windSpeedMps,
        OptionalDouble windAngleRad,
        OptionalDouble pressureHpa,
        OptionalDouble humidityRelative,
        OptionalDouble visibilityMeters,
        OptionalDouble severity01,
        Optional<Boolean> storming,
        Optional<Boolean> snowing,
        String status
) {
    public WeatherSample {
        Objects.requireNonNull(providerId);
        Objects.requireNonNull(requestedPosition);
        Objects.requireNonNull(cloudCover);
        Objects.requireNonNull(rainIntensity);
        Objects.requireNonNull(temperatureC);
        Objects.requireNonNull(windSpeedMps);
        Objects.requireNonNull(windAngleRad);
        Objects.requireNonNull(pressureHpa);
        Objects.requireNonNull(humidityRelative);
        Objects.requireNonNull(visibilityMeters);
        Objects.requireNonNull(severity01);
        Objects.requireNonNull(storming);
        Objects.requireNonNull(snowing);
        Objects.requireNonNull(status);
    }

    public static WeatherSample unavailable(String providerId, BlockPos position, String status) {
        return new WeatherSample(
                false,
                providerId,
                position.immutable(),
                OptionalDouble.empty(),
                OptionalDouble.empty(),
                OptionalDouble.empty(),
                OptionalDouble.empty(),
                OptionalDouble.empty(),
                OptionalDouble.empty(),
                OptionalDouble.empty(),
                OptionalDouble.empty(),
                OptionalDouble.empty(),
                Optional.empty(),
                Optional.empty(),
                status
        );
    }

    public static WeatherSample available(
            String providerId,
            BlockPos position,
            double cloudCover,
            double rainIntensity,
            double temperatureC,
            double windSpeedMps,
            double windAngleRad,
            boolean storming,
            boolean snowing,
            String status
    ) {
        return new WeatherSample(
                true,
                providerId,
                position.immutable(),
                OptionalDouble.of(cloudCover),
                OptionalDouble.of(rainIntensity),
                OptionalDouble.of(temperatureC),
                OptionalDouble.of(windSpeedMps),
                OptionalDouble.of(windAngleRad),
                OptionalDouble.empty(),
                OptionalDouble.empty(),
                OptionalDouble.empty(),
                OptionalDouble.empty(),
                Optional.of(storming),
                Optional.of(snowing),
                status
        );
    }
}
