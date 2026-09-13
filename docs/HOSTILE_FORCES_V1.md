# DrewCraft V1 Hostile Strategic Forces

This document is the BP5 implementation contract for factions, patrols, hordes, raids, armies, and reinforcements. It builds on `STRATEGIC_WORLD_MODEL.md`, `STRATEGIC_MATERIALIZATION.md`, and `SOURCE_CORE_SPEC.md`.

## Core rule

> **A strategic force is a persistent population and mission record. Minecraft entities are only a bounded tactical projection of that record near players.**

A 256-unit army therefore remains one lightweight `StrategicGroup` while distant. When observed, BP3 may materialize at most the configured active cap (64 by default), with later waves drawn from the surviving strategic population.

## Data-driven faction catalog

Packaged V1 force content lives in:

`mods/drewcraft/src/main/resources/data/drewcraft/strategic/factions.json`

The schema describes:

- faction ID;
- group template ID;
- strategic role (`PATROL`, `HORDE`, `RAID`, `ARMY`, `REINFORCEMENT`);
- source classes allowed to launch the template;
- strength multiplier relative to the source's base production strength;
- target policy;
- minimum/maximum strategic travel distance;
- weighted Minecraft entity composition.

`StrategicFactionCatalog` parses and validates the packaged JSON into immutable templates. `StrategicForceTemplate` deterministically converts weighted composition into exact integer counts whose sum is always the represented strategic strength.

V1 ships three profiles:

- `drewcraft:test_hostile` for deterministic development tests;
- `drewcraft:undead`;
- `drewcraft:raiders`.

The catalog is content data rather than scheduler logic, so later composition/balance changes do not require replacing the strategic simulation architecture.

## Roles

### Patrol

Small source-local force. Uses source geography only and stays relatively close to its producer.

### Horde / warband

Larger roaming force. Uses a regional route derived from source geography and does not acquire players through hidden global queries.

### Raid

Medium expedition toward a persisted scouted regional objective.

### Army

Large represented population. City/stronghold V1 templates use an 8x source base-strength multiplier. A stronghold with base strength 32 can therefore commit one 256-unit army if its persistent population budget can pay for it.

### Reinforcement

Prefers another intact persistent source of the same faction in the same dimension. If no allied source exists, it falls back to an explicit source-geography regional route rather than inventing an unseen target.

## Exact source-budget accounting

BP4 originally proved fixed-size source launches. BP5 extends source authority so a launch consumes the exact `StrategicGroup.totalStrength()` it represents.

The variable-strength launch commit remains inside the same synchronized SavedData authority used by Source Core clearing. Before commit DrewCraft verifies:

- source identity;
- source generation;
- source is not cleared;
- group source ID matches;
- faction matches;
- dimension matches;
- group ID is not already present;
- persistent source population budget can pay the exact represented strength.

Only after those checks does source budget decrement and the group enter persistent strategic state.

Therefore a 256-unit army consumes 256 source population, not 32, and BP4 clear-vs-launch race safety is preserved.

## Mission state and non-omniscient targeting

Strategic groups now persist `StrategicMission` metadata:

- template ID;
- target knowledge category;
- human-readable knowledge explanation;
- exact persisted target position;
- issue game time.

Knowledge categories are:

- `LEGACY_ROUTE` — migration state for pre-BP5 groups;
- `SOURCE_GEOGRAPHY` — local/regional destination derived only from the generated source;
- `SCOUTED_REGION` — deterministic precomputed scouting objective;
- `ALLIED_SOURCE_LOCATION` — position of another persistent same-faction source.

The BP5 source planner does **not** query the nearest player, scan for hidden player bases, or read unloaded player construction to choose a target.

The mission target is persisted with the group and must match its strategic route destination. Mission and casualties therefore survive chunk unload and restart together.

Future gameplay may add legitimate ways for factions to learn a player settlement (combat contact, scouting, discovered roads, alarms, etc.), but that must enter the same explicit target-knowledge model rather than adding omniscient target selection.

## Large-army materialization

BP5 does not raise BP3's tactical limits.

Default BP3 limits remain:

- maximum active entities per encounter: 64;
- maximum successful new strategic spawns globally per materialization cycle: 128;
- maximum encounter records inspected per cycle: 32.

Example:

```text
Strategic army strength = 256
        |
player approaches
        v
maximum 64 tactical entities
        |
37 die
        v
strategic strength = 219
active survivors = 27
        |
next wave can add at most 37
        v
active population returns to 64, not 219
```

The remaining 155 units are still abstract reserve.

## Persistence

`StrategicGroup` schema 3 adds mission metadata. Schema-1 and schema-2 groups migrate to `LEGACY_ROUTE` mission state using their existing persisted destination.

Composition and total strength are now validated to be exactly equal at group construction/load time. Tactical casualties decrement both together through BP3 encounter authority.

## BP5 automated acceptance

Focused tests cover:

- packaged faction catalog loading;
- undead and raider availability for all five V1 hostile roles;
- exact deterministic weighted composition allocation;
- affordability filtering;
- mission NBT round trip;
- schema-1/schema-2 mission migration;
- future group-schema rejection;
- non-omniscient stronghold army planning with `SCOUTED_REGION` knowledge;
- 256-unit stronghold army exact source-budget debit;
- 64-unit tactical cap on that army;
- 37 tactical deaths -> 219 strategic survivors;
- 27 active survivors -> exactly 37 available slots in the next wave;
- save/restart preserves army role, mission, target, casualty count, and active encounter authority.

## BP5 / BP6 boundary

BP5 decides **what force exists, how large it is, where it is going, and why it knows that destination**.

BP6 decides **what a loaded hostile encounter does when ordinary local navigation cannot reach its objective because a fortification blocks the way**.

BP5 therefore does not implement block breaking or siege breach selection.
