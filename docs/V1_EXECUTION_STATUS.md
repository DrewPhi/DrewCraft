# DrewCraft V1 Execution Status

**Last updated:** 2026-09-12  
**Current phase:** **Strategic substrate + transactional materialization complete -> BP4 hostile sources next**  
**Current breakpoint handoff:** `docs/CURRENT_BREAKPOINT.md`  
**Breakpoint protocol:** `docs/DEVELOPMENT_BREAKPOINTS.md`

This file is the live execution-state overlay for DrewCraft V1. `docs/CURRENT_BREAKPOINT.md` is the exact stop/resume handoff for user-driven **"go"** sessions. `docs/V1_REMAINING_EXECUTION_PLAN.md` remains the detailed path to `1.0.0`.

## Certified platform and integration profile

DrewCraft V1 remains pinned to:

- Minecraft **1.21.1**;
- NeoForge **21.1.250**;
- Java **21**;
- **34 dependencies total** in the current candidate profile: 33 exact provider artifacts + one exact Terrain Diffusion Plus source build.

The earlier 31-dependency dedicated-server baseline certification remains GitHub Actions run **34704011609**. Provider acquisition/hash validation for the current 33 provider artifacts passed in run **34724313143**, and the 34-dependency manifest graph passed in run **34724313201**.

Core subsystem authorities remain:

- terrain/world: **Terrain Diffusion Plus**;
- weather: **Project Atmosphere**;
- industry/kinetic power: **Create**;
- physical V1 ground radar: **Create: Radars**;
- vehicles/aircraft: **Immersive Vehicles / MTS**;
- distant terrain: **Distant Horizons**;
- pregeneration: **Chunky**.

## Environment / aviation / radar progress

Steps through **8B** are implemented at their documented development scopes:

- DrewCraft integration/service platform;
- Terrain Diffusion realized-world adapter;
- Project Atmosphere adapter;
- Create kinetic adapter;
- MTS observation;
- aviation/weather physics bridge;
- cached terrain-aware radar sensing;
- official Create: Radars physical ground radar + DrewCraft weather/terrain overlay integration.

V1 pilots use Project Atmosphere's existing handheld Weather Radar plus player ATC communication. Dedicated MTS cockpit radar remains V1.1+.

Final representative client/world acceptance for radar and aviation remains part of the later full-stack release cycle.

## Strategic-world progress

### BP1 — strategic persistence + coarse simulation substrate — PASS

BP1 established persistent `StrategicGroup` records, stable UUIDs, composition/strength/state, cached routes, elapsed-time movement, schema migration, a bounded coarse scheduler, and admin diagnostics.

Distant populations are records, not mobs. The scheduler performs no chunk loading, entity creation, Minecraft navigation, or route search.

### BP2 — coarse terrain routing + ETA + unloaded travel proof — PASS

BP2 established:

- configurable coarse strategic cells, default 64×64 blocks;
- explicit `ROAD`, `BRIDGE`, `NORMAL`, `UNKNOWN`, `DIFFICULT`, `WATER`, and `BLOCKED` traversal policy;
- bounded deterministic A* with finite detour and expanded-node bounds;
- weighted cached routes and terrain-sensitive ETA;
- event/version-driven route-cache invalidation rather than periodic global rerouting;
- persisted solved routes/cursors across restart;
- realized-terrain capture that never force-loads terrain.

Acceptance includes a **10,000-block unloaded strategic journey**, saved/reloaded mid-route and completed through the actual coarse scheduler. Runs **34726835776** and **34726857058** passed.

### BP3 — transactional materialization + casualty reconciliation — PASS

BP3 establishes the V1 strategic ↔ tactical ownership transaction. The detailed contract is `docs/STRATEGIC_MATERIALIZATION.md`.

Implemented:

- persistent encounter UUID + `PREPARING` / `MATERIALIZED` / `RECONCILING` / `COMPLETE` lifecycle;
- `DrewCraftSavedData` schema **3** with encounter persistence and schema-2 migration;
- atomic one-encounter-per-group reservation;
- real NeoForge entity materialization only near players and only in already-loaded chunks;
- durable entity tags carrying group UUID, encounter UUID, and strategic entity type;
- entity UUID reservation committed before `addFreshEntity()` join handling;
- stale tagged-entity rejection after reconciliation;
- idempotent death/casualty accounting;
- survivor dematerialization without false casualties;
- restart recovery for interrupted transitions;
- persistent MATERIALIZED encounter authority across restart;
- safe recovery of reserved entity UUIDs that never actually return after a crash;
- fail-closed load validation for missing/duplicate/inconsistent encounter ownership;
- bounded wave backfill from surviving strategic reserve.

