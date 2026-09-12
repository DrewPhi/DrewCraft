package dev.drewcraft.service.power;

import java.util.Objects;
import java.util.Optional;
import java.util.OptionalDouble;
import net.minecraft.core.BlockPos;

/** Immutable Create-kinetic snapshot owned by DrewCraft. */
public record PowerSample(
        boolean available,
        String providerId,
        BlockPos requestedPosition,
        Optional<BlockPos> sourcePosition,
        Optional<Boolean> kineticallyPowered,
        OptionalDouble speedRpm,
        OptionalDouble theoreticalSpeedRpm,
        Optional<Boolean> overstressed,
        Optional<Boolean> networkPresent,
        String status
) {
    public PowerSample {
        Objects.requireNonNull(providerId);
        Objects.requireNonNull(requestedPosition);
        Objects.requireNonNull(sourcePosition);
        Objects.requireNonNull(kineticallyPowered);
        Objects.requireNonNull(speedRpm);
        Objects.requireNonNull(theoreticalSpeedRpm);
        Objects.requireNonNull(overstressed);
        Objects.requireNonNull(networkPresent);
        Objects.requireNonNull(status);
        requestedPosition = requestedPosition.immutable();
        sourcePosition = sourcePosition.map(BlockPos::immutable);
    }

    public static PowerSample unavailable(String providerId, BlockPos position, String status) {
        return new PowerSample(
                false,
                providerId,
                position,
                Optional.empty(),
                Optional.empty(),
                OptionalDouble.empty(),
                OptionalDouble.empty(),
                Optional.empty(),
                Optional.empty(),
                status
        );
    }

    public static PowerSample noInput(String providerId, BlockPos position) {
        return new PowerSample(
                true,
                providerId,
                position,
                Optional.empty(),
                Optional.of(false),
                OptionalDouble.of(0.0),
                OptionalDouble.of(0.0),
                Optional.of(false),
                Optional.of(false),
                "no_local_create_kinetic_input"
        );
    }
}
