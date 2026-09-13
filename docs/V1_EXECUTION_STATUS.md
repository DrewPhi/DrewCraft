# DrewCraft V1 Execution Status

**Last updated:** 2026-09-12  
**Current phase:** **Stage 11 strategic-world kernel / BP1-BP2 complete -> BP3 materialization next**  
**Current breakpoint handoff:** `docs/CURRENT_BREAKPOINT.md`  
**Breakpoint protocol:** `docs/DEVELOPMENT_BREAKPOINTS.md`  
**Canonical contracts:** `docs/v_1_requirements.md`, `docs/v_1_development_tree.md`, `docs/V1_REMAINING_EXECUTION_PLAN.md`, `docs/STRATEGIC_ROUTING.md`, and the V1 radar scope amendment `docs/RADAR_V1.md`

This file is the live execution-state overlay for DrewCraft V1. The requirements document defines the overall V1 product contract; the development tree defines dependency order; `docs/V1_REMAINING_EXECUTION_PLAN.md` is the detailed post-8B plan through `1.0.0`; `docs/CURRENT_BREAKPOINT.md` is the exact stop/resume handoff for "go" development sessions.

For radar specifically, `docs/RADAR_V1.md` supersedes the older Stage 10 custom-hardware / V1 cockpit-radar implementation details: V1 uses Create: Radars for physical ground radar, Project Atmosphere's existing handheld Weather Radar for pilots/explorers, and defers an MTS cockpit radar instrument to V1.1+.

## Certified base snapshot and current integration profile

The Minecraft 1.21.1 / NeoForge 21.1.250 / Java 21 baseline dedicated-server certification was performed on the earlier **31-dependency** snapshot: 30 provider artifacts plus one exact Terrain Diffusion Plus source build.

Baseline certification evidence remains GitHub Actions run **34704011609**, job **103580655867**, commit `4259d0ccf0e10f34298f744c42b253a1c08603d0`, success. It proved fresh Terrain Diffusion world boot, clean shutdown, same-world restart, second shutdown and fatal-log scan. The successful full verified-profile reconstruction was run **34702233400**.

The current V1 integration profile adds the complete physical-radar dependency chain:

- **Create: Radars 0.4.9.4** — Modrinth `BLu2Yqfq` / `AntNFNAx`;
- **Create Big Cannons 5.11.7** — required by Create: Radars;
- **Ritchie's Projectile Library 2.1.2** — required by Create Big Cannons.

Therefore the current candidate profile is **34 dependencies total**: **33 exact provider artifacts + the exact Terrain Diffusion Plus source build**. GitHub Actions provider acquisition/hash run **34724313143** completed successfully with zero hard failures, and all three radar-chain artifacts are SHA-256 pinned in `pack/manifest/candidate_hashes.yaml`.

Core authorities remain:

- Terrain/world authority: **Terrain Diffusion Plus**;
- weather authority: **Project Atmosphere**;
- industry/kinetic power: **Create**;
- physical ground radar frontend: **Create: Radars**;
- vehicles/aircraft: **Immersive Vehicles / MTS**;
- distant terrain: **Distant Horizons**;
- pregeneration: **Chunky**.

Create Big Cannons and Ritchie's Projectile Library enter V1 because they are required runtime dependencies of the selected radar frontend; their presence does not make cannon progression/balance part of Step 8B.

## DrewCraft integration-platform progress

### Steps 1-5 — DONE

The DrewCraft NeoForge integration mod, service contracts, fail-closed Terrain Diffusion and Project Atmosphere adapters, diagnostics, persistence/version boundaries and cheap compile/unit CI are established. Terrain sampling remains realized-world-only and never force-loads chunks or invokes neural inference. Atmosphere values not exposed by the selected upstream API remain unavailable rather than fabricated.

### Step 6 — Create kinetic bridge — DONE at compile/unit scope

`CreatePowerService` is the narrow read-only Create kinetic/stress adapter. DrewCraft does not invent a generic electrical layer.

### Step 7A — MTS observation — DONE at compile/unit scope

`MtsVehicleService` exposes DrewCraft-owned vehicle identity, position, velocity, orientation and aircraft classification through an isolated runtime binding.

### Step 7B — aviation/weather physics — DONE at compile/unit/mixin-shape scope

`MtsWeatherPhysicsBridge` and the narrow optional MTS physics mixin apply Project Atmosphere airflow in the aircraft force calculation while restoring the ground-relative frame afterward. Full representative in-game acceptance remains part of the final V1 integration run.

### Step 8A — cached terrain-aware radar engine — DONE at compile/unit scope

