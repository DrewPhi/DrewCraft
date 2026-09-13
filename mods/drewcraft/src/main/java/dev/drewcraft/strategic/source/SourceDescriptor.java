package dev.drewcraft.strategic.source;

import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.UUID;

/** Immutable generated-geography identity used for idempotent hostile-source discovery. */
public record SourceDescriptor(
        String dimension,
        String structureId,
        int anchorX,
        int anchorY,
        int anchorZ,
        SourceCorePosition corePosition,
        SourceClass sourceClass,
        String factionId
) {
    public SourceDescriptor {
        dimension = requireNonBlank(dimension, "dimension");
        structureId = requireNonBlank(structureId, "structureId");
        corePosition = Objects.requireNonNull(corePosition, "corePosition");
        sourceClass = Objects.requireNonNull(sourceClass, "sourceClass");
        factionId = requireNonBlank(factionId, "factionId");
        if (!dimension.equals(corePosition.dimension())) {
            throw new IllegalArgumentException("source descriptor and core must share a dimension");
        }
    }

    public UUID stableSourceId() {
        String canonical = "drewcraft-source-v1|" + dimension + "|" + structureId + "|"
                + anchorX + "|" + anchorY + "|" + anchorZ;
        return UUID.nameUUIDFromBytes(canonical.getBytes(StandardCharsets.UTF_8));
    }

    private static String requireNonBlank(String value, String name) {
        Objects.requireNonNull(value, name);
        if (value.isBlank()) throw new IllegalArgumentException(name + " must not be blank");
        return value;
    }
}
