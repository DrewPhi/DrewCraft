package dev.drewcraft.strategic.encounter;

import dev.drewcraft.strategic.model.StrategicGroup;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Pure bounded wave planner. It never touches a Minecraft world or entity. */
public final class StrategicEncounterPlanner {
    private StrategicEncounterPlanner() {
    }

    public static List<String> nextWave(StrategicGroup group, StrategicEncounter encounter, int activeEntityCap) {
        Objects.requireNonNull(group, "group");
        Objects.requireNonNull(encounter, "encounter");
        if (activeEntityCap < 1) throw new IllegalArgumentException("activeEntityCap must be positive");
        if (!group.groupId().equals(encounter.groupId())) {
            throw new IllegalArgumentException("encounter does not belong to group");
        }

        int freeSlots = Math.max(0, activeEntityCap - encounter.activeEntityCount());
        if (freeSlots == 0 || group.totalStrength() == 0) return List.of();

        ArrayList<String> result = new ArrayList<>(freeSlots);
        group.composition().entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .forEach(entry -> {
                    if (result.size() >= freeSlots) return;
                    int alreadyActive = encounter.activeCountForType(entry.getKey());
                    int abstractReserve = Math.max(0, entry.getValue() - alreadyActive);
                    int take = Math.min(abstractReserve, freeSlots - result.size());
                    for (int i = 0; i < take; i++) result.add(entry.getKey());
                });
        return List.copyOf(result);
    }
}
