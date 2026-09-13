# DrewCraft V1 Execution Status

**Last updated:** 2026-09-12  
**Current phase:** **BP1-BP4 strategic foundation complete -> BP5 hostile population breadth next**  
**Current breakpoint handoff:** `docs/CURRENT_BREAKPOINT.md`  
**Breakpoint protocol:** `docs/DEVELOPMENT_BREAKPOINTS.md`

This file is the live execution-state overlay for DrewCraft V1. `docs/CURRENT_BREAKPOINT.md` is the exact stop/resume handoff for user-driven **"go"** sessions. `docs/V1_REMAINING_EXECUTION_PLAN.md` remains the detailed path to `1.0.0`.

## Certified platform and integration profile

DrewCraft V1 remains pinned to Minecraft **1.21.1**, NeoForge **21.1.250**, and Java **21**.

The current candidate profile contains **34 dependencies total**: 33 exact provider artifacts plus one exact Terrain Diffusion Plus source build. The earlier dedicated-server baseline remains run **34704011609**; current provider acquisition/hash validation passed in **34724313143** and the 34-dependency manifest graph passed in **34724313201**.

Core subsystem authorities remain:

- terrain/world: **Terrain Diffusion Plus**;
- weather: **Project Atmosphere**;
- industry/kinetic power: **Create**;
- physical V1 ground radar: **Create: Radars**;
- vehicles/aircraft: **Immersive Vehicles / MTS**;
- distant terrain: **Distant Horizons**;
- pregeneration: **Chunky**.

## Environment / aviation / radar

Steps through **8B** are implemented at their development scopes:

- DrewCraft integration/service platform;
- Terrain Diffusion realized-world adapter;
- Project Atmosphere adapter;
- Create kinetic adapter;
- MTS observation;
- aviation/weather physics bridge;
- cached terrain-aware radar sensing;
- official Create: Radars physical ground radar + DrewCraft weather/terrain overlay.

V1 pilots use Project Atmosphere's existing handheld Weather Radar plus player ATC communication. Dedicated MTS cockpit radar remains V1.1+. Final representative client/world acceptance for radar and aviation remains part of BP9/BP10.

## Strategic-world progress

### BP1 — strategic persistence + coarse simulation substrate — PASS

Persistent strategic groups, stable UUIDs, composition/strength/state, cached waypoint routes, elapsed-time movement, schema migration, bounded coarse scheduling, and admin diagnostics are established. Distant groups are records rather than mobs and do not perform chunk loading, entity creation, Minecraft navigation, or route search.

### BP2 — coarse terrain routing + ETA + unloaded travel — PASS

BP2 established the 64×64 default coarse routing grid, explicit terrain costs, bounded deterministic A*, cached weighted routes, ETA, event/version-driven invalidation, persisted route progress, and realized-terrain capture without forced loading. A 10,000-block abstract journey survives mid-route save/reload and completes through the actual scheduler. Runs **34726835776** and **34726857058** passed.

### BP3 — transactional materialization + casualties — PASS

Detailed contract: `docs/STRATEGIC_MATERIALIZATION.md`.

Implemented:

- one durable encounter UUID per materialized group;
- `PREPARING / MATERIALIZED / RECONCILING / COMPLETE` lifecycle;
- real tactical entities only near players and in already-loaded chunks;
- durable group/encounter/type tags;
- synchronized duplication-safe materialization;
- idempotent casualty accounting;
- safe dematerialization and restart recovery;
- stale-entity rejection;
- per-encounter and global spawn bounds.

Default bounds: **64 active entities per encounter**, **128 new strategic entities per materialization cycle**, **32 encounters processed per cycle**.

Canonical proof passes: `100 -> 64 active -> kill 37 -> 63 strategic -> unload -> restart -> 63`. A true simultaneous two-thread reservation test proves one group cannot produce two encounters.

Final BP3 code/test head `974e2d25cdede7a5679340445bfc3d5471e36cd8`; CI **34727614866** passed.

### BP4 — hostile sources + permanent clearing — PASS

Detailed contract: `docs/STRATEGIC_SOURCES.md`; product clearing semantics: `docs/SOURCE_CORE_SPEC.md`.

Implemented:

