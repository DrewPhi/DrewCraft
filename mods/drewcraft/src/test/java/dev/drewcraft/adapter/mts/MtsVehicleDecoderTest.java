package dev.drewcraft.adapter.mts;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import dev.drewcraft.service.vehicle.VehicleSnapshot;
import java.util.UUID;
import org.junit.jupiter.api.Test;

final class MtsVehicleDecoderTest {
    @Test
    void decodesPublicMtsShapeIntoOwnedSnapshot() throws Exception {
        MtsVehicleDecoder decoder = MtsVehicleDecoder.tryBind(FakeVehicle.class);
        assertTrue(decoder != null);

        UUID id = UUID.randomUUID();
        FakeVehicle vehicle = new FakeVehicle(id);
        VehicleSnapshot snapshot = decoder.decode(vehicle);

        assertEquals(id, snapshot.id());
        assertEquals("testpack:testplane", snapshot.typeId());
        assertEquals(10.0, snapshot.position().x, 1.0e-6);
        assertEquals(2.0, snapshot.velocityBlocksPerTick().z, 1.0e-6);
        assertEquals(90.0, snapshot.yawDegrees(), 1.0e-6);
        assertEquals(5.0, snapshot.pitchDegrees(), 1.0e-6);
        assertEquals(-3.0, snapshot.rollDegrees(), 1.0e-6);
        assertTrue(snapshot.aircraft());
    }

    public static class Point {
        public double x;
        public double y;
        public double z;
        Point(double x, double y, double z) { this.x = x; this.y = y; this.z = z; }
    }

    public static class Rotation {
        public final Point angles = new Point(5, 90, -3);
    }

    public static class Motorized {
        public boolean isAircraft = true;
    }

    public static class Definition {
        public Motorized motorized = new Motorized();
    }

    public static class FakeVehicle {
        public UUID uniqueUUID;
        public boolean isValid = true;
        public Point position = new Point(10, 80, -4);
        public Point motion = new Point(1, 0, 2);
        public Rotation orientation = new Rotation();
        public Definition definition = new Definition();

        FakeVehicle(UUID id) { this.uniqueUUID = id; }

        @Override
        public String toString() { return "testpack:testplane"; }
    }
}
