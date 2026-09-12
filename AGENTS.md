# AGENTS.md — DrewCraft / ServerMc

This repository is the canonical source for the **DrewCraft** Minecraft server experience. `ServerMc` is the repository/internal project name; DrewCraft is the player-facing product/server name.

## Read first

Before making architectural or implementation changes, read these in order:

1. `docs/v_1_requirements.md` — hard V1 product/release contract
2. `docs/v_1_development_tree.md` — canonical dependency-ordered execution checklist
3. `docs/V1_EXECUTION_STATUS.md` — **live gate status, certification evidence, frozen-baseline policy, and immediate next work**
4. `docs/STRATEGIC_WORLD_MODEL.md` — strategic hostile-source / roaming-force / herd behavior contract
5. `docs/SOURCE_CORE_SPEC.md` — exact hostile-source clearing/persistence semantics
6. `docs/PERFORMANCE_STACK.md` — performance/optimization architecture
7. `docs/MOD_STACK.md` — subsystem ownership / anti-redundancy policy
8. `docs/UPSTREAM_DEPENDENCIES.md` — source, fork, licensing, and redistribution policy
9. `pack/manifest/README.md` — resolver/profile/promotion architecture
10. `pack/manifest/upstreams.yaml`, `performance_candidates.yaml`, and `profiles.yaml` — machine-readable dependency state
11. `docs/PROJECT_SPEC.md`, `docs/SYSTEMS.md`, `docs/REPO_ARCHITECTURE.md`, and `docs/LAUNCHER_HOSTING.md`
12. `docs/ROADMAP.md` — high-level roadmap only; the requirements/development-tree/execution-status documents above win on conflicts

## Current execution state — 2026-09-12

The reproducible base stack is **certified for V1 integration development**.

- Minecraft 1.21.1 / NeoForge 21.1.250 / Java 21
- `stage2_base_performance` resolves and verifies successfully
- exact dependency graph: 30 provider artifacts + one exact Terrain Diffusion Plus source build
- full profile verification run `34702233400`: **PASS**
- dedicated-server smoke run `34704011609` / job `103580655867`: **PASS**
- fresh Terrain Diffusion Plus world reached readiness and shut down cleanly
- the same persisted world restarted, reached readiness, and shut down cleanly
- fatal-error scan passed

The current mod/dependency profile is therefore the **frozen V1 integration baseline**. Do not restart mod shopping, opportunistic version bumps, structure-pack stacking, or tactical-AI experiments unless a blocking V1 defect makes a baseline change necessary. Mandatory transitives for already-selected dependencies are allowed when genuinely required.

The next active milestone is `mods/drewcraft/`: integration-mod scaffolding, upstream capability/API audit, stable adapter contracts, and the first thin environment vertical slice.

## CI policy after baseline certification

The successful smoke test is the baseline certification run, not a test to repeat on every commit.

During normal V1 integration development:

- prefer compile, manifest, schema, unit, and focused integration tests;
- do not run full fresh Terrain Diffusion Plus world creation on ordinary commits;
- do not Chunky-pregenerate a production-scale world in GitHub Actions;
- rerun an expensive full baseline boot only if an unavoidable dependency/platform change invalidates the certification, or during the meaningful V1 acceptance cycle;
- prefer the final full-stack/soak/profiling cycle on local or dedicated hardware where long runs and client observation are cheap.

## Non-negotiable design principles

- DrewCraft V1 is **feature-complete and integration-complete, not balance-complete**. Broad recipe/economy/fuel/spawn/difficulty tuning is V1.1+ unless an upstream default destroys a core design pillar.
- Geography matters. Do not introduce routine teleportation or systems that make roads, rail, aircraft, or weather irrelevant.
- Terrain Diffusion Plus owns overworld terrain/climate/caves.
- Project Atmosphere is the atmospheric source of truth.
- Create is the primary infrastructure/technology language and owns rail/industry.
- MTS / Immersive Vehicles owns road vehicles and aircraft.
- Distant Horizons owns distant terrain LOD.
- Chunky is offline pregeneration tooling, not live world simulation.
- Simple Clouds is rendering/visual support under the weather integration; it is not a second weather authority.
- DrewCraft owns radar, cross-mod environmental bridges, strategic sources/populations, unloaded movement, armies, materialization, casualty reconciliation, herds, and siege semantics.
- Normal Minecraft local spawning, farms, ordinary spawners, caves, redstone, building, and Create contraptions remain available; strategic simulation is additive.
- Strategic populations outside loaded chunks are persistent lightweight records, not permanently ticked entities.
- Important hostile groups occupy real strategic positions while unloaded. Do not implement attacks as arbitrary timed spawn events near players.
- Hostile strategic sources are tied to real generated geography and persistent `SourceRecord`s.
- The player-facing Source Core block is not itself authoritative state.
- Legitimate Source Core destruction atomically persists `CLEARED`; replacing/moving/duplicating the block cannot reactivate or duplicate source authority.
- Groups committed before source clearing remain real populations; no new group may commit after `CLEARED` becomes authoritative.
- Wild herds may use persistent strategic records, but named/domesticated/leashed/penned/player-owned animals must not be silently absorbed.
- Sieges path normally first. Breaching is constrained to useful corridors; never implement indiscriminate nearest-block griefing.
- Radar is physical infrastructure: antenna/dish, controller, Create kinetic power, connectivity/data, terrain/height-dependent coverage, physical display.
- Friends must not manually manage Java, NeoForge, or mod folders.
- Client and server releases come from one locked manifest and must not drift.
- Do not commit generated worlds, third-party jars by default, Java runtimes, model weights, credentials, backups, or large caches.
- Do not add cloud autoscaling that can silently create charges.

