package dev.drewcraft.adapter.mts;

import dev.drewcraft.service.vehicle.VehicleQueryResult;
import dev.drewcraft.service.vehicle.VehicleService;
import dev.drewcraft.service.vehicle.VehicleSnapshot;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.List;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/** Read-only MTS/Immersive Vehicles observation adapter. */
public final class MtsVehicleService implements VehicleService {
    public static final String PROVIDER_ID = "mts.vehicle";
    private static final String WRAPPER_WORLD_CLASS = "mcinterface1211.WrapperWorld";
    private static final String VEHICLE_CLASS = "minecrafttransportsimulator.entities.instances.EntityVehicleF_Physics";

    private final Bindings bindings;

    public MtsVehicleService() {
        this.bindings = Bindings.tryBind();
    }

    @Override
    public String providerId() {
        return PROVIDER_ID;
    }

    @Override
    public VehicleQueryResult query(ServerLevel level, Vec3 center, double radiusBlocks) {
        if (level == null || center == null || !Double.isFinite(radiusBlocks) || radiusBlocks < 0.0) {
            return VehicleQueryResult.unavailable(providerId(), "invalid_request");
        }
        if (bindings == null) {
            return VehicleQueryResult.unavailable(providerId(), "mts_vehicle_api_unavailable");
        }

        try {
            Object wrapper = bindings.getWrapperFor.invoke(null, level);
            Object raw = bindings.getEntitiesOfType.invoke(wrapper, bindings.vehicleClass);
            if (!(raw instanceof Collection<?> vehicles)) {
                return VehicleQueryResult.unavailable(providerId(), "mts_entity_collection_shape_mismatch");
            }

            double radiusSquared = radiusBlocks * radiusBlocks;
            List<VehicleSnapshot> snapshots = new ArrayList<>();
            for (Object vehicle : vehicles) {
                if (!bindings.decoder.isValid(vehicle)) {
                    continue;
                }
                VehicleSnapshot snapshot = bindings.decoder.decode(vehicle);
                if (snapshot.position().distanceToSqr(center) <= radiusSquared) {
                    snapshots.add(snapshot);
                }
            }
            snapshots.sort(Comparator.comparingDouble(snapshot -> snapshot.position().distanceToSqr(center)));
            return new VehicleQueryResult(true, providerId(), snapshots, "mts_vehicle_snapshot");
        } catch (ReflectiveOperationException | RuntimeException exception) {
            return VehicleQueryResult.unavailable(providerId(),
                    "mts_vehicle_api_mismatch:" + exception.getClass().getSimpleName());
        }
    }

    private record Bindings(
            Class<?> vehicleClass,
            Method getWrapperFor,
            Method getEntitiesOfType,
            MtsVehicleDecoder decoder
    ) {
        private static Bindings tryBind() {
            try {
                ClassLoader loader = MtsVehicleService.class.getClassLoader();
                Class<?> wrapperClass = Class.forName(WRAPPER_WORLD_CLASS, false, loader);
                Class<?> vehicleClass = Class.forName(VEHICLE_CLASS, false, loader);
                Method getWrapperFor = wrapperClass.getMethod("getWrapperFor", Level.class);
                Method getEntitiesOfType = wrapperClass.getMethod("getEntitiesOfType", Class.class);
                MtsVehicleDecoder decoder = MtsVehicleDecoder.tryBind(vehicleClass);
                if (decoder == null) {
                    return null;
                }
                return new Bindings(vehicleClass, getWrapperFor, getEntitiesOfType, decoder);
            } catch (ReflectiveOperationException | LinkageError exception) {
                return null;
            }
        }
    }
}
