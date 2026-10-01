package dev.drewcraft.adapter.mts;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Assumptions;
import static org.junit.jupiter.api.Assertions.*;

class MtsFuelCapacityPolicyTest {
    @Test void exactShippingMtsVehicleSchemaAndHookExist() throws Exception {
        Assumptions.assumeTrue(Boolean.getBoolean("drewcraft.verifyMts"));
        Class<?> vehicleClass = Class.forName("minecrafttransportsimulator.jsondefs.JSONVehicle");
        Object vehicle = vehicleClass.getConstructor().newInstance();
        var motorizedField = vehicleClass.getField("motorized");
        Object motorized = motorizedField.getType().getConstructor().newInstance();
        motorizedField.set(vehicle, motorized);
        var capacity = motorized.getClass().getField("fuelCapacity");
        var initial = motorized.getClass().getField("defaultFuelQty");
        capacity.setInt(motorized, 10000);
        initial.setInt(motorized, 1000);
        MtsFuelCapacityPolicy.applyVehicleDefinition(vehicle);
        MtsFuelCapacityPolicy.applyVehicleDefinition(vehicle);
        assertEquals(20000, capacity.getInt(motorized));
        assertEquals(1000, initial.getInt(motorized));
        // Inspect the target without initializing MTS runtime/game state.
        Class<?> parser = Class.forName("minecrafttransportsimulator.packloading.PackParser", false,
                vehicleClass.getClassLoader());
        Class<?> definition = Class.forName("minecrafttransportsimulator.jsondefs.AJSONMultiModelProvider");
        assertNotNull(parser.getDeclaredMethod("parseAllDefinitions", definition,
                java.util.List.class, String.class));
    }

    public static class Motorized {
        public int fuelCapacity;
        public int defaultFuelQty = 100;
        Motorized(int capacity) { fuelCapacity = capacity; }
    }

    @Test void doublesOnceWithoutGrantingFuel() throws Exception {
        Motorized motor = new Motorized(10000);
        MtsFuelCapacityPolicy.doubleCapacityOnce(motor);
        MtsFuelCapacityPolicy.doubleCapacityOnce(motor);
        assertEquals(20000, motor.fuelCapacity);
        assertEquals(100, motor.defaultFuelQty);
    }

    @Test void independentDefinitionsAndZeroCapacity() throws Exception {
        Motorized first = new Motorized(2500), second = new Motorized(2500), zero = new Motorized(0);
        for (Motorized motor : new Motorized[]{first, second, zero})
            MtsFuelCapacityPolicy.doubleCapacityOnce(motor);
        assertEquals(5000, first.fuelCapacity);
        assertEquals(5000, second.fuelCapacity);
        assertEquals(0, zero.fuelCapacity);
    }

    @Test void invalidCapacityDoesNotWrapOrMutate() {
        Motorized overflow = new Motorized(Integer.MAX_VALUE), negative = new Motorized(-1);
        assertThrows(ArithmeticException.class, () -> MtsFuelCapacityPolicy.doubleCapacityOnce(overflow));
        assertThrows(IllegalArgumentException.class, () -> MtsFuelCapacityPolicy.doubleCapacityOnce(negative));
        assertEquals(Integer.MAX_VALUE, overflow.fuelCapacity);
        assertEquals(-1, negative.fuelCapacity);
    }

    @Test void nonVehicleDefinitionsAreUntouched() {
        Motorized storage = new Motorized(10000);
        MtsFuelCapacityPolicy.applyVehicleDefinition(storage);
        MtsFuelCapacityPolicy.applyVehicleDefinition(null);
        assertEquals(10000, storage.fuelCapacity);
    }
}
