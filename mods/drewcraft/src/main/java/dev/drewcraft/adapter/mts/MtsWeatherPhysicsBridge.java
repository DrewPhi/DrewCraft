package dev.drewcraft.adapter.mts;

import dev.drewcraft.aviation.AviationAirflowSample;
import dev.drewcraft.aviation.AviationWindModel;
import dev.drewcraft.config.DrewCraftConfig;
import dev.drewcraft.service.DrewCraftServices;
import dev.drewcraft.service.terrain.TerrainSample;
import dev.drewcraft.service.weather.WeatherSample;
import java.lang.reflect.Field;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.Vec3;

/**
 * Narrow MTS physics bridge. It temporarily expresses MTS motion relative to the
 * surrounding air so MTS's own aerodynamic model sees headwind/crosswind/turbulence,
 * then restores the resulting motion to the ground-relative frame.
 */
public final class MtsWeatherPhysicsBridge {
    private static volatile Bindings bindings;

    private MtsWeatherPhysicsBridge() {
    }

    public static Frame beforeForces(Object vehicle) {
        if (vehicle == null || !DrewCraftConfig.MTS_VEHICLE_ADAPTER.get() || !DrewCraftConfig.AVIATION_WEATHER.get()) {
            return null;
        }
        Bindings b = bindingsFor(vehicle.getClass());
        if (b == null) {
            return null;
        }

        try {
            if (!b.isAircraft(vehicle)) {
                return null;
            }
            Object wrapperWorld = b.mtsWorld.get(vehicle);
            Object rawLevel = b.wrapperLevel.get(wrapperWorld);
            if (!(rawLevel instanceof ServerLevel level)) {
                return null;
            }

            Object positionPoint = b.position.get(vehicle);
            Vec3 position = b.readPoint(positionPoint);
            BlockPos blockPos = BlockPos.containing(position);
            WeatherSample weather = DrewCraftServices.weather().sample(level, blockPos);
            TerrainSample terrain = DrewCraftServices.terrain().sample(level, blockPos);
            UUID id = (UUID) b.uniqueUuid.get(vehicle);
            AviationAirflowSample airflow = AviationWindModel.calculate(weather, terrain, id, position, level.getGameTime());
            if (!airflow.available()) {
                return null;
            }

            double speedFactor = b.speedFactor.getDouble(vehicle);
            Vec3 windInternal = AviationWindModel.toMtsMotion(airflow.totalAirVelocityMps(), speedFactor);
            if (windInternal.lengthSqr() < 1.0e-12) {
                return null;
            }

            Object motionPoint = b.motion.get(vehicle);
            Vec3 groundMotion = b.readPoint(motionPoint);
            Vec3 airMotion = groundMotion.subtract(windInternal);
            b.writePoint(motionPoint, airMotion);
            b.velocity.setDouble(vehicle, airMotion.length());

            Vec3 heading = b.readPoint(b.headingVector.get(vehicle));
            double airAxialVelocity = Math.abs(airMotion.dot(heading));
            b.axialVelocity.setDouble(vehicle, airAxialVelocity);
            b.refreshAerodynamicVectors(vehicle, airMotion, heading);

            return new Frame(windInternal, airAxialVelocity, airflow);
        } catch (ReflectiveOperationException | RuntimeException exception) {
            return null;
        }
    }

    public static void afterForces(Object vehicle, Frame frame) {
        if (vehicle == null || frame == null) {
            return;
        }
        Bindings b = bindingsFor(vehicle.getClass());
        if (b == null) {
            return;
        }
        try {
            Object motionPoint = b.motion.get(vehicle);
            Vec3 groundMotion = b.readPoint(motionPoint).add(frame.windInternal());
            b.writePoint(motionPoint, groundMotion);
            b.velocity.setDouble(vehicle, groundMotion.length());
            // Keep axialVelocity air-relative so MTS indicatedSpeed behaves like airspeed.
            b.axialVelocity.setDouble(vehicle, frame.airAxialVelocity());
            Vec3 heading = b.readPoint(b.headingVector.get(vehicle));
            b.refreshGroundVectors(vehicle, groundMotion, heading);
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            // Optional compatibility bridge: fail closed instead of taking down the server.
        }
    }

    private static Bindings bindingsFor(Class<?> vehicleClass) {
        Bindings current = bindings;
        if (current != null && current.vehicleClass == vehicleClass) {
            return current;
        }
        Bindings created = Bindings.tryBind(vehicleClass);
        bindings = created;
        return created;
    }

    public record Frame(Vec3 windInternal, double airAxialVelocity, AviationAirflowSample airflow) {
    }

    private static final class Bindings {
        private final Class<?> vehicleClass;
        private final Field uniqueUuid;
        private final Field mtsWorld;
        private final Field wrapperLevel;
        private final Field position;
        private final Field motion;
        private final Field orientation;
        private final Field headingVector;
        private final Field speedFactor;
        private final Field velocity;
        private final Field axialVelocity;
        private final Field normalizedVelocityVector;
        private final Field verticalVector;
        private final Field sideVector;
        private final Field definition;
        private final Field pointX;
        private final Field pointY;
        private final Field pointZ;
        private final Field matrixM01;
        private final Field matrixM11;
        private final Field matrixM21;