`RadarEngine` provides the bounded server-authoritative radar sensing/caching and Terrain Diffusion line-of-sight machinery established in commit `3ce5d4359919e646edf4b9e211d7fffb180c758e`.

### Step 8B — physical ground radar + weather display integration — DONE at code/manifest/hash scope

The main implementation is commit **`a78f00ea6a193b3e929ad3c2cf1dcde7b32dda3b`**. DrewCraft mod CI run **34724118761** passed `test` + `build`, pack-manifest validation run **34724313201** passed for the 34-dependency graph, and provider-hash run **34724313143** acquired and hashed all 33 provider artifacts with zero hard failures.

V1 uses the official **Create: Radars 0.4.9.4** physical ground radar instead of custom DrewCraft dish/controller/display blocks. DrewCraft adds a separate fail-closed compatibility layer:

- Create: Radars owns dish construction, Create-powered operation, hardware range, native contacts, filters, networks and monitors;
- a server-authoritative 9x9 Project Atmosphere weather product is cached for 20 ticks per radar/range;
- the Create radar's own hardware range defines the weather product radius;
- Terrain Diffusion realized terrain masks individual weather beams without forcing chunks or invoking terrain inference;
- unavailable/unrealized terrain is marked uncertain rather than fabricated;
- the compact product piggybacks on Create: Radars' existing monitor block-entity synchronization;
- the physical monitor and full-screen Create monitor render weather below native contact tracks;
- the full-screen view includes wind speed/direction and temperature when available;
- Project Atmosphere's existing handheld Weather Radar is retained unchanged;
- MTS cockpit radar and dedicated airborne traffic radar are V1.1+;
- optional `@Pseudo` mixins/reflection keep the compatibility boundary fail-closed.

`docs/RADAR_V1.md` is the detailed acceptance contract. Final representative client/world acceptance still needs to visually prove the physical monitor overlay, contacts over weather, storm agreement, power recovery, and low-site versus high-site terrain coverage.

### Stage 11 / BP1-BP2 — strategic-world kernel — DONE at compile/unit/runtime-wiring scope

Stage 11 now proves that distant strategic populations can exist and travel as **persistent lightweight records rather than loaded Minecraft mobs**.

BP1 established:

- stable strategic-group UUIDs and versioned persistence;
- continuous dimension-aware strategic positions;
- composition/strength/state/speed data;
- cached-route cursor/progress;
- bounded coarse scheduler with interval, group-count, CPU-time and catch-up budgets;
- elapsed-time route advancement with no chunk loading, entity creation or path search;
- admin diagnostics and focused persistence/scheduler tests.

BP2 added the route-generation half:

- configurable coarse routing cells, default **64×64 blocks**;
- explicit `ROAD`, `BRIDGE`, `NORMAL`, `UNKNOWN`, `DIFFICULT`, `WATER`, and `BLOCKED` costs;
- conservative `UNKNOWN` behavior instead of forced terrain generation;
- a versioned coarse terrain-cost map that does not query Minecraft world state during route search;
- bounded deterministic 8-neighbor A* with finite detour bounds and a hard expanded-node cap;
- no blocked-corner diagonal cuts;
- weighted route segments, so terrain affects both chosen route and travel time;
- ETA from remaining weighted route cost divided by effective group speed;
- LRU route-template cache keyed by endpoints/dimension/terrain-map version;
- event-driven cache invalidation rather than periodic global rerouting;
- solved routes persisted in each strategic group so restarts do not require A* to reconstruct an already-deployed route;
- optional already-loaded-terrain capture through the realized-world terrain service only;
- route/ETA/search-performance admin commands.

Acceptance evidence includes a **10,000-block strategic journey driven through the real coarse scheduler**, saved/reloaded mid-trip as a restart boundary, then continued to exact arrival with the route cursor, weighted costs and group identity preserved. The proof uses no Minecraft world, chunk or entity object. DrewCraft mod CI runs **34726835776** and **34726857058** passed; the latter includes the final route-schema migration tests. `docs/STRATEGIC_ROUTING.md` is the routing contract and `docs/CURRENT_BREAKPOINT.md` records the BP2 handoff.

Important production boundary: the routing engine is complete, but the final production terrain-cost index will be populated from the final pregenerated world/offline metadata. Live routing never triggers Terrain Diffusion generation. Unindexed territory remains explicitly `UNKNOWN` until indexed or safely captured from already-loaded realized terrain.

## Remaining V1 execution contract

The strategic-performance invariant remains:

> **Distant/unloaded groups are lightweight records with cached coarse routes and elapsed-time movement. They do not keep chunks loaded, run ordinary Minecraft AI, run siege planning, or recompute full paths continuously.**

