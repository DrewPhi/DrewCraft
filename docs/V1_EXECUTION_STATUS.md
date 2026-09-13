# DrewCraft V1 Execution Status

**Last updated:** 2026-09-12  
**Current phase:** **BP1-BP5 strategic population system complete -> BP6 siege planner next**  
**Current breakpoint handoff:** `docs/CURRENT_BREAKPOINT.md`  
**Breakpoint protocol:** `docs/DEVELOPMENT_BREAKPOINTS.md`

This is the live execution-state overlay for DrewCraft V1. `docs/CURRENT_BREAKPOINT.md` is the exact stop/resume handoff for user-driven **"go"** sessions. `docs/V1_REMAINING_EXECUTION_PLAN.md` remains the detailed path to `1.0.0`.

## Certified platform and integration profile

DrewCraft V1 remains pinned to Minecraft **1.21.1**, NeoForge **21.1.250**, and Java **21**.

The current candidate profile contains **34 dependencies total**: 33 exact provider artifacts plus one exact Terrain Diffusion Plus source build. The earlier dedicated-server baseline remains run **34704011609**; current provider acquisition/hash validation passed in **34724313143** and the 34-dependency manifest graph passed in **34724313201**.

Subsystem authorities remain:

- terrain/world: **Terrain Diffusion Plus**;
- weather: **Project Atmosphere**;
- industry/kinetic power: **Create**;
- physical V1 ground radar: **Create: Radars**;
- vehicles/aircraft: **Immersive Vehicles / MTS**;
- distant terrain: **Distant Horizons**;
- pregeneration: **Chunky**.

Environment/aviation/radar integration through **8B** is implemented at development scope. Final representative client/world acceptance remains part of BP9/BP10.

## Strategic-world progress

### BP1 — persistence + coarse simulation — PASS

Persistent `StrategicGroup`s, stable IDs, composition/strength/state, cached waypoint routes, bounded elapsed-time scheduling, admin diagnostics, and no distant entity/chunk simulation.

### BP2 — coarse terrain routing + ETA + unloaded travel — PASS

64×64 default coarse cells, explicit terrain costs, bounded deterministic A*, cached weighted routes, event-driven invalidation, ETA, no force-loaded terrain, and a 10,000-block save/restart unloaded journey. Evidence: **34726835776**, **34726857058**.

### BP3 — transactional materialization + casualties — PASS

One durable encounter per group, loaded-chunk-only entity materialization, durable entity tags, idempotent casualties, restart recovery, stale-entity rejection, and bounded tactical waves. Defaults remain **64 active/encounter**, **128 new strategic entities/materialization cycle**, **32 encounters/cycle**.

Canonical proof: `100 -> 64 active -> kill 37 -> 63 strategic -> unload/restart -> 63`. Evidence: **34727614866**, concurrency proof **34727505486**.

### BP4 — hostile sources + permanent clearing — PASS

Persistent generated-geography `SourceRecord`s, real Source Core, mining/explosion clearing, crash-durable permanent neutralization, bounded source production, clear-versus-launch race safety, and generated-structure registration seam without global scans or force loading.

Source Core also now has an intentional magenta/black checkerboard V1 texture and broadcasts a server chat message when a real source is permanently deactivated.

Final BP4 core evidence: **34728862438**. Source Core polish evidence: **34729284337**.

### BP5 — factions / patrols / hordes / raids / armies / reinforcements — PASS

Detailed contract: `docs/HOSTILE_FORCES_V1.md`.

Implemented:

- versioned JSON-backed hostile faction/force catalog;
- V1 profiles for `drewcraft:test_hostile`, `drewcraft:undead`, and `drewcraft:raiders`;
- `PATROL`, `HORDE`, `RAID`, `ARMY`, and `REINFORCEMENT` templates;
- source-class eligibility, strength multipliers, target policy, travel range, and weighted entity composition as data rather than scheduler branches;
- deterministic exact composition allocation whose counts always equal represented strategic strength;
- variable-size source production with exact population-budget debit under the same synchronized authority as Source Core clearing;
- `StrategicGroup` schema **3** with persisted `StrategicMission`;
- mission template ID, target, issue time, target-knowledge category, and human-readable knowledge reason;
- schema-1/schema-2 group migration to `LEGACY_ROUTE` mission state;
- explicit non-omniscient target policy using `SOURCE_GEOGRAPHY`, `SCOUTED_REGION`, or `ALLIED_SOURCE_LOCATION` rather than hidden player/base queries;
- deterministic scouted expedition objectives with no nearest-player lookup;
- large represented armies reusing BP3's unchanged tactical cap/wave system;
- persistent mission, casualties, and encounter state across restart.

