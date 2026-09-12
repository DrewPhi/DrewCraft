# DrewCraft V1 Execution Status

**Last updated:** 2026-09-12  
**Current phase:** environment/aviation/radar integration head implemented -> strategic-world kernel next  
**Canonical contracts:** `docs/v_1_requirements.md`, `docs/v_1_development_tree.md`, and `docs/RADAR_V1.md`

This file is the live execution-state overlay for DrewCraft V1. The requirements document defines the V1 contract; the development tree defines dependency order; this file records which gates have actually passed and what work is next.

## Certified base snapshot and current integration profile

The Minecraft 1.21.1 / NeoForge 21.1.250 / Java 21 baseline dedicated-server certification was performed on the earlier **31-dependency** snapshot: 30 provider artifacts plus one exact Terrain Diffusion Plus source build.

Baseline certification evidence remains GitHub Actions run **34704011609**, job **103580655867**, commit `4259d0ccf0e10f34298f744c42b253a1c08603d0`, success. It proved fresh Terrain Diffusion world boot, clean shutdown, same-world restart, second shutdown and fatal-log scan. The successful full verified-profile reconstruction was run **34702233400**.

The current V1 integration profile adds one intentionally selected gameplay/integration dependency: **Create: Radars 0.4.9.4 (1.21.1 NeoForge)**. Therefore the current candidate profile is **32 dependencies total** before later gameplay/source-profile promotion. This addition does not erase the earlier certification evidence, but it does mean the final V1 full-stack acceptance run must re-certify the complete current profile.

Core authorities remain:

- Terrain/world authority: **Terrain Diffusion Plus**;
- weather authority: **Project Atmosphere**;
- industry/kinetic power: **Create**;
- physical ground radar frontend: **Create: Radars**;
- vehicles/aircraft: **Immersive Vehicles / MTS**;
- distant terrain: **Distant Horizons**;
- pregeneration: **Chunky**.

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

### Step 8B — physical ground radar + weather display integration — DONE at code/manifest scope

V1 uses the official **Create: Radars 0.4.9.4** physical ground radar instead of custom DrewCraft dish/controller/display blocks. The pack manifest pins Modrinth project `BLu2Yqfq`, version `AntNFNAx`.

DrewCraft adds a separate fail-closed compatibility layer:

- Create: Radars owns dish construction, Create-powered operation, hardware range, native contacts, filters, networks and monitors;
- a server-authoritative 9x9 Project Atmosphere weather product is cached for 20 ticks per radar/range;
- the Create radar's own range defines the weather product radius, so larger dish constructions naturally expand potential weather coverage;
- Terrain Diffusion realized terrain masks individual weather beams, so radar elevation/site selection affects usable coverage;
- the compact product piggybacks on Create: Radars' existing monitor block-entity sync rather than adding per-render/per-display scans;
- the physical monitor and full-screen Create monitor render weather below native contact tracks;
- the full-screen view includes wind speed/direction and temperature when the Atmosphere API supplies them;
- Project Atmosphere's existing handheld Weather Radar is retained unchanged for pilots/explorers;
- MTS cockpit radar and dedicated airborne traffic radar are explicitly deferred to V1.1+.

`docs/RADAR_V1.md` is the acceptance contract. The ordinary DrewCraft CI validates code/unit shape; live dish/power/monitor/terrain/weather behavior is reserved for the final representative full-stack acceptance run, consistent with the post-baseline CI policy.

## CI policy after baseline certification

Until V1 is substantially complete:

- use manifest/schema/unit/compile/targeted tests on ordinary commits;
- do not automatically rerun the expensive full Terrain Diffusion fresh-world smoke for bridge development;
- do not Chunky-pregenerate production scale in GitHub Actions;
- repeat the full-stack boot at V1 acceptance or if a base/platform change creates a blocking compatibility question;
- run the final representative acceptance locally/on dedicated hardware so clients, in-world behavior, logs and `spark` profiling can be inspected.

## Gate status

| Gate | State | Evidence / remaining condition |
| --- | --- | --- |
| Reproducible manifest/resolver | **PASS** | Deterministic profile tooling established; current profile includes pinned Create: Radars candidate |
| Original 31-dependency dedicated-server baseline | **PASS** | Run 34704011609 |
| Current 32-dependency final full-stack re-certification | **OPEN FOR FINAL ACCEPTANCE** | Includes Create: Radars addition |
| DrewCraft mod scaffold + persistence | **PASS** | Module and cheap CI established |
| TD+ realized-world adapter | **PASS: compile/unit scope** | No force-load/inference query path |
| Project Atmosphere adapter | **PASS: compile/unit scope** | Public snapshot, fail-closed boundary |
| Create kinetic bridge | **PASS: compile/unit scope** | Step 6 implemented |
| MTS observation | **PASS: compile/unit scope** | Step 7A implemented |
| Aviation/weather physics | **PASS: compile/unit scope** | Step 7B implemented; final in-game observation deferred |
| Radar sensing engine | **PASS: compile/unit scope** | Step 8A implemented |
| Physical ground radar/weather monitor integration | **DONE: code/manifest scope** | Step 8B implemented; `docs/RADAR_V1.md` defines final in-game acceptance |
| MTS cockpit radar | **POST-V1** | V1 pilots use Atmosphere handheld + ATC communication |
| Strategic-world kernel | **NEXT** | Persistent IDs, coarse clock, routes/ETA, materialization transaction |
| Production world/pregen/restore | **OPEN** | Representative-world gate |
| ARM/production host benchmark | **OPEN** | Benchmark after representative world exists |
| Launcher/release/deployment | **OPEN** | Build against immutable release contract |
| V1 full-stack acceptance | **OPEN** | Current profile, local/host/client/soak/restart/profiling gate |

## Immediate next sequence

**Step 9 / strategic-world kernel is now the implementation head.** Start with the smallest restart-safe unloaded `StrategicGroup` proof: stable IDs/schema, coarse clock/catch-up bounds, coarse terrain-aware routing and ETA, then the materialization/dematerialization transaction. Do not jump directly to army/siege/herd breadth before persistence and reconciliation are correct.
