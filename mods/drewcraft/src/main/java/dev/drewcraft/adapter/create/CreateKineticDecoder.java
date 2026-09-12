package dev.drewcraft.adapter.create;

import dev.drewcraft.service.power.PowerSample;
import java.lang.reflect.Method;
import java.util.Optional;
import java.util.OptionalDouble;
import net.minecraft.core.BlockPos;

/**
 * Reflection decoder for Create's public kinetic read surface. Reflection is kept
 * inside the adapter so core DrewCraft code never imports Create implementation types.
 */
final class CreateKineticDecoder {
    private CreateKineticDecoder() {
    }

    static PowerSample decode(
            String providerId,
            Object kineticBlockEntity,
            BlockPos requestedPosition,
            BlockPos sourcePosition,
            Method getSpeed,
            Method getTheoreticalSpeed,
            Method isOverStressed,
            Method hasNetwork
    ) {
        try {
            double speed = ((Number) getSpeed.invoke(kineticBlockEntity)).doubleValue();
            double theoreticalSpeed = ((Number) getTheoreticalSpeed.invoke(kineticBlockEntity)).doubleValue();
            boolean overstressed = (Boolean) isOverStressed.invoke(kineticBlockEntity);
            boolean networkPresent = (Boolean) hasNetwork.invoke(kineticBlockEntity);
            boolean powered = networkPresent && !overstressed && Math.abs(speed) > 1.0e-4;

            return new PowerSample(
                    true,
                    providerId,
                    requestedPosition,
                    Optional.of(sourcePosition),
                    Optional.of(powered),
                    OptionalDouble.of(speed),
                    OptionalDouble.of(theoreticalSpeed),
                    Optional.of(overstressed),
                    Optional.of(networkPresent),
                    "create_kinetic_sample"
            );
        } catch (ReflectiveOperationException | ClassCastException exception) {
            return PowerSample.unavailable(providerId, requestedPosition,
                    "create_kinetic_api_mismatch:" + exception.getClass().getSimpleName());
        }
    }
}
