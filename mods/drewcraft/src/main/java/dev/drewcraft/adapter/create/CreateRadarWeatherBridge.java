package dev.drewcraft.adapter.create;

import dev.drewcraft.DrewCraft;
import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.radar.WeatherRadarEngine;
import dev.drewcraft.radar.WeatherRadarProduct;
import java.lang.reflect.Method;
import java.util.Collections;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.WeakHashMap;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;

/**
 * Isolated compatibility boundary for the official Create: Radars monitor/radar classes.
 * No protected upstream code or assets are copied and DrewCraft has no compile-time dependency on the mod.
 */
public final class CreateRadarWeatherBridge {
    public static final String PAYLOAD_KEY = "DrewCraftWeatherRadarV1";
    private static final Map<Object, WeatherRadarProduct> CLIENT_PRODUCTS = Collections.synchronizedMap(new WeakHashMap<>());
    private static final Set<Class<?>> REPORTED_FAILURES = ConcurrentHashMap.newKeySet();

    private static final ClassValue<MonitorBindings> MONITOR_BINDINGS = new ClassValue<>() {
        @Override
        protected MonitorBindings computeValue(Class<?> type) {
            try {
                return new MonitorBindings(
                        type.getMethod("isController"),
                        type.getMethod("getRadar"),
                        type.getMethod("getSize")
                );
            } catch (ReflectiveOperationException exception) {
                throw new IllegalStateException("Create: Radars monitor API mismatch", exception);
            }
        }
    };

    private static final ClassValue<RadarBindings> RADAR_BINDINGS = new ClassValue<>() {
        @Override
        protected RadarBindings computeValue(Class<?> type) {
            try {
                return new RadarBindings(
                        type.getMethod("isRunning"),
                        type.getMethod("getRange"),
                        type.getMethod("getWorldPos"),
                        type.getMethod("getRadarType")
                );
            } catch (ReflectiveOperationException exception) {
                throw new IllegalStateException("Create: Radars radar API mismatch", exception);
            }
        }
    };

    private CreateRadarWeatherBridge() {
    }

    public static void writeServerPayload(Object monitor, CompoundTag tag, boolean clientPacket) {
        if (!clientPacket || !enabled()) {
            tag.remove(PAYLOAD_KEY);
            return;
        }
        if (!(monitor instanceof BlockEntity blockEntity) || !(blockEntity.getLevel() instanceof ServerLevel level)) {
            return;
        }

        try {
            MonitorBindings monitorBindings = MONITOR_BINDINGS.get(monitor.getClass());
            if (!(Boolean) monitorBindings.isController.invoke(monitor)) {
                tag.remove(PAYLOAD_KEY);
                return;
            }

            Object rawOptional = monitorBindings.getRadar.invoke(monitor);
            if (!(rawOptional instanceof Optional<?> optional) || optional.isEmpty()) {
                tag.remove(PAYLOAD_KEY);
                return;
            }

            Object radar = optional.get();
            RadarBindings radarBindings = RADAR_BINDINGS.get(radar.getClass());
            String radarType = String.valueOf(radarBindings.getRadarType.invoke(radar));
            // V1 deliberately integrates ground spinning radar only. Create/Sable plane radar and MTS cockpit radar are post-V1.
            if (!"spinning".equals(radarType)) {
                tag.remove(PAYLOAD_KEY);
                return;
            }

            BlockPos radarPosition = (BlockPos) radarBindings.getWorldPos.invoke(radar);
            double range = ((Number) radarBindings.getRange.invoke(radar)).doubleValue();
            boolean running = (Boolean) radarBindings.isRunning.invoke(radar);
            WeatherRadarProduct product = running
                    ? WeatherRadarEngine.get().scanGround(level, radarPosition, range)
                    : WeatherRadarProduct.unavailable(level.getGameTime(), radarPosition, range, "create_radar_offline");
            tag.put(PAYLOAD_KEY, product.toTag());
        } catch (ReflectiveOperationException | RuntimeException exception) {
            reportOnce(monitor.getClass(), exception);
            tag.remove(PAYLOAD_KEY);
        }
    }

    public static void readClientPayload(Object monitor, CompoundTag tag, boolean clientPacket) {
        if (!clientPacket) {
            return;
        }
        if (!tag.contains(PAYLOAD_KEY, Tag.TAG_COMPOUND)) {
            CLIENT_PRODUCTS.remove(monitor);
            return;
        }
        try {
            CLIENT_PRODUCTS.put(monitor, WeatherRadarProduct.fromTag(tag.getCompound(PAYLOAD_KEY)));
        } catch (RuntimeException exception) {
            CLIENT_PRODUCTS.remove(monitor);
            reportOnce(monitor.getClass(), exception);
        }
    }

    public static WeatherRadarProduct clientProduct(Object monitor) {
        if (!enabled() || monitor == null) {
            return null;
        }
        return CLIENT_PRODUCTS.get(monitor);
    }

    public static int monitorSize(Object monitor) {
        if (monitor == null) return 1;
        try {
            return Math.max(1, ((Number) MONITOR_BINDINGS.get(monitor.getClass()).getSize.invoke(monitor)).intValue());
        } catch (ReflectiveOperationException | RuntimeException exception) {
            reportOnce(monitor.getClass(), exception);
            return 1;
        }
    }

    public static Direction monitorFacing(Object monitor) {
        if (!(monitor instanceof BlockEntity blockEntity)) {
            return Direction.NORTH;
        }
        BlockState state = blockEntity.getBlockState();
        for (Property<?> property : state.getProperties()) {
            if (!"facing".equals(property.getName())) continue;
            Comparable<?> value = readProperty(state, property);
            if (value instanceof Direction direction) {
                return direction;
            }
        }
        return Direction.NORTH;
    }

    @SuppressWarnings({"rawtypes", "unchecked"})
    private static Comparable<?> readProperty(BlockState state, Property<?> property) {
        return state.getValue((Property) property);
    }

    private static boolean enabled() {
        try {
            return DrewCraftConfig.RADAR.get() && DrewCraftConfig.CREATE_RADARS_ADAPTER.get();
        } catch (IllegalStateException exception) {
            return true;
        }
    }

    private static void reportOnce(Class<?> type, Throwable throwable) {
        if (REPORTED_FAILURES.add(type)) {
            DrewCraft.LOGGER.warn("Create: Radars weather bridge disabled for {}: {}", type.getName(), throwable.toString());
        }
    }

    private record MonitorBindings(Method isController, Method getRadar, Method getSize) {
    }

    private record RadarBindings(Method isRunning, Method getRange, Method getWorldPos, Method getRadarType) {
    }
}