- world persistence schema **4** with versioned `SourceRecord`s;
- stable source UUID derived from dimension + generated structure ID + deterministic structure anchor;
- idempotent generated-source discovery;
- fail-closed conflicting rediscovery and duplicate core binding;
- real `drewcraft:source_core` block with no BlockItem and piston-immovable behavior;
- player-break and actual-explosion clear hooks;
- synchronized, permanent, idempotent clear transaction;
- immediate SavedData flush for irreversible core clears;
- source production budgets, cooldowns, launch serials, and transaction generation counter;
- bounded persistent-record-only source scheduler with fair rotating cursor;
- defaults: 200-tick cadence, 16 sources inspected/cycle, 4 launches/cycle, 1200-tick route-failure backoff;
- BP2 bounded route planning for launched groups;
- route failure consumes no source population;
- clear-versus-launch race protection using captured source generation;
- already-committed groups survive source clearing and restart;
- cleared sources reject all subsequent launches, including after restart;
- `GeneratedSourceRegistration` seam for deterministic template/worldgen integration without chunk searching or force loading;
- `/drewcraft source create-test|list|inspect|clear|perf` diagnostics.

BP4 deliberately uses a minimal routed zombie `PATROL` as its production proof. BP5 owns faction/composition/role/target breadth.

Final BP4 code/test head **`188fff9583d917aeb44fd8802987f0b51604b178`**; DrewCraft mod CI **34728862438** passed the complete `test + build` suite. Focused persistence/schema runs **34728805083** and **34728787877** also passed.

Production-world boundary: the final pregeneration track still must select the real camp/fort/city/etc. templates, assign deterministic Source Core anchors, and call the already-implemented `GeneratedSourceRegistration` seam. No recurring live chunk/structure scan will be introduced.

## Strategic performance invariant

> **Keep the world abstract while nobody is looking; materialize only what players can interact with; cache expensive decisions; persist every important consequence.**

Specifically:

- distant groups and sources do not keep chunks loaded;
- distant groups do not run Minecraft AI/pathfinding;
- source production iterates bounded persistent records rather than world chunks;
- coarse routes are cached and not recomputed continuously;
- only player-near tactical subsets exist as entities;
- materialization has encounter-count, per-encounter entity, and global spawn-work bounds;
- siege planning will run only for loaded blocked encounters in BP6.

## Remaining critical path

```text
DONE BP1 strategic persistence + coarse scheduler
DONE BP2 coarse routing + ETA + unloaded travel
DONE BP3 transactional materialization + casualties
DONE BP4 hostile sources + permanent clearing
→ NEXT BP5 factions / patrols / hordes / raids / large armies
→ BP6 bounded path-first siege planner
→ BP7 strategic herds + local-spawn coexistence
→ BP8 production world / deployment / release / launcher convergence
→ BP9 cross-system scale / failure / recovery hardening
→ BP10 release candidate + hard acceptance
→ 1.0.0
```

Production-world/pregeneration, host benchmarking, immutable release artifacts, server updater/backups, and Windows/macOS launcher work may proceed in parallel and converge before the RC freeze.

## Gate status

| Gate | State | Evidence / remaining condition |
| --- | --- | --- |
| Reproducible manifest/resolver | **PASS** | 34-dependency graph; run 34724313201 |
| Provider artifact acquisition/hashes | **PASS** | 33 provider artifacts; run 34724313143 |
| Original dedicated-server baseline | **PASS** | run 34704011609 |
| Environment/adapters through 8A | **PASS: development scope** | compile/unit evidence established |
| Physical Create radar + weather integration | **DONE: code/manifest/hash scope** | final visual acceptance later |
| BP1 strategic persistence/scheduler | **PASS** | persistence/scheduler CI |
| BP2 routing/ETA/unloaded travel | **PASS** | runs 34726835776 + 34726857058 |
| BP3 materialization/casualties | **PASS** | run 34727614866; concurrency run 34727505486 |
| BP4 hostile sources | **PASS** | run 34728862438; source lifecycle/clear/launch tests green |
| BP5 hostile population breadth | **NEXT** | factions/templates/roles/targets/large-army proof |
| BP6 siege | **BLOCKED ON BP5** | bounded path-first breach planner |
| BP7 herds/local spawning | **BLOCKED ON BP6** | ecology/coexistence proof |
| Production world/pregen/restore | **OPEN / PARALLEL** | real source-template binding converges by BP8 |
| ARM/production host benchmark | **OPEN / PARALLEL** | representative world required |
| Release/server updater | **OPEN / PARALLEL** | converge by BP8 |
| Windows/macOS launcher | **OPEN / PARALLEL** | converge by BP8 |
| V1 full-stack acceptance | **OPEN** | BP9-BP10 |

## Immediate next sequence — BP5

On the next **"go"**, follow `docs/CURRENT_BREAKPOINT.md` and the BP5 definition in `docs/DEVELOPMENT_BREAKPOINTS.md`.

BP5 must add data-driven faction/group templates, patrol/horde/raid/army/reinforcement roles, several meaningful hostile compositions, explainable/non-omniscient targeting, persistent mission state, and a large-army proof that reuses BP3 bounded materialization rather than loading the entire represented force.

Do **not** begin BP6 siege planning until BP5 is reached, reported, and the user says **"go"** again.
