package dev.drewcraft.strategic.source;

import java.util.Objects;

public record SourceCorePosition(String dimension, int x, int y, int z) {
    public SourceCorePosition {
        Objects.requireNonNull(dimension, "dimension");
        if (dimension.isBlank()) throw new IllegalArgumentException("dimension must not be blank");
    }
}
