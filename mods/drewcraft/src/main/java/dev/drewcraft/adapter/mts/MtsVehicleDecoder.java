package dev.drewcraft.adapter.mts;

import dev.drewcraft.service.vehicle.VehicleSnapshot;
import java.lang.reflect.Field;
import java.util.UUID;
import net.minecraft.world.phys.Vec3;

/** Translates public MTS vehicle state into DrewCraft-owned immutable snapshots. */
final class MtsVehicleDecoder {
    private final Field uniqueUuid;
    private final Field isValid;
    private final Field position;
    private final Field motion;
    private final Field orientation;
    private final Field angles;
    private final Field pointX;
    private final Field pointY;
    private final Field pointZ;
    private final Field definition;

    private MtsVehicleDecoder(
            Field uniqueUuid,
            Field isValid,
            Field position,
            Field motion,
            Field orientation,
            Field angles,
            Field pointX,
            Field pointY,
            Field pointZ,
            Field definition
    ) {
        this.uniqueUuid = uniqueUuid;
        this.isValid = isValid;
        this.position = position;
        this.motion = motion;
        this.orientation = orientation;
        this.angles = angles;
        this.pointX = pointX;
        this.pointY = pointY;
        this.pointZ = pointZ;
        this.definition = definition;
    }

    static MtsVehicleDecoder tryBind(Class<?> vehicleClass) {
        try {
            Field position = vehicleClass.getField("position");
            Class<?> pointClass = position.getType();
            Field orientation = vehicleClass.getField("orientation");
            Field angles = orientation.getType().getField("angles");
            return new MtsVehicleDecoder(
                    vehicleClass.getField("uniqueUUID"),
                    vehicleClass.getField("isValid"),
                    position,
                    vehicleClass.getField("motion"),
                    orientation,
                    angles,
                    pointClass.getField("x"),
                    pointClass.getField("y"),
                    pointClass.getField("z"),
                    vehicleClass.getField("definition")
            );
        } catch (ReflectiveOperationException exception) {
            return null;
        }
    }

    VehicleSnapshot decode(Object vehicle) throws ReflectiveOperationException {
        UUID id = (UUID) uniqueUuid.get(vehicle);
        Object positionPoint = position.get(vehicle);
        Object motionPoint = motion.get(vehicle);
        Object orientationObject = orientation.get(vehicle);
        Object anglePoint = angles.get(orientationObject);

        return new VehicleSnapshot(
                id,
                String.valueOf(vehicle),
                vector(positionPoint),
                vector(motionPoint),
                number(pointY.get(anglePoint)),
                number(pointX.get(anglePoint)),
                number(pointZ.get(anglePoint)),
                isAircraft(definition.get(vehicle))
        );
    }

    boolean isValid(Object vehicle) throws IllegalAccessException {
        return isValid.getBoolean(vehicle);
    }

    private Vec3 vector(Object point) throws IllegalAccessException {
        return new Vec3(number(pointX.get(point)), number(pointY.get(point)), number(pointZ.get(point)));
    }

    private static double number(Object value) {
        return ((Number) value).doubleValue();
    }

    private static boolean isAircraft(Object definition) throws ReflectiveOperationException {
        if (definition == null) {
            return false;
        }
        Field motorizedField = definition.getClass().getField("motorized");
        Object motorized = motorizedField.get(definition);
        if (motorized == null) {
            return false;
        }
        return motorized.getClass().getField("isAircraft").getBoolean(motorized);
    }
}
