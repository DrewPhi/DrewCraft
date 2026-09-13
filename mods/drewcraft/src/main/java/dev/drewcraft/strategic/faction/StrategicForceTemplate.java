package dev.drewcraft.strategic.faction;

import dev.drewcraft.strategic.model.StrategicGroupType;
import dev.drewcraft.strategic.source.SourceClass;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/** Immutable data-driven hostile force template. */
public record StrategicForceTemplate(
        String id,
        StrategicGroupType groupType,
        Set<SourceClass> allowedSourceClasses,
        int strengthMultiplier,
        StrategicTargetPolicy targetPolicy,
        double minDistanceBlocks,
        double maxDistanceBlocks,
        Map<String, Double> compositionWeights
) {
    public StrategicForceTemplate {
        id = requireNonBlank(id, "id");
        groupType = Objects.requireNonNull(groupType, "groupType");
        if (groupType == StrategicGroupType.TEST || groupType == StrategicGroupType.HERD) {
            throw new IllegalArgumentException("hostile template cannot use group type " + groupType);
        }
        Objects.requireNonNull(allowedSourceClasses, "allowedSourceClasses");
        if (allowedSourceClasses.isEmpty()) throw new IllegalArgumentException("allowedSourceClasses must not be empty");
        allowedSourceClasses = Set.copyOf(EnumSet.copyOf(allowedSourceClasses));
        if (strengthMultiplier < 1) throw new IllegalArgumentException("strengthMultiplier must be positive");
        targetPolicy = Objects.requireNonNull(targetPolicy, "targetPolicy");
        if (!Double.isFinite(minDistanceBlocks) || !Double.isFinite(maxDistanceBlocks)
                || minDistanceBlocks < 0.0 || maxDistanceBlocks < minDistanceBlocks) {
            throw new IllegalArgumentException("invalid target-distance range");
        }
        Objects.requireNonNull(compositionWeights, "compositionWeights");
        LinkedHashMap<String, Double> normalized = new LinkedHashMap<>();
        compositionWeights.entrySet().stream().sorted(Map.Entry.comparingByKey()).forEach(entry -> {
            String entityId = requireNonBlank(entry.getKey(), "entity id");
            double weight = Objects.requireNonNull(entry.getValue(), "composition weight");
            if (!Double.isFinite(weight) || weight <= 0.0) throw new IllegalArgumentException("composition weights must be positive");
            normalized.put(entityId, weight);
        });
        if (normalized.isEmpty()) throw new IllegalArgumentException("compositionWeights must not be empty");
        compositionWeights = Collections.unmodifiableMap(normalized);
    }

    public boolean supports(SourceClass sourceClass) {
        return allowedSourceClasses.contains(sourceClass);
    }

    public int desiredStrength(int baseStrength) {
        if (baseStrength <= 0) throw new IllegalArgumentException("baseStrength must be positive");
        return Math.multiplyExact(baseStrength, strengthMultiplier);
    }

    /** Largest-remainder deterministic allocation; total always equals requested strength. */
    public Map<String, Integer> compositionForStrength(int strength) {
        if (strength <= 0) throw new IllegalArgumentException("strength must be positive");
        double sum = compositionWeights.values().stream().mapToDouble(Double::doubleValue).sum();
        LinkedHashMap<String, Integer> counts = new LinkedHashMap<>();
        List<Remainder> remainders = new ArrayList<>();
        int assigned = 0;
        for (Map.Entry<String, Double> entry : compositionWeights.entrySet()) {
            double exact = strength * entry.getValue() / sum;
            int floor = (int) Math.floor(exact);
            if (floor > 0) counts.put(entry.getKey(), floor);
            assigned += floor;
            remainders.add(new Remainder(entry.getKey(), exact - floor));
        }
        remainders.sort(Comparator.comparingDouble(Remainder::fraction).reversed().thenComparing(Remainder::entityId));
        for (int i = assigned; i < strength; i++) {
            String entityId = remainders.get((i - assigned) % remainders.size()).entityId();
            counts.merge(entityId, 1, Integer::sum);
        }
        return Collections.unmodifiableMap(counts);
    }

    private static String requireNonBlank(String value, String name) {
        Objects.requireNonNull(value, name);
        if (value.isBlank()) throw new IllegalArgumentException(name + " must not be blank");
        return value;
    }

    private record Remainder(String entityId, double fraction) {
    }
}
