# DrewCraft V1 Execution Status

**Last updated:** 2026-09-12  
**Current phase:** certified base stack -> DrewCraft integration platform  
**Canonical contracts:** `docs/v_1_requirements.md` and `docs/v_1_development_tree.md`

This document is the live execution-state overlay for DrewCraft V1. The requirements document defines what V1 must contain; the development tree defines dependency order; this file records which gates have actually passed, the evidence for those claims, and the next implementation work.

## Current state

The reproducible Minecraft 1.21.1 / NeoForge / Java 21 base is now **certified for V1 integration development**.

The exact `stage2_base_performance` dependency graph resolves and verifies successfully, and the resulting dedicated server has created a brand-new Terrain Diffusion Plus world, reached normal server readiness, stopped cleanly, restarted the same world, reached readiness again, stopped cleanly again, and passed the workflow fatal-error scan.

This is the point at which DrewCraft stops selecting more base mods and starts integrating the chosen systems.

### What is frozen now

For V1 integration work, treat the current base profile as frozen unless a blocking defect makes a dependency change unavoidable.

- Minecraft: **1.21.1**
- Loader: **NeoForge 21.1.250**
- Java: **21**
- Base profile: `stage2_base_performance`
- Dependency graph: **31 total dependencies**
  - **30 provider artifacts** with exact provider identities/hashes
  - **1 source build:** Terrain Diffusion Plus from its exact pinned source commit/build recipe
- Terrain/world authority: **Terrain Diffusion Plus**
- Weather authority: **Project Atmosphere**
- Industry/power language: **Create**
- Vehicle/aircraft platform: **Immersive Vehicles / MTS**
- Distant terrain: **Distant Horizons**
- Pregeneration tool: **Chunky**

No additional gameplay/content mod should be added merely because it is interesting or potentially useful. From this point forward, the default work is **interactions, compatibility bridges, custom DrewCraft systems, profiling, and optimization of the frozen stack**. A newly discovered mandatory transitive dependency may still be added when required to make an already-selected dependency function.

## Certification evidence

### Full verified-profile reconstruction

GitHub Actions run **34702233400** completed successfully.

It rebuilt the exact pinned Terrain Diffusion Plus source artifact, resolved the selected profile, acquired the provider artifacts, enforced provider SHA-256 locks, and reconstructed the verified server/client artifact tree without unresolved dependencies, download failures, or hash failures.

### Dedicated-server baseline certification

GitHub Actions run **34704011609** / job **103580655867** completed successfully from commit:

`4259d0ccf0e10f34298f744c42b253a1c08603d0`

Successful gates:

1. exact Terrain Diffusion Plus source checkout and NeoForge CPU build;
2. exact verified DrewCraft server mod tree reconstruction;
3. pinned NeoForge server installation;
4. fresh dedicated-server world creation;
5. Minecraft readiness (`Done`) on the new Terrain Diffusion Plus world;
6. clean shutdown;
7. restart of the same persisted world;
8. readiness after restart;
9. second clean shutdown;
10. fatal-log-pattern scan;
11. diagnostic evidence upload.

Smoke evidence artifact: **10303917312**  
Artifact digest: `sha256:52ecf4981cadcf5b9d4443665f30e03fbe8d8a27a7b363be0d7e23781f4b5a07`

The workflow rejected the following fatal signatures and found none:

- `Mod loading has failed`
- `Failed to start the minecraft server`
- `Exception in server tick loop`
- `Missing or unsupported mandatory dependencies`

### First-world timing observation

The exact Terrain Diffusion Plus build took approximately **6m 41s** in the successful CI job.

The fresh dedicated-server boot began at approximately `2026-09-12T16:20:23Z`; the workflow reported `FIRST BOOT OK` at `2026-09-12T16:46:45Z`, about **26 minutes** later including readiness detection and clean shutdown.

The same-world restart began immediately afterward and reported `RESTART OK` at `2026-09-12T16:48:51Z`, about **2 minutes** later including clean shutdown.

Interpretation: expensive Terrain Diffusion Plus first-world initialization is a provisioning/world-build concern, not evidence that normal restarts require the same amount of work.

The smoke workflow intentionally does **not** Chunky-pregenerate the production-scale world. It uses `view-distance=4` and `simulation-distance=4` and only proves that the selected stack can create, persist, reopen, and cleanly stop a real world.