        private Bindings(
                Class<?> vehicleClass,
                Field uniqueUuid,
                Field mtsWorld,
                Field wrapperLevel,
                Field position,
                Field motion,
                Field orientation,
                Field headingVector,
                Field speedFactor,
                Field velocity,
                Field axialVelocity,
                Field normalizedVelocityVector,
                Field verticalVector,
                Field sideVector,
                Field definition,
                Field pointX,
                Field pointY,
                Field pointZ,
                Field matrixM01,
                Field matrixM11,
                Field matrixM21
        ) {
            this.vehicleClass = vehicleClass;
            this.uniqueUuid = uniqueUuid;
            this.mtsWorld = mtsWorld;
            this.wrapperLevel = wrapperLevel;
            this.position = position;
            this.motion = motion;
            this.orientation = orientation;
            this.headingVector = headingVector;
            this.speedFactor = speedFactor;
            this.velocity = velocity;
            this.axialVelocity = axialVelocity;
            this.normalizedVelocityVector = normalizedVelocityVector;
            this.verticalVector = verticalVector;
            this.sideVector = sideVector;
            this.definition = definition;
            this.pointX = pointX;
            this.pointY = pointY;
            this.pointZ = pointZ;
            this.matrixM01 = matrixM01;
            this.matrixM11 = matrixM11;
            this.matrixM21 = matrixM21;
        }

        static Bindings tryBind(Class<?> vehicleClass) {
            try {
                Field position = vehicleClass.getField("position");
                Class<?> pointClass = position.getType();
                Field orientation = vehicleClass.getField("orientation");
                Class<?> matrixClass = orientation.getType();
                Field wrapperLevel = Class.forName("mcinterface1211.WrapperWorld", false, vehicleClass.getClassLoader())
                        .getDeclaredField("world");
                wrapperLevel.setAccessible(true);

                Field normalized = vehicleClass.getDeclaredField("normalizedVelocityVector");
                Field vertical = vehicleClass.getDeclaredField("verticalVector");
                Field side = vehicleClass.getDeclaredField("sideVector");
                normalized.setAccessible(true);
                vertical.setAccessible(true);
                side.setAccessible(true);

                return new Bindings(
                        vehicleClass,
                        vehicleClass.getField("uniqueUUID"),
                        vehicleClass.getField("world"),
                        wrapperLevel,
                        position,
                        vehicleClass.getField("motion"),
                        orientation,
                        vehicleClass.getField("headingVector"),
                        vehicleClass.getField("speedFactor"),
                        vehicleClass.getField("velocity"),
                        vehicleClass.getField("axialVelocity"),
                        normalized,
                        vertical,
                        side,
                        vehicleClass.getField("definition"),
                        pointClass.getField("x"),
                        pointClass.getField("y"),
                        pointClass.getField("z"),
                        matrixClass.getField("m01"),
                        matrixClass.getField("m11"),
                        matrixClass.getField("m21")
                );
            } catch (ReflectiveOperationException | LinkageError exception) {
                return null;
            }
        }

        boolean isAircraft(Object vehicle) throws ReflectiveOperationException {
            Object def = definition.get(vehicle);
            if (def == null) {
                return false;
            }
            Object motorized = def.getClass().getField("motorized").get(def);
            return motorized != null && motorized.getClass().getField("isAircraft").getBoolean(motorized);
        }

        Vec3 readPoint(Object point) throws IllegalAccessException {
            return new Vec3(
                    ((Number) pointX.get(point)).doubleValue(),
                    ((Number) pointY.get(point)).doubleValue(),
                    ((Number) pointZ.get(point)).doubleValue()
            );
        }

        void writePoint(Object point, Vec3 value) throws IllegalAccessException {
            pointX.setDouble(point, value.x);
            pointY.setDouble(point, value.y);
            pointZ.setDouble(point, value.z);
        }

        void refreshAerodynamicVectors(Object vehicle, Vec3 airMotion, Vec3 heading)
                throws ReflectiveOperationException {
            Vec3 normalized = airMotion.lengthSqr() > 1.0e-12 ? airMotion.normalize() : Vec3.ZERO;
            Object matrix = orientation.get(vehicle);
            Vec3 vertical = new Vec3(
                    matrixM01.getDouble(matrix),
                    matrixM11.getDouble(matrix),
                    matrixM21.getDouble(matrix)
            );
            Vec3 side = vertical.cross(heading);
            writePoint(normalizedVelocityVector.get(vehicle), normalized);
            writePoint(verticalVector.get(vehicle), vertical);
            writePoint(sideVector.get(vehicle), side);
        }

        void refreshGroundVectors(Object vehicle, Vec3 groundMotion, Vec3 heading)
                throws ReflectiveOperationException {
            Vec3 normalized = groundMotion.lengthSqr() > 1.0e-12 ? groundMotion.normalize() : Vec3.ZERO;
            Object matrix = orientation.get(vehicle);
            Vec3 vertical = new Vec3(
                    matrixM01.getDouble(matrix),
                    matrixM11.getDouble(matrix),
                    matrixM21.getDouble(matrix)
            );
            Vec3 side = vertical.cross(heading);
            writePoint(normalizedVelocityVector.get(vehicle), normalized);
            writePoint(verticalVector.get(vehicle), vertical);
            writePoint(sideVector.get(vehicle), side);
        }
    }
}
