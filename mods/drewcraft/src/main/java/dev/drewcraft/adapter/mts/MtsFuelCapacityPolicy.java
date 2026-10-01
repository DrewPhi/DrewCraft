package dev.drewcraft.adapter.mts;

import java.lang.reflect.Field;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** Doubles vehicle definition capacity, never saved fuel or generic fluid storage. */
public final class MtsFuelCapacityPolicy {
    private static final Set<Object> APPLIED = Collections.newSetFromMap(new IdentityHashMap<>());

    private MtsFuelCapacityPolicy() {}

    public static void applyVehicleDefinition(Object definition) {
        if (definition == null || !definition.getClass().getName().equals(
                "minecrafttransportsimulator.jsondefs.JSONVehicle")) return;
        try {
            Object motorized = definition.getClass().getField("motorized").get(definition);
            if (motorized != null) doubleCapacityOnce(motorized);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException("Pinned MTS vehicle fuel-capacity API changed", e);
        }
    }

    static synchronized void doubleCapacityOnce(Object motorized) throws ReflectiveOperationException {
        if (APPLIED.contains(motorized)) return;
        Field capacity = motorized.getClass().getField("fuelCapacity");
        int original = capacity.getInt(motorized);
        if (original < 0) throw new IllegalArgumentException("Negative MTS fuel capacity");
        int doubled = Math.multiplyExact(original, 2);
        capacity.setInt(motorized, doubled);
        APPLIED.add(motorized);
    }
}
