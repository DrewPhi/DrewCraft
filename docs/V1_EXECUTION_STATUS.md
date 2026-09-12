# DrewCraft V1 Execution Status

**Last updated:** 2026-09-12  
**Current phase:** environment/aviation/radar integration head implemented -> strategic-world kernel next  
**Canonical contracts:** `docs/v_1_requirements.md`, `docs/v_1_development_tree.md`, `docs/V1_REMAINING_EXECUTION_PLAN.md`, and the V1 radar scope amendment `docs/RADAR_V1.md`

This file is the live execution-state overlay for DrewCraft V1. The requirements document defines the overall V1 product contract; the development tree defines dependency order; `docs/V1_REMAINING_EXECUTION_PLAN.md` is the detailed post-8B plan from the current state through `1.0.0`; this file records which gates have actually passed and what work is next. For radar specifically, `docs/RADAR_V1.md` supersedes the older Stage 10 custom-hardware / V1 cockpit-radar implementation details: V1 uses Create: Radars for physical ground radar, Project Atmosphere's existing handheld Weather Radar for pilots/explorers, and defers an MTS cockpit radar instrument to V1.1+.

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
- the Create radar's own hardware range defines the weather product radius, so larger dish constructions naturally expand potential weather coverage;
- Terrain Diffusion realized terrain masks individual weather beams, so antenna elevation/site selection can affect usable coverage without forcing chunks or invoking terrain inference;
- unavailable/unrealized terrain is marked uncertain rather than fabricated;
- the compact product piggybacks on Create: Radars' existing monitor block-entity synchronization rather than adding per-render/per-display world scans;
- the physical monitor and full-screen Create monitor render weather below Create: Radars' native contact tracks;
- the full-screen view includes wind speed/direction and temperature when the Atmosphere API supplies them;
- Project Atmosphere's existing handheld Weather Radar is retained unchanged for pilots/explorers;
- MTS cockpit radar and dedicated airborne traffic radar are explicitly deferred to V1.1+;
- the compatibility boundary has no compile-time Create: Radars dependency and uses optional `@Pseudo` mixins/reflection so it fails closed instead of making unrelated DrewCraft code unloadable.

`docs/RADAR_V1.md` is the detailed acceptance contract. Automated code/manifest/hash validation is complete. The final representative client/world acceptance must still visually prove the physical Create monitor overlay, native contacts over weather, actual storm agreement, power-off recovery, and low-site versus high-site terrain coverage in the pregenerated world; those checks are intentionally part of the V1 full-stack acceptance rather than a synthetic unit test.

## Remaining V1 execution contract

`docs/V1_REMAINING_EXECUTION_PLAN.md` is now the detailed implementation order from this point to `1.0.0`.

Its most important strategic-performance invariant is:

> **Distant/unloaded groups are lightweight records with cached coarse routes and elapsed-time movement. They do not keep chunks loaded, run ordinary Minecraft AI, run siege planning, or recompute full paths continuously.**

Normal Minecraft pathfinding and siege planning occur only for bounded materialized entities near players. Large army strength may therefore represent hundreds of units while only a capped tactical subset exists as entities at one time.

The remaining critical path is:

```text
11 strategic persistence/scheduler/coarse routing/ETA
→ 12 transactional materialization + casualty reconciliation
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

The radar dependency addition is such a compatibility change, so current-profile verified-layout and dedicated-server smoke workflows were launched after the exact hashes were locked. Their result is compatibility evidence, not a substitute for the later physical-monitor/client acceptance described above.

## Gate status

| Gate | State | Evidence / remaining condition |
| --- | --- | --- |
| Reproducible manifest/resolver | **PASS** | 34-dependency graph validates; run 34724313201 |
| Provider artifact acquisition/hashes | **PASS** | 33 provider artifacts, zero hard failures; run 34724313143 |
| Original 31-dependency dedicated-server baseline | **PASS** | Run 34704011609 |
| Current 34-dependency verified layout | **RUNNING / FINALIZING** | Full-profile verification launched after radar dependency chain was pinned |
| Current 34-dependency dedicated-server smoke | **RUNNING / FINALIZING** | Fresh boot + restart compatibility test launched after radar dependency chain was pinned |
| DrewCraft mod scaffold + persistence | **PASS** | Module and cheap CI established |
| TD+ realized-world adapter | **PASS: compile/unit scope** | No force-load/inference query path |
| Project Atmosphere adapter | **PASS: compile/unit scope** | Public snapshot, fail-closed boundary |
| Create kinetic bridge | **PASS: compile/unit scope** | Step 6 implemented |
| MTS observation | **PASS: compile/unit scope** | Step 7A implemented |
| Aviation/weather physics | **PASS: compile/unit scope** | Step 7B implemented; final in-game observation deferred |
| Radar sensing engine | **PASS: compile/unit scope** | Step 8A implemented |
| Physical ground radar/weather monitor integration | **DONE: code/manifest/hash scope** | Step 8B implemented; mod CI + graph + provider hashes green; `docs/RADAR_V1.md` defines final in-game acceptance |
| MTS cockpit radar | **POST-V1** | V1 pilots use Atmosphere handheld + ATC communication |
| Strategic-world kernel | **NEXT** | Follow Stage 11 in `V1_REMAINING_EXECUTION_PLAN.md` |
| Production world/pregen/restore | **OPEN / PARALLEL** | Track A in remaining-plan document |
| ARM/production host benchmark | **OPEN / PARALLEL** | Track B after representative world exists |
| Release artifact/server updater | **OPEN / PARALLEL** | Tracks C-D |
| Windows/macOS launcher | **OPEN / PARALLEL** | Track E |
| V1 full-stack acceptance | **OPEN** | Stages 18-22 |

## Immediate next sequence

Follow `docs/V1_REMAINING_EXECUTION_PLAN.md` exactly unless a blocking discovery is documented.

The immediate coding queue is:

1. strategic persistence schema + stable IDs;
2. bounded strategic scheduler + elapsed-time/catch-up semantics;
3. coarse terrain-cost interface/cache;
4. cached route engine + ETA;
5. admin diagnostics + one fully unloaded moving-group proof;
6. only then begin the materialization/dematerialization transaction.

Do not jump directly to army content, source breadth, siege AI, or herds before the shared persistence/routing/materialization gates pass.