## Important previous blocker that is now resolved

The first real dedicated-server attempt exposed one missing mandatory transitive dependency: Gabou's Libs required Architectury API `>=13.0.8`.

DrewCraft now pins Architectury API NeoForge **13.0.11** (CurseForge project `419699`, file `8492726`) with SHA-256:

`9cc92f2c09533fc5482c60f993bd891c655a0e32b637037cdcb7c2b23adedeeb`

After adding that required transitive, the full verified profile and dedicated-server smoke test both passed.

## What this certification proves

It proves that the frozen base dependency graph can be reproducibly assembled and can boot/restart as a real NeoForge dedicated server with a newly created Terrain Diffusion Plus world.

It does **not** yet prove:

- Windows client compatibility;
- Apple Silicon client compatibility;
- every Create/MTS/Atmosphere/Distant Horizons gameplay interaction;
- production-radius Chunky pregeneration;
- Oracle/Ampere host suitability;
- long-duration memory/performance behavior;
- the DrewCraft custom bridges, radar, aviation-weather, strategic-world, siege, or herd systems;
- final release/launcher/update behavior.

Those are later gates, not reasons to reopen base-mod selection now.

## CI policy after baseline certification

The successful smoke run is the **baseline certification run**.

Until V1 integration is substantially complete:

- use cheap manifest/schema/unit/compile tests on ordinary commits;
- test custom logic through focused unit/integration tests wherever possible;
- do not automatically rerun the full Terrain Diffusion Plus fresh-world smoke test on every integration commit;
- do not Chunky-pregenerate a production-size world in GitHub Actions;
- only repeat an expensive baseline boot before V1 acceptance, or earlier if an unavoidable base dependency/platform change invalidates this certification.

The next full-stack acceptance run should preferably be performed locally/on dedicated hardware where long execution, logs, spark profiling, and client observation do not consume GitHub-hosted CI minutes.

## Gate status

| Gate | State | Evidence / remaining condition |
| --- | --- | --- |
| Reproducible manifest/resolver | **PASS** | Exact profile reconstruction works in CI |
| Provider artifact identity/hash lock | **PASS** | 30 provider artifacts verified |
| Terrain Diffusion Plus exact source/build provenance | **PASS** | Exact commit + exact build recipe + model provenance verified |
| NeoForge platform lock | **PASS** | NeoForge 21.1.250 installer pinned/hashed |
| Dedicated-server fresh-world boot | **PASS** | Run 34704011609 |
| Dedicated-server persisted-world restart | **PASS** | Run 34704011609 |
| Obvious fatal-log scan | **PASS** | Run 34704011609 |
| Base mod additions | **FROZEN** | Compatibility/integration work now takes priority |
| Production world pipeline | **NEXT LATER GATE** | Radius, pregeneration, archive/restore still required |
| ARM/production host benchmark | **OPEN** | Benchmark after a representative world artifact exists |
| DrewCraft integration mod | **NEXT ACTIVE MILESTONE** | Scaffold + adapter contracts + capability audit |
| Aviation weather / radar | **BLOCKED ON INTEGRATION PLATFORM** | Implement as thin vertical slices after adapters |
| Strategic world kernel | **BLOCKED ON INTEGRATION PLATFORM/PERSISTENCE BASE** | Then sources, groups, sieges, herds |
| Launcher/release/deployment | **OPEN** | Build against immutable release contract |
| V1 full-stack acceptance | **OPEN** | Final local/host/client/soak/restart/profiling gate |

## Next implementation sequence

### 1. Freeze and document the certified baseline

Treat the successful dependency/profile state above as the V1 integration baseline. Avoid opportunistic version bumps or additional content mods. Any future baseline change must state why it is necessary and what certification evidence it invalidates.

### 2. Scaffold `mods/drewcraft/`

Create one NeoForge 1.21.1 / Java 21 integration mod rather than many tightly coupled custom mods.

The first skeleton should include:

- DrewCraft mod identity/version;
- server/client-safe module boundaries;
- configuration;
- feature flags;
- command/debug surface;
- test structure;
- versioned SavedData/persistence foundation;
- CI that compiles/tests the custom mod without booting the full Minecraft world.

