package dev.drewcraft.aviation;

import dev.drewcraft.service.terrain.TerrainSample;
import dev.drewcraft.service.weather.WeatherSample;
import java.util.OptionalDouble;
import java.util.UUID;
import net.minecraft.world.phys.Vec3;

/** Pure, bounded conversion from DrewCraft weather/terrain truth to aircraft airflow. */
public final class AviationWindModel {
    public static final double MAX_TURBULENCE_MPS = 6.0;

    private AviationWindModel() {
    }

    public static AviationAirflowSample calculate(
            WeatherSample weather,
            TerrainSample terrain,
            UUID vehicleId,
            Vec3 vehiclePosition,
            long gameTime
    ) {
        if (weather == null || !weather.available()
                || weather.windSpeedMps().isEmpty() || weather.windAngleRad().isEmpty()) {
            return AviationAirflowSample.unavailable("weather_wind_unavailable");
        }

        double windSpeed = Math.max(0.0, weather.windSpeedMps().getAsDouble());
        double angle = weather.windAngleRad().getAsDouble();
        // Project Atmosphere convention: angle zero blows toward +Z.
        Vec3 steady = new Vec3(-Math.sin(angle) * windSpeed, 0.0, Math.cos(angle) * windSpeed);

        OptionalDouble agl = OptionalDouble.empty();
        double groundFactor = 0.0;
        if (terrain != null && terrain.available() && terrain.surfaceY().isPresent()) {
            double height = Math.max(0.0, vehiclePosition.y - terrain.surfaceY().getAsInt());
            agl = OptionalDouble.of(height);
            groundFactor = clamp01((96.0 - height) / 96.0);
        }

        double rain = weather.rainIntensity().orElse(0.0);
        double storm = weather.storming().orElse(false) ? 1.0 : 0.0;
        double weatherFactor = clamp01(storm * 0.65 + clamp01(rain) * 0.25 + clamp01(windSpeed / 30.0) * 0.10);
        double mechanicalFactor = groundFactor * clamp01(windSpeed / 12.0);
        double amplitude = Math.min(MAX_TURBULENCE_MPS,
                windSpeed * 0.06 + weatherFactor * 3.75 + mechanicalFactor * 1.5);

        long idBits = vehicleId == null ? 0L : vehicleId.getMostSignificantBits() ^ vehicleId.getLeastSignificantBits();
        double seed = ((idBits >>> 11) & 0xFFFF) / 65535.0 * Math.PI * 2.0;
        double phase = gameTime * 0.035 + seed;
        Vec3 raw = new Vec3(
                Math.sin(phase * 1.73 + 0.31) * amplitude * 0.62,
                Math.sin(phase * 2.29 + 1.17) * amplitude * 0.34,
                Math.cos(phase * 1.37 + 2.03) * amplitude * 0.62
        );
        Vec3 turbulence = raw.length() > amplitude && raw.length() > 0.0
                ? raw.scale(amplitude / raw.length())
                : raw;

        return new AviationAirflowSample(
                true,
                steady,
                turbulence,
                steady.add(turbulence),
                agl,
                amplitude,
                "project_atmosphere_airflow"
        );
    }

    /** Converts real m/s to the internal MTS motion units used by its configured speed factor. */
    public static Vec3 toMtsMotion(Vec3 airVelocityMps, double mtsSpeedFactor) {
        if (airVelocityMps == null || !Double.isFinite(mtsSpeedFactor) || mtsSpeedFactor <= 0.0) {
            return Vec3.ZERO;
        }
        return airVelocityMps.scale(1.0 / (mtsSpeedFactor * 20.0));
    }

    private static double clamp01(double value) {
        return Math.max(0.0, Math.min(1.0, value));
    }
}