Representative automated scenario:

```text
stronghold source budget = 384
army strength = 256
source budget after commit = 128
materialized tactical cap = 64
37 deaths -> 219 strategic survivors / 27 active survivors
next wave = exactly 37
save/restart -> role + mission + target + 219 population + 27 active reservations preserved
```

No test or runtime rule requires all 256 represented units to be loaded as Minecraft entities.

Final BP5 code/test head **`c8bb18e8e6af986b614db08235c0d8b4202926a9`**; final DrewCraft mod CI **34729884759 — SUCCESS**. Representative large-army proof **34729684064 — SUCCESS**; variable-strength source transaction **34729641645 — SUCCESS**.

## Strategic performance invariant

> **Keep the world abstract while nobody is looking; materialize only what players can interact with; cache expensive decisions; persist every important consequence.**

Specifically:

- distant groups/sources do not keep chunks loaded;
- distant groups do not run Minecraft AI/pathfinding;
- source production iterates bounded persistent records rather than world chunks;
- coarse routes are cached and not recomputed continuously;
- represented army strength is independent of loaded tactical entity count;
- only player-near tactical subsets exist as entities;
- mission targets are persistent/explainable rather than repeatedly rediscovered through hidden global queries;
- materialization retains encounter-count, per-encounter entity, and global spawn-work bounds;
- siege planning will first appear in BP6 and only for loaded blocked encounters.

## Remaining critical path

```text
DONE BP1 strategic persistence + coarse scheduler
DONE BP2 coarse routing + ETA + unloaded travel
DONE BP3 transactional materialization + casualties
DONE BP4 hostile sources + permanent clearing
DONE BP5 factions / patrols / hordes / raids / armies / reinforcements
→ NEXT BP6 bounded path-first siege planner
→ BP7 strategic herds + local-spawn coexistence
→ BP8 production world / deployment / release / launcher convergence
→ BP9 cross-system scale / failure / recovery hardening
→ BP10 release candidate + hard acceptance
→ 1.0.0
```

Production-world/pregeneration, host benchmarking, immutable release artifacts, server updater/backups, and Windows/macOS launcher work remain parallel tracks and converge before the RC freeze.

## Gate status

| Gate | State | Evidence / remaining condition |
| --- | --- | --- |
| Reproducible manifest/resolver | **PASS** | run 34724313201 |
| Provider artifact acquisition/hashes | **PASS** | run 34724313143 |
| Original dedicated-server baseline | **PASS** | run 34704011609 |
| Environment/adapters through 8A | **PASS: development scope** | compile/unit evidence |
| Physical Create radar + weather integration | **DONE: code/manifest/hash scope** | final visual acceptance later |
| BP1 strategic persistence/scheduler | **PASS** | focused CI |
| BP2 routing/ETA/unloaded travel | **PASS** | 34726835776 + 34726857058 |
| BP3 materialization/casualties | **PASS** | 34727614866 + 34727505486 |
| BP4 hostile sources | **PASS** | 34728862438; polish 34729284337 |
| BP5 hostile population breadth | **PASS** | 34729884759; large-army proof 34729684064 |
| BP6 siege | **NEXT** | bounded path-first breach planner |
| BP7 herds/local spawning | **BLOCKED ON BP6** | ecology/coexistence proof |
| Production world/pregen/restore | **OPEN / PARALLEL** | structure/core/faction binding by BP8 |
| ARM/production host benchmark | **OPEN / PARALLEL** | representative world required |
| Release/server updater | **OPEN / PARALLEL** | converge by BP8 |
| Windows/macOS launcher | **OPEN / PARALLEL** | converge by BP8 |
| V1 full-stack acceptance | **OPEN** | BP9-BP10 |

## Immediate next sequence — BP6

On the next **"go"**, follow `docs/CURRENT_BREAKPOINT.md` and the BP6 definition in `docs/DEVELOPMENT_BREAKPOINTS.md`.

BP6 must remain path-first and local: ordinary navigation before breaching; siege planning only for loaded blocked encounters; bounded/cached breach search; siege-capable units only; gates/doors/useful weak barriers and block hardness considered; protected/decorative blocks avoided; open gates used; sealed forts breached through a deliberate useful corridor.

Do **not** begin BP7 strategic herds/local-spawn coexistence until BP6 is reached, reported, and the user says **"go"** again.
