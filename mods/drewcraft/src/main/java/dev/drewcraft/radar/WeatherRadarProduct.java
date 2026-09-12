package dev.drewcraft.radar;

import java.util.Arrays;
import java.util.Objects;
import java.util.OptionalDouble;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;

/** Compact server-authored weather image synced through an existing radar monitor update. */
public record WeatherRadarProduct(
        boolean available,
        long gameTime,
        BlockPos radarPosition,
        double rangeBlocks,
        int gridSize,
        byte[] intensity255,
        byte[] visibility,
        OptionalDouble windSpeedMps,
        OptionalDouble windAngleRad,
        OptionalDouble temperatureC,
        String status
) {
    public static final int SCHEMA_VERSION = 1;
    public static final byte VIS_OUTSIDE = 0;
    public static final byte VIS_CLEAR = 1;
    public static final byte VIS_UNKNOWN = 2;
    public static final byte VIS_BLOCKED = 3;
    public static final byte VIS_UNAVAILABLE = 4;

    public WeatherRadarProduct {
        Objects.requireNonNull(radarPosition);
        Objects.requireNonNull(intensity255);
        Objects.requireNonNull(visibility);
        Objects.requireNonNull(windSpeedMps);
        Objects.requireNonNull(windAngleRad);
        Objects.requireNonNull(temperatureC);
        Objects.requireNonNull(status);
        if (gridSize < 1 || intensity255.length != gridSize * gridSize || visibility.length != gridSize * gridSize) {
            throw new IllegalArgumentException("weather radar grid shape mismatch");
        }
        intensity255 = intensity255.clone();
        visibility = visibility.clone();
    }

    @Override
    public byte[] intensity255() {
        return intensity255.clone();
    }

    @Override
    public byte[] visibility() {
        return visibility.clone();
    }

    public int intensityUnsigned(int x, int z) {
        return Byte.toUnsignedInt(intensity255[index(x, z)]);
    }

    public byte visibilityAt(int x, int z) {
        return visibility[index(x, z)];
    }

    private int index(int x, int z) {
        if (x < 0 || z < 0 || x >= gridSize || z >= gridSize) {
            throw new IndexOutOfBoundsException("weather radar cell outside grid");
        }
        return z * gridSize + x;
    }

    public CompoundTag toTag() {
        CompoundTag tag = new CompoundTag();
        tag.putInt("schema", SCHEMA_VERSION);
        tag.putBoolean("available", available);
        tag.putLong("gameTime", gameTime);
        tag.putLong("radarPos", radarPosition.asLong());
        tag.putDouble("range", rangeBlocks);
        tag.putInt("grid", gridSize);
        tag.putByteArray("intensity", intensity255);
        tag.putByteArray("visibility", visibility);
        putOptional(tag, "windSpeed", windSpeedMps);
        putOptional(tag, "windAngle", windAngleRad);
        putOptional(tag, "temperature", temperatureC);
        tag.putString("status", status);
        return tag;
    }

    public static WeatherRadarProduct fromTag(CompoundTag tag) {
        int schema = tag.getInt("schema");
        int grid = tag.getInt("grid");
        byte[] intensity = tag.getByteArray("intensity");
        byte[] visibility = tag.getByteArray("visibility");
        if (schema != SCHEMA_VERSION || grid < 1 || intensity.length != grid * grid || visibility.length != grid * grid) {
            return unavailable(0L, BlockPos.ZERO, 0.0, "invalid_weather_radar_payload");
        }
        return new WeatherRadarProduct(
                tag.getBoolean("available"),
                tag.getLong("gameTime"),
                BlockPos.of(tag.getLong("radarPos")),
                tag.getDouble("range"),
                grid,
                intensity,
                visibility,
                getOptional(tag, "windSpeed"),
                getOptional(tag, "windAngle"),
                getOptional(tag, "temperature"),
                tag.getString("status")
        );
    }

    public static WeatherRadarProduct unavailable(long gameTime, BlockPos position, double range, String status) {
        return new WeatherRadarProduct(
                false,
                gameTime,
                position == null ? BlockPos.ZERO : position.immutable(),
                Math.max(0.0, range),
                1,
                new byte[]{0},
                new byte[]{VIS_UNAVAILABLE},
                OptionalDouble.empty(),
                OptionalDouble.empty(),
                OptionalDouble.empty(),
                status
        );
    }

    private static void putOptional(CompoundTag tag, String key, OptionalDouble value) {
        if (value.isPresent() && Double.isFinite(value.getAsDouble())) {
            tag.putDouble(key, value.getAsDouble());
        }
    }

    private static OptionalDouble getOptional(CompoundTag tag, String key) {
        return tag.contains(key, Tag.TAG_DOUBLE) ? OptionalDouble.of(tag.getDouble(key)) : OptionalDouble.empty();
    }

    @Override
    public String toString() {
        return "WeatherRadarProduct[available=" + available + ", gameTime=" + gameTime + ", radarPosition=" + radarPosition
                + ", rangeBlocks=" + rangeBlocks + ", gridSize=" + gridSize + ", intensity255=" + Arrays.toString(intensity255)
                + ", visibility=" + Arrays.toString(visibility) + ", status=" + status + "]";
    }
}
