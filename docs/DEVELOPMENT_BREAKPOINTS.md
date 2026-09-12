# DrewCraft V1 Development Breakpoints

**Purpose:** define the stop/report points for continuous implementation sessions from the current post-8B state to `1.0.0`.

When the user says **"go"**, development should continue through the next unfinished breakpoint without asking for routine confirmation. Stop only when that breakpoint is reached, when a genuine blocking dependency/safety issue prevents further work, or when evidence shows the breakpoint definition itself must change. At each stop, report what was implemented, what tests/evidence passed, any known limitations, the exact Git commit/head, and the next breakpoint.

A breakpoint is intentionally larger than a single class or commit. It should end at a coherent proof that makes the next layer safe to build.

## BP1 — Strategic persistence + coarse simulation substrate

**Goal:** prove a strategic population can exist and move while represented only as persisted data.

Required before stopping:

- versioned `StrategicGroup` model with stable UUID identity;
- dimension-aware strategic position;
- group type/state/faction/source identity fields;
- composition/strength and movement-speed fields;
- cached waypoint-route representation and route cursor;
- deterministic NBT serialization/deserialization with future-schema rejection;
- `DrewCraftSavedData` schema migration that persists strategic groups;
- bounded coarse scheduler with explicit interval, groups-per-cycle, and catch-up cap;
- elapsed-time advancement along an already-cached route;
- no chunk loading, entity creation, Minecraft pathfinding, or route search in the scheduler;
- admin diagnostics sufficient to create/list/inspect a test group and force a bounded simulation step;
- focused tests for route movement, catch-up clamping, arrival, and persistence round trip;
- DrewCraft mod compile/unit CI green.

**Not part of BP1:** terrain-aware route generation. BP1 may use an explicitly supplied/cached waypoint route. BP2 owns route computation.

## BP2 — Coarse terrain routing + ETA + unloaded travel proof

**Goal:** turn destinations into bounded cached routes without live global world simulation.

Required before stopping:

- coarse terrain-cost abstraction/cache that never invokes Terrain Diffusion generation at route time;
- bounded A*/Dijkstra-equivalent route engine;
- deterministic route cache and event-driven invalidation;
- explicit unknown/blocked/water/difficult/normal cost policy;
- ETA from remaining cached route and effective speed;
- route/search timing diagnostics and hard node/work bounds;
- admin destination/route/ETA commands;
- one test group can travel thousands of blocks strategically with relevant chunks unloaded;
- save/restart preserves route cursor/progress;
- no continuous path recomputation;
- unit/integration evidence green.

## BP3 — Transactional materialization + casualty reconciliation

**Goal:** safely transform one strategic group into real mobs near players and back again.

Required before stopping:

- encounter UUID/state machine;
- duplication-safe materialization transaction;
- durable entity tags mapping entities to group/encounter;
- bounded active-entity/wave budget;
- idempotent casualty accounting;
- dematerialization/reconciliation;
- recovery from restart in transitional/materialized states;
- canonical `100 -> fight -> 63 -> unload -> restart -> 63` proof;
- two-player simultaneous approach cannot duplicate encounter.

## BP4 — Hostile sources + permanent clearing

**Goal:** make hostile structures persistent strategic producers.

Required before stopping:

- stable `SourceRecord` registry tied to real structure geography;
- idempotent discovery/indexing;
- Source Core binding and authoritative clear transaction;
- deterministic launch budget/cooldown;
- source launches real strategic groups through BP1/BP2 kernel;
- cleared source survives unload/restart and cannot launch again;
- already-launched forces remain real after source clearing.

## BP5 — Factions, patrols, hordes, raids, and large armies

**Goal:** expand from one generic group to the V1 hostile strategic population system.

Required before stopping:

- data-driven faction/group templates;
- patrol, roaming horde/warband, raid, army, and reinforcement roles;
- multiple meaningful hostile compositions;
- bounded wave materialization for large strength values;
- non-omniscient/explainable target-knowledge rule;
- persistent casualties/mission state across unload/restart;
- representative large-army scenario passes without requiring all represented units to be loaded.

## BP6 — Path-first bounded siege planner

**Goal:** make fortifications matter without indiscriminate griefing.

Required before stopping:

- ordinary navigation attempted first;
- siege planner runs only for loaded blocked encounters;
- bounded/cached breach planning;
- siege-capable roles only;
- block scoring for route utility, hardness, gates/doors/weaker barriers, and protected tags;
- constrained breach corridor;
- open-gate scenario uses gate;
- sealed-fort scenario chooses useful breach;
- irrelevant decorative blocks are not selected merely because they are nearby.

## BP7 — Strategic herds + local-spawn coexistence

**Goal:** finish the strategic ecology layer without replacing Minecraft ecology.

Required before stopping:

- persistent wild-herd records using the shared kernel;
- herd materialization/dematerialization and restart safety;
- named/domesticated/leashed/penned/player-owned animals excluded from silent strategic absorption;
- ordinary night/cave/local hostile spawning still works;
- mob farms and ordinary spawners still work;
- strategic caps do not accidentally suppress normal ecology.

## BP8 — Production world + deployment + release/launcher convergence

**Goal:** make the complete game reproducible and installable on real infrastructure.

This breakpoint may consume parallel work accumulated earlier.

Required before stopping:

- production Terrain Diffusion World Scale 2 candidate selected from measured pregeneration experiments;
- world generation metadata/archive/checksum/restore proof;
- production host decision after ARM/native/performance benchmark;
- immutable client/server release artifacts and version/protocol manifest;
- staged server updater with backup/health-check/rollback rules;
- off-host backup/restore drill;
- Windows one-click install/update/repair path;
- Apple Silicon macOS one-click install/update/repair path;
- two clean clients converge to the same exact pack and join the server.

## BP9 — Cross-system scale, failure, and recovery hardening

**Goal:** prove DrewCraft behaves as one game rather than a set of isolated features.

Required before stopping:

- weather/radar/aviation/transport scenario;
- hostile-source -> unloaded march -> materialization -> siege -> casualties -> source clear scenario;
- herd scenario;
- radar power loss/recovery scenario;
- worst-normal-load performance test with MSPT p50/p95/p99, memory/GC, network, entity counts, scheduler/route/siege/radar timings;
- crash/restart tests around materialization, combat, source clearing, siege, and updates;
- persistence schema migration test;
- backup restore on representative state;
- no unresolved correctness/performance blocker for release candidate.

## BP10 — V1 release candidate + hard acceptance

**Goal:** freeze one exact build and prove it is DrewCraft V1.

Required before stopping:

- dependency/worldgen freeze;
- exact RC artifacts and production world identity;
- Windows + Apple Silicon clean install tests;
- multiplayer soak;
- update/repair/restore matrix;
- final radar visual/terrain acceptance;
- final aviation-weather acceptance;
- final strategic source/army/siege/herd/local-spawn acceptance;
- production performance acceptable;
- website download buttons point at real distributable artifacts;
- no V1-blocking open defect;
- tag `1.0.0` only after the exact RC passes.

## Stop/report protocol

At every breakpoint report:

1. breakpoint reached;
2. implementation summary;
3. acceptance/tests and CI run IDs;
4. unresolved non-blocking limitations explicitly deferred;
5. current `main` commit SHA;
6. next breakpoint and its one-sentence goal.

Do not continue into the next breakpoint until the user says **"go"** again.