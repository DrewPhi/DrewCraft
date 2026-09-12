package dev.drewcraft.service.terrain;

import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import net.minecraft.core.BlockPos;

public record TerrainSample(
        boolean available,
        String providerId,
        BlockPos requestedPosition,
        OptionalInt surfaceY,
        Optional<String> biomeId,
        Optional<String> surfaceBlockId,
        OptionalInt seaLevel,
        String status
) {
    public TerrainSample {
        Objects.requireNonNull(providerId);
        Objects.requireNonNull(requestedPosition);
        Objects.requireNonNull(surfaceY);
        Objects.requireNonNull(biomeId);
        Objects.requireNonNull(surfaceBlockId);
        Objects.requireNonNull(seaLevel);
        Objects.requireNonNull(status);
    }

    public static TerrainSample unavailable(String providerId, BlockPos position, String status) {
        return new TerrainSample(
                false,
                providerId,
                position.immutable(),
                OptionalInt.empty(),
                Optional.empty(),
                Optional.empty(),
                OptionalInt.empty(),
                status
        );
    }

    public static TerrainSample available(
            String providerId,
            BlockPos position,
            int surfaceY,
            String biomeId,
            String surfaceBlockId,
            int seaLevel,
            String status
    ) {
        return new TerrainSample(
                true,
                providerId,
                position.immutable(),
                OptionalInt.of(surfaceY),
                Optional.of(biomeId),
                Optional.of(surfaceBlockId),
                OptionalInt.of(seaLevel),
                status
        );
    }
}
