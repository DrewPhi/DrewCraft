package dev.drewcraft.strategic.model;

/** Why a strategic group is allowed to know its persisted objective. */
public enum StrategicTargetKnowledge {
    /** Migration/default for groups created before BP5 mission metadata existed. */
    LEGACY_ROUTE,
    /** Objective comes only from the source's own generated geography. */
    SOURCE_GEOGRAPHY,
    /** Objective is a deterministic regional scouting waypoint; no player position is queried. */
    SCOUTED_REGION,
    /** Objective is the known position of another persistent allied source. */
    ALLIED_SOURCE_LOCATION,
    /** Explicit wildlife migration corridor supplied by world-build/offline herd seeding. */
    MIGRATION_ROUTE
}
