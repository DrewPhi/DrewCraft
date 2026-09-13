package dev.drewcraft.strategic.encounter;

/** Durable lifecycle for one tactical manifestation of a strategic group. */
public enum StrategicEncounterState {
    PREPARING,
    MATERIALIZED,
    RECONCILING,
    COMPLETE
}
