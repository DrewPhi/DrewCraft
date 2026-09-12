package dev.drewcraft.service.power;

import java.util.Objects;
import java.util.Optional;
import java.util.OptionalDouble;
import net.minecraft.core.BlockPos;

public record PowerSample(
        boolean available,
        String providerId,
        BlockPos requestedPosition,
        Optional<Boolean> kineticallyPowered,
        OptionalDouble speedRpm,
        Optional<Boolean> overstressed,
        String status
) {
    public PowerSample {
        Objects.requireNonNull(providerId);
        Objects.requireNonNull(requestedPosition);
        Objects.requireNonNull(kineticallyPowered);
        Objects.requireNonNull(speedRpm);
        Objects.requireNonNull(overstressed);
        Objects.requireNonNull(status);
    }

    public static PowerSample unavailable(String providerId, BlockPos position, String status) {
        return new PowerSample(
                false,
                providerId,
                position.immutable(),
                Optional.empty(),
                OptionalDouble.empty(),
                Optional.empty(),
                status
        );
    }
}
