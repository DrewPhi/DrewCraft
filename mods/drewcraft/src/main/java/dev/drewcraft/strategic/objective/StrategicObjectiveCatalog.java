package dev.drewcraft.strategic.objective;

import dev.drewcraft.strategic.model.StrategicPosition;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Immutable-at-runtime objectives supplied by the reviewed production-world seed file. */
public final class StrategicObjectiveCatalog {
    private static List<StrategicObjective> objectives = List.of();

    private StrategicObjectiveCatalog() { }

    public static synchronized void replace(List<StrategicObjective> replacement) {
        objectives = List.copyOf(replacement);
    }

    public static synchronized void clear() {
        objectives = List.of();
    }

    public static synchronized Optional<StrategicObjective> nearest(StrategicPosition origin) {
        return objectives.stream()
                .filter(objective -> objective.position().dimension().equals(origin.dimension()))
                .min(Comparator.<StrategicObjective>comparingDouble(
                                objective -> objective.position().distanceTo(origin))
                        .thenComparing(StrategicObjective::id));
    }

    public static synchronized List<StrategicObjective> all() {
        return new ArrayList<>(objectives);
    }

    public record StrategicObjective(String id, String kind, StrategicPosition position) {
        public StrategicObjective {
            Objects.requireNonNull(id, "id");
            Objects.requireNonNull(kind, "kind");
            Objects.requireNonNull(position, "position");
            if (id.isBlank() || kind.isBlank()) throw new IllegalArgumentException("objective id/kind must not be blank");
        }
    }
}