Default tactical bounds are intentionally conservative:

- 20-tick materialization cadence;
- 160-block materialization radius;
- 224-block dematerialization radius;
- 200-tick dematerialization grace;
- **64 active entities per encounter**;
- **128 successful new strategic entities globally per materialization cycle**;
- **32 encounter records processed per cycle**.

The central population invariant is:

> **Materialization never subtracts population. Only an idempotently confirmed tactical death reduces strategic strength.**

The canonical automated proof passes:

```text
100 strategic units
→ one encounter reserved
→ 64 tactical entities represented
→ 37 confirmed deaths
→ strategic strength = 63
→ duplicate death callbacks do nothing
→ only 36 units remain eligible to backfill the 27 active survivors
→ encounter dematerializes
→ save / restart
→ strategic strength remains exactly 63
```

A real two-thread barrier test also proves simultaneous callers cannot create two encounters for one group.

BP3 final code/test head: **`974e2d25cdede7a5679340445bfc3d5471e36cd8`**. DrewCraft mod CI run **34727614866** passed the complete `test + build` suite. Simultaneous-reservation proof run **34727505486** also passed.

## Strategic performance invariant

> **Keep the world abstract while nobody is looking; materialize only what players can interact with; cache expensive decisions; persist every important consequence.**

Specifically:

- distant groups do not keep chunks loaded;
- distant groups do not run Minecraft AI/pathfinding;
- coarse routes are cached and not recomputed continuously;
- only player-near tactical subsets exist as entities;
- materialization has encounter-count, per-encounter entity, and global spawn-work bounds;
- siege planning will run only for loaded blocked encounters in BP6.

## Remaining critical path

```text
DONE BP1 strategic persistence + coarse scheduler
DONE BP2 coarse routing + ETA + unloaded travel
DONE BP3 transactional materialization + casualties
→ NEXT BP4 hostile sources + permanent clearing
→ BP5 factions / patrols / hordes / raids / large armies
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
| BP1 strategic persistence/scheduler | **PASS** | persistence/scheduler tests + CI |
| BP2 routing/ETA/unloaded travel | **PASS** | runs 34726835776 + 34726857058 |
| BP3 materialization/casualties | **PASS** | run 34727614866; concurrency run 34727505486 |
| BP4 hostile sources | **NEXT** | source registry, Source Core, launch/clear permanence |
| BP5 hostile population breadth | **BLOCKED ON BP4** | faction/group templates + armies |
| BP6 siege | **BLOCKED ON BP5** | bounded path-first breach planner |
| BP7 herds/local spawning | **BLOCKED ON BP6** | ecology/coexistence proof |
| Production world/pregen/restore | **OPEN / PARALLEL** | converge by BP8 |
| ARM/production host benchmark | **OPEN / PARALLEL** | representative world required |
| Release/server updater | **OPEN / PARALLEL** | converge by BP8 |
| Windows/macOS launcher | **OPEN / PARALLEL** | converge by BP8 |
| V1 full-stack acceptance | **OPEN** | BP9-BP10 |

## Immediate next sequence — BP4

On the next **"go"**, follow `docs/CURRENT_BREAKPOINT.md`, `docs/SOURCE_CORE_SPEC.md`, and the BP4 definition in `docs/DEVELOPMENT_BREAKPOINTS.md`.

BP4 must prove:

1. stable persistent `SourceRecord` identities tied to generated geography;
2. idempotent source discovery/indexing;
3. Source Core binding with authoritative clear state in SavedData;
4. deterministic source launch budget/cooldown;
5. launched forces use the existing BP1/BP2/BP3 kernel;
6. source clearing survives unload/restart permanently;
7. a cleared source cannot launch another group;
8. groups already committed before clearing remain real populations.

Do **not** begin BP5 faction/horde/army breadth until BP4 is reached, reported, and the user says **"go"** again.
