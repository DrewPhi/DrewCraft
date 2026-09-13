package dev.drewcraft.strategic.model;

import java.util.Objects;

/** Persisted strategic objective plus an explicit explanation of how the group knows it. */
public record StrategicMission(
        String templateId,
        StrategicTargetKnowledge targetKnowledge,
        String knowledgeDetail,
        StrategicPosition target,
        long issuedGameTime
) {
    public StrategicMission {
        templateId = requireNonBlank(templateId, "templateId");
        targetKnowledge = Objects.requireNonNull(targetKnowledge, "targetKnowledge");
        knowledgeDetail = requireNonBlank(knowledgeDetail, "knowledgeDetail");
        target = Objects.requireNonNull(target, "target");
        issuedGameTime = Math.max(0L, issuedGameTime);
    }

    public static StrategicMission legacy(StrategicPosition target, long gameTime) {
        return new StrategicMission(
                "drewcraft:legacy_route",
                StrategicTargetKnowledge.LEGACY_ROUTE,
                "route existed before BP5 mission metadata",
                target,
                gameTime
        );
    }

    private static String requireNonBlank(String value, String name) {
        Objects.requireNonNull(value, name);
        if (value.isBlank()) throw new IllegalArgumentException(name + " must not be blank");
        return value;
    }
}
