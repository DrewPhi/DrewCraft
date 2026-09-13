package dev.drewcraft.strategic.herd;

import dev.drewcraft.strategic.model.StrategicPosition;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.UUID;

/** Immutable world-build seed for one explicitly owned strategic wild herd. */
public record WildHerdDescriptor(
        String dimension,
        String speciesEntityId,
        int originX,
        int originZ,
        int destinationX,
        int destinationZ,
        int count,
        double movementSpeedBlocksPerSecond
) {
    public static final String WILDLIFE_FACTION_ID = "drewcraft:wildlife";

    public WildHerdDescriptor {
        dimension = requireNonBlank(dimension, "dimension");
        speciesEntityId = requireNonBlank(speciesEntityId, "speciesEntityId");
        if (count <= 0) throw new IllegalArgumentException("count must be positive");
        if (!Double.isFinite(movementSpeedBlocksPerSecond) || movementSpeedBlocksPerSecond <= 0.0) {
            throw new IllegalArgumentException("movementSpeedBlocksPerSecond must be finite and positive");
        }
    }

    public StrategicPosition origin() {
        return new StrategicPosition(dimension, originX + 0.5, originZ + 0.5);
    }

    public StrategicPosition destination() {
        return new StrategicPosition(dimension, destinationX + 0.5, destinationZ + 0.5);
    }

    public UUID stableHerdId() {
        String key = "drewcraft-wild-herd-v1|" + dimension + "|" + speciesEntityId
                + "|" + originX + "|" + originZ + "|" + destinationX + "|" + destinationZ;
        return UUID.nameUUIDFromBytes(key.getBytes(StandardCharsets.UTF_8));
    }

    public String templateId() {
        return "drewcraft:wild_herd/" + speciesEntityId.replace(':', '_');
    }

    private static String requireNonBlank(String value, String name) {
        Objects.requireNonNull(value, name);
        if (value.isBlank()) throw new IllegalArgumentException(name + " must not be blank");
        return value;
    }
}