### 3. Define upstream-independent service contracts

Core DrewCraft logic should depend on DrewCraft interfaces, not third-party implementation classes.

Initial contracts:

- `TerrainService.sample(position)` -> elevation, terrain/climate fields needed by DrewCraft;
- `WeatherService.sample(position)` -> wind, temperature, pressure, humidity, precipitation, visibility, severity;
- `PowerService` -> Create kinetic availability/consumption semantics for DrewCraft machines;
- `VehicleService` -> MTS vehicle/aircraft position, velocity, orientation and instrument/control hooks.

Upstream types must stay inside their adapter modules so an upstream update does not infect strategic/radar/aviation code.

### 4. Audit upstream integration surfaces before writing invasive hooks

Audit in this order:

1. Terrain Diffusion Plus;
2. Project Atmosphere;
3. Create;
4. MTS / Immersive Vehicles.

For each upstream, record:

- public API/events/capabilities;
- data needed by DrewCraft and where it lives;
- server-versus-client authority;
- update/event cadence;
- thread assumptions;
- persistence/network implications;
- whether direct API access is sufficient;
- whether a narrowly scoped accessor/mixin is needed.

Integration preference order is:

**public API/event -> external adapter -> narrow accessor/mixin -> maintained fork only as a last resort and only when license permits.**

### 5. First vertical proof: environment sampler

Implement Terrain Diffusion Plus and Project Atmosphere adapters first and expose a server-side debug command such as `/drewcraft env sample`.

At a position, it should report the environmental data DrewCraft will later use: elevation/terrain context plus atmospheric wind/temperature/pressure/humidity/precipitation/visibility/severity where available.

This is the first important proof because aviation and radar both depend on the same environmental truth.

### 6. Add the Create power adapter

Model Create as **kinetic power**, not generic electricity. DrewCraft machinery such as radar controllers should consume a small adapter contract that can answer whether the required kinetic infrastructure is present/adequate without making radar logic depend directly on Create internals.

### 7. Add the MTS adapter and prove aviation weather

Expose aircraft state through `VehicleService`, then prove the first cross-mod slice:

`Terrain Diffusion Plus -> Project Atmosphere -> DrewCraft -> MTS`

Initial behavior should cover server-authoritative environmental sampling, headwind/crosswind, bounded turbulence, storm/severity effects, visibility, and terrain/elevation inputs before adding broader aircraft content.

### 8. Build radar on the same environment pipeline

Use:

`Atmosphere + Terrain/elevation + antenna height/terrain horizon + Create power -> DrewCraft cached radar scan -> ground display / aircraft instrument`

Implement sensing/caching/power/terrain masking before spending time on decorative presentation.

### 9. Establish the strategic kernel

Once the integration mod/persistence base is stable, build:

- stable strategic IDs;
- coarse simulation clock;
- route/ETA engine;
- persistent `SourceRecord` / `StrategicGroup` / `HerdRecord` foundations;
- transactional materialization/dematerialization;
- casualty reconciliation;
- admin/debug inspection.

Only after this kernel is correct should DrewCraft add armies/factions, source production, siege planning, and animal-herd breadth.

### 10. Finish V1 systems, then perform one comprehensive acceptance cycle

After the V1 vertical slices and release/deployment path are implemented, run the expensive complete system locally/on the chosen server target:

- fresh install and existing-world restart;
- Windows and Apple Silicon clients;
- representative long-distance travel;
- weather + aviation + radar;
- Create and MTS interaction;
- strategic materialization/casualties/source clearing/sieges/herds;
- ordinary local spawning/farms;
- production pregeneration/archive/restore;
- spark/MSPT/memory/GC profiling;
- long soak and restart/failure tests;
- launcher update/repair/rollback;
- log/crash audit.

That is the point to diagnose full-stack runtime problems and make evidence-based optimizations. Broad gameplay/economy/difficulty tuning remains a post-V1 pass unless an upstream default violates a core design pillar.

## Immediate next task

**Scaffold the DrewCraft integration mod and perform the four-upstream capability/API audit, beginning with Terrain Diffusion Plus and Project Atmosphere.**

Do not begin with radar UI, armies, balance tuning, or another mod search. The shortest path to V1 is to establish stable adapter contracts and prove one thin environment -> gameplay vertical slice first.
