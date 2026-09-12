package dev.drewcraft.adapter.atmosphere;

import dev.drewcraft.service.weather.WeatherSample;
import java.lang.reflect.Method;
import net.minecraft.core.BlockPos;

/**
 * Converts Project Atmosphere's public WeatherSnapshot record into the DrewCraft contract.
 * Reflection keeps the moving upstream source branch out of DrewCraft's compile-time API surface;
 * the exact selected runtime JAR remains the release contract.
 */
final class AtmosphereSnapshotDecoder {
    private static final ClassValue<Accessors> ACCESSORS = new ClassValue<>() {
        @Override
        protected Accessors computeValue(Class<?> type) {
            try {
                return new Accessors(
                        type.getMethod("cloudCover"),
                        type.getMethod("rainIntensity"),
                        type.getMethod("temperatureC"),
                        type.getMethod("windSpeedMps"),
                        type.getMethod("windAngleRad"),
                        type.getMethod("isStorming"),
                        type.getMethod("isSnowing")
                );
            } catch (ReflectiveOperationException exception) {
                throw new IllegalStateException("Project Atmosphere WeatherSnapshot API mismatch", exception);
            }
        }
    };

    private AtmosphereSnapshotDecoder() {
    }

    static WeatherSample decode(Object snapshot, BlockPos position) {
        if (snapshot == null) {
            return WeatherSample.unavailable(
                    ProjectAtmosphereWeatherService.PROVIDER_ID,
                    position,
                    "project_atmosphere_returned_null_snapshot"
            );
        }

        try {
            Accessors accessors = ACCESSORS.get(snapshot.getClass());
            return WeatherSample.available(
                    ProjectAtmosphereWeatherService.PROVIDER_ID,
                    position,
                    number(accessors.cloudCover().invoke(snapshot)),
                    number(accessors.rainIntensity().invoke(snapshot)),
                    number(accessors.temperatureC().invoke(snapshot)),
                    number(accessors.windSpeedMps().invoke(snapshot)),
                    number(accessors.windAngleRad().invoke(snapshot)),
                    bool(accessors.isStorming().invoke(snapshot)),
                    bool(accessors.isSnowing().invoke(snapshot)),
                    "public_snapshot_ok; pressure_hpa=unavailable; humidity=unavailable"
            );
        } catch (ReflectiveOperationException | RuntimeException exception) {
            return WeatherSample.unavailable(
                    ProjectAtmosphereWeatherService.PROVIDER_ID,
                    position,
                    "snapshot_api_mismatch:" + rootMessage(exception)
            );
        }
    }

    private static double number(Object value) {
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        throw new IllegalStateException("expected numeric snapshot accessor");
    }

    private static boolean bool(Object value) {
        if (value instanceof Boolean bool) {
            return bool;
        }
        throw new IllegalStateException("expected boolean snapshot accessor");
    }

    private static String rootMessage(Throwable throwable) {
        Throwable current = throwable;
        while (current.getCause() != null) {
            current = current.getCause();
        }
        String message = current.getMessage();
        return current.getClass().getSimpleName() + (message == null ? "" : ":" + message);
    }

    private record Accessors(
            Method cloudCover,
            Method rainIntensity,
            Method temperatureC,
            Method windSpeedMps,
            Method windAngleRad,
            Method isStorming,
            Method isSnowing
    ) {
    }
}