Normal Minecraft pathfinding and siege planning occur only for bounded materialized entities near players. Large army strength may represent hundreds of units while only a capped tactical subset exists at once.

The remaining critical path is now:

```text
DONE 11 strategic persistence/scheduler/coarse routing/ETA
→ NEXT 12 transactional materialization + casualty reconciliation
→ 13 hostile sources + Source Core clearing
→ 14 factions/hordes/raids/large armies
→ 15 bounded path-first siege planner
→ 16 strategic wild herds
→ 17 local-spawn coexistence
→ 18 cross-system scenarios
→ 19 performance hardening
→ 20 crash/persistence/backup/recovery
→ 21 release-candidate freeze
→ 22 hard acceptance
→ 1.0.0
```

Production world/pregeneration, host/ARM benchmarking, immutable release artifacts, server updater/backups, and the Windows/macOS launcher proceed in parallel and converge before the RC freeze.

## CI policy after baseline certification

Until V1 is substantially complete:

- use manifest/schema/unit/compile/targeted tests on ordinary commits;
- do not Chunky-pregenerate production scale in GitHub Actions;
- repeat full-stack boot when a base/platform dependency change creates a real compatibility question and at V1 acceptance;
- run the final representative acceptance locally/on dedicated hardware so clients, in-world behavior, logs and `spark` profiling can be inspected.

## Gate status

| Gate | State | Evidence / remaining condition |
| --- | --- | --- |
| Reproducible manifest/resolver | **PASS** | 34-dependency graph validates; run 34724313201 |
| Provider artifact acquisition/hashes | **PASS** | 33 provider artifacts, zero hard failures; run 34724313143 |
| Original 31-dependency dedicated-server baseline | **PASS** | Run 34704011609 |
| Current 34-dependency final full-stack acceptance | **OPEN** | Representative server/client/world acceptance remains later |
| DrewCraft mod scaffold + persistence | **PASS** | Module and cheap CI established |
| TD+ realized-world adapter | **PASS: compile/unit scope** | No force-load/inference query path |
| Project Atmosphere adapter | **PASS: compile/unit scope** | Public snapshot, fail-closed boundary |
| Create kinetic bridge | **PASS: compile/unit scope** | Step 6 implemented |
| MTS observation | **PASS: compile/unit scope** | Step 7A implemented |
| Aviation/weather physics | **PASS: compile/unit scope** | Step 7B implemented; final in-game observation deferred |
| Radar sensing engine | **PASS: compile/unit scope** | Step 8A implemented |
| Physical ground radar/weather monitor integration | **DONE: code/manifest/hash scope** | Step 8B implemented; final visual acceptance later |
| Strategic-world kernel | **PASS: compile/unit/runtime-wiring scope** | BP1+BP2; 10,000-block scheduler/restart proof; runs 34726835776 + 34726857058 |
| Materialization + casualty reconciliation | **NEXT — BP3** | Encounter transaction, bounded entities, idempotent casualties, restart recovery |
| Hostile sources | **BLOCKED ON BP3** | BP4 |
| Army/faction breadth | **BLOCKED ON BP4** | BP5 |
| Siege planner | **BLOCKED ON BP5** | BP6 |
| Strategic herds/local-spawn coexistence | **BLOCKED ON BP6** | BP7 |
| Production world/pregen/restore | **OPEN / PARALLEL** | Track A in remaining-plan document |
| ARM/production host benchmark | **OPEN / PARALLEL** | Track B after representative world exists |
| Release artifact/server updater | **OPEN / PARALLEL** | Tracks C-D |
| Windows/macOS launcher | **OPEN / PARALLEL** | Track E |
| V1 full-stack acceptance | **OPEN** | BP8-BP10 / Stages 18-22 |

## Immediate next sequence — BP3

On the next **"go"**, follow `docs/CURRENT_BREAKPOINT.md` and stop when BP3 passes.

BP3 implementation order:

1. persistent encounter UUID and explicit materialization state machine;
2. atomic/duplication-safe strategic → tactical transition;
3. durable entity identity mapping to `groupId` + `encounterId`;
4. bounded active-entity and wave budgets;
5. idempotent casualty accounting;
6. safe dematerialization/reconciliation back to strategic state;
7. restart recovery from `MATERIALIZING`, `MATERIALIZED`, and `DEMATERIALIZING` states;
8. canonical `100 → fight → 63 → unload → restart → 63` proof;
9. simultaneous two-player materialization cannot duplicate the encounter.

Do not begin hostile-source breadth, army content, siege AI, or herds until BP3 passes and the user says **"go"** again.