## Development order from the certified baseline

`docs/v_1_development_tree.md` remains the canonical dependency graph. `docs/V1_EXECUTION_STATUS.md` says which gates are already complete.

From the current state, work in this order:

1. scaffold one NeoForge 1.21.1 / Java 21 `mods/drewcraft/` integration mod;
2. establish configuration, feature flags, observability/debug commands, tests, network/version boundaries, and versioned SavedData persistence foundation;
3. define upstream-independent adapter contracts for terrain, weather, Create kinetic power, and MTS vehicle/aircraft state;
4. audit integration surfaces in order: Terrain Diffusion Plus -> Project Atmosphere -> Create -> MTS;
5. prefer public API/events, then an external adapter, then the narrowest possible accessor/mixin; fork only as a last resort when the upstream license permits it;
6. prove a server-side environment sampler using Terrain Diffusion Plus + Project Atmosphere;
7. add Create kinetic-power and MTS adapters;
8. prove the first cross-mod slice `Terrain Diffusion Plus -> Project Atmosphere -> DrewCraft -> MTS` for aviation weather;
9. build physical radar on the same environment pipeline and cache scans/terrain masks;
10. establish strategic persistence/IDs/coarse clock/route-ETA/materialization/casualty reconciliation before scaling to sources, armies, sieges, or herds;
11. build launcher/release/server-update paths against immutable manifest/artifact contracts;
12. perform production-world, host, client-platform, restore, soak, failure, and performance acceptance tests before V1.

Do not jump straight to radar UI, army content breadth, decorative blocks, or difficulty tuning before the adapter/persistence foundations they depend on exist.

## Custom mod architecture

Prefer **one NeoForge integration mod with internal modules/adapters** rather than many tiny mutually dependent mods.

Core logic should depend on DrewCraft-owned contracts rather than third-party implementation types. Initial service boundaries should be roughly:

- `TerrainService.sample(position)` -> elevation / terrain / climate data needed by DrewCraft;
- `WeatherService.sample(position)` -> wind / temperature / pressure / humidity / precipitation / visibility / severity;
- `PowerService` -> Create kinetic availability / consumption semantics;
- `VehicleService` -> MTS pose / velocity / orientation / instrument-control hooks.

Third-party types belong inside their adapter modules. This is how DrewCraft localizes upstream churn and keeps radar, aviation, and strategic logic testable without booting the whole game.

Every major custom subsystem should have:

- a server-side feature flag;
- bounded performance behavior;
- admin/debug observability;
- versioned persistence where applicable;
- restart/unload/failure tests where applicable.

## Strategic world contract

`docs/STRATEGIC_WORLD_MODEL.md` and `docs/SOURCE_CORE_SPEC.md` are authoritative.

The strategic kernel should provide stable IDs, coarse elapsed-time simulation, route/ETA state, persistent sources/groups/herds, transactional materialization/dematerialization, and casualty reconciliation. Loaded tactical behavior is replaceable; strategic identity and persistence are not.

No global per-tick scans or distant full-resolution pathfinding. Distant groups move coarsely; nearby groups materialize into bounded tactical entities/waves and reconcile back to their strategic record.

## Weather / aviation / radar contract

Project Atmosphere provides weather state. Terrain Diffusion Plus provides terrain/elevation/climate context. DrewCraft adapts both into upstream-independent data used by aviation and radar.

The first meaningful integration proof is an environment-sampling debug command. Only after that should weather forces be applied to MTS aircraft.

Radar should reuse the same environment pipeline. Height, terrain obstruction, power, range, cadence, and caching must matter. Ground radar and aircraft radar should not become separate weather simulations.

## Performance contract

The performance stack owns performance only; it never owns gameplay state or strategic semantics.

- offline pregeneration remains the primary defense against live Terrain Diffusion worldgen cost;
- strategic records remain the primary defense against ticking thousands of distant entities;
- cache radar products and terrain masks;
- cap expensive siege planners/materialized populations;
- measure p50/p95/p99 MSPT, memory/GC, and representative client frame behavior;
- use `spark` for profiling;
- behavior-changing optimizers require separate evidence before promotion;
- C2ME remains an isolated experiment unless correctness and speed are both proven.

## Upstream dependency and fork policy

- Track official upstream source for every third-party dependency.
- Provider artifacts use exact identity/hash verification.
- Terrain Diffusion Plus source builds use exact source commit/build recipe/model provenance; raw JAR bytes are not assumed reproducible across Gradle builds when archive metadata varies.
- Prefer official binaries plus DrewCraft adapters.
- Do not fork/vendor an upstream merely to simplify packaging.
- Fork only when a required V1 integration/bug fix cannot live cleanly in DrewCraft and licensing permits the intended modification/distribution.
- If a fork becomes necessary, record upstream base ref, fork URL, DrewCraft commit, patch purpose, build procedure, license notes, and artifact identity.
- Source visibility is not redistribution permission; respect provider/license restrictions.

## Release discipline

Do not update a dependency merely because a newer version exists. The certified baseline is evidence, and changing a base dependency invalidates some of that evidence.

World-generation changes are especially sensitive because they can permanently change new terrain.

A V1 feature is complete only after its relevant dependency-tree gate passes, including restart/unload/performance behavior where required. Working once in a development world is not sufficient.

## User experience

The public-facing name is **DrewCraft**.

The download site should remain deliberately simple: one Windows install path and one Mac install path. Complexity belongs in the launcher/updater, not in instructions for friends.
