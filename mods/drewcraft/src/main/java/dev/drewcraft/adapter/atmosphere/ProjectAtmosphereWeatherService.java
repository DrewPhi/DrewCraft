package dev.drewcraft.adapter.atmosphere;

import dev.drewcraft.DrewCraft;
import dev.drewcraft.service.weather.WeatherSample;
import dev.drewcraft.service.weather.WeatherService;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;

/** Read-only adapter over Project Atmosphere's public AtmoApi. */
public final class ProjectAtmosphereWeatherService implements WeatherService {
    public static final String PROVIDER_ID = "project_atmosphere.public_api";
    private static final String API_CLASS = "net.Gabou.projectatmosphere.api.AtmoApi";

    private final Object apiInstance;
    private final Method getCurrentWeather;
    private final String bindFailure;

    public ProjectAtmosphereWeatherService() {
        Object instance = null;
        Method weatherMethod = null;
        String failure = null;
        try {
            Class<?> apiClass = Class.forName(API_CLASS);
            Method getInstance = apiClass.getMethod("getInstance");
            instance = getInstance.invoke(null);
            weatherMethod = apiClass.getMethod("getCurrentWeather", ServerLevel.class, BlockPos.class);
        } catch (ReflectiveOperationException | LinkageError exception) {
            failure = rootMessage(exception);
            DrewCraft.LOGGER.warn("Project Atmosphere public API binding failed: {}", failure);
        }
        this.apiInstance = instance;
        this.getCurrentWeather = weatherMethod;
        this.bindFailure = failure;
    }

    @Override
    public String providerId() {
        return PROVIDER_ID;
    }

    @Override
    public WeatherSample sample(ServerLevel level, BlockPos position) {
        if (level == null || position == null) {
            return WeatherSample.unavailable(PROVIDER_ID, BlockPos.ZERO, "invalid_request");
        }
        if (bindFailure != null || apiInstance == null || getCurrentWeather == null) {
            return WeatherSample.unavailable(PROVIDER_ID, position, "api_bind_failed:" + bindFailure);
        }

        try {
            Object snapshot = getCurrentWeather.invoke(apiInstance, level, position);
            return AtmosphereSnapshotDecoder.decode(snapshot, position);
        } catch (IllegalAccessException | InvocationTargetException | RuntimeException exception) {
            return WeatherSample.unavailable(
                    PROVIDER_ID,
                    position,
                    "weather_query_failed:" + rootMessage(exception)
            );
        }
    }

    private static String rootMessage(Throwable throwable) {
        Throwable current = throwable;
        while (current.getCause() != null) {
            current = current.getCause();
        }
        String message = current.getMessage();
        return current.getClass().getSimpleName() + (message == null ? "" : ":" + message);
    }
}
