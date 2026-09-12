# AGENTS.md — DrewCraft / ServerMc

This repository is the canonical source for the **DrewCraft** Minecraft server experience. `ServerMc` is the repository/internal project name; DrewCraft is the player-facing product/server name.

## Read first

Before making architectural or implementation changes, read these in order:

1. `docs/v_1_requirements.md` — hard V1 product/release contract
2. `docs/v_1_development_tree.md` — canonical dependency-ordered execution checklist
3. `docs/V1_EXECUTION_STATUS.md` — **live gate status, certification evidence, and immediate next work**
4. `docs/V1_REMAINING_EXECUTION_PLAN.md` — **detailed post-8B implementation plan from the current state through `1.0.0`**
5. `docs/STRATEGIC_WORLD_MODEL.md` — strategic hostile-source / roaming-force / herd behavior contract
6. `docs/SOURCE_CORE_SPEC.md` — exact hostile-source clearing/persistence semantics
7. `docs/RADAR_V1.md` — current V1 radar scope and acceptance contract
8. `docs/PERFORMANCE_STACK.md` — performance/optimization architecture
9. `docs/MOD_STACK.md` — subsystem ownership / anti-redundancy policy
10. `docs/UPSTREAM_DEPENDENCIES.md` — source, fork, licensing, and redistribution policy
11. `pack/manifest/README.md` — resolver/profile/promotion architecture
12. `pack/manifest/upstreams.yaml`, `performance_candidates.yaml`, `radar_candidates.yaml`, and `profiles.yaml` — machine-readable dependency state
13. `docs/PROJECT_SPEC.md`, `docs/SYSTEMS.md`, `docs/REPO_ARCHITECTURE.md`, and `docs/LAUNCHER_HOSTING.md`
14. `docs/ROADMAP.md` — high-level roadmap only; the requirements/current execution documents above win on conflicts

## Current execution state — 2026-09-12

The original Minecraft 1.21.1 / NeoForge 21.1.250 / Java 21 **31-dependency** baseline is certified for V1 integration development. Since that certification, the selected V1 radar frontend added the complete required runtime chain:

- Create: Radars 0.4.9.4;
- Create Big Cannons 5.11.7;
- Ritchie's Projectile Library 2.1.2.

The current candidate profile is therefore **34 dependencies total: 33 exact provider artifacts + one exact Terrain Diffusion Plus source build**. Provider acquisition/hash evidence for the 33 provider artifacts passed in run `34724313143` with zero hard failures. The earlier 31-dependency baseline certification remains run `34704011609`; current-profile verification/smoke evidence is tracked in `docs/V1_EXECUTION_STATUS.md`.

Steps through **8B** are implemented at their documented scopes:

- DrewCraft integration mod/service platform;
- Terrain Diffusion realized-world adapter;
- Project Atmosphere adapter;
- Create kinetic adapter;
- MTS observation;
- aviation/weather physics bridge;
- cached terrain-aware radar engine;
- Create: Radars physical ground-radar + DrewCraft weather overlay integration.

The next implementation head is **Stage 11 — strategic-world kernel**. Follow `docs/V1_REMAINING_EXECUTION_PLAN.md` rather than the older pre-8B wording when choosing exact tasks.

## CI policy after baseline certification

The successful smoke test is evidence, not a test to repeat blindly on every commit.

During normal V1 integration development:

- prefer compile, manifest, schema, unit, and focused integration tests;
- do not run full fresh Terrain Diffusion Plus world creation on ordinary commits;
- do not Chunky-pregenerate a production-scale world in GitHub Actions;
- rerun an expensive full baseline/current-profile boot when an unavoidable dependency/platform change invalidates earlier evidence, or during the meaningful V1 acceptance cycle;
- prefer the final full-stack/soak/profiling cycle on local or dedicated hardware where long runs and client observation are cheap.

## Non-negotiable design principles

- DrewCraft V1 is **feature-complete and integration-complete, not balance-complete**. Broad recipe/economy/fuel/spawn/difficulty tuning is V1.1+ unless an upstream default destroys a core design pillar.
- Geography matters. Do not introduce routine teleportation or systems that make roads, rail, aircraft, or weather irrelevant.
- Terrain Diffusion Plus owns overworld terrain/climate/caves.
- Project Atmosphere is the atmospheric source of truth.
- Create is the primary infrastructure/technology language and owns rail/industry.
- Create: Radars owns V1 physical ground-radar hardware, native contacts, networks, monitors, and its own Create-powered operation; DrewCraft adds weather/terrain integration externally.
- MTS / Immersive Vehicles owns road vehicles and aircraft.
- Distant Horizons owns distant terrain LOD.
- Chunky is offline pregeneration tooling, not live world simulation.
- Simple Clouds is rendering/visual support under the weather integration; it is not a second weather authority.
- Project Atmosphere's existing handheld Weather Radar is the V1 pilot/explorer weather device. A dedicated MTS cockpit radar instrument is post-V1 unless explicitly promoted.
- DrewCraft owns cross-mod environmental bridges, strategic sources/populations, unloaded movement, armies, materialization, casualty reconciliation, herds, and siege semantics.
- Normal Minecraft local spawning, farms, ordinary spawners, caves, redstone, building, and Create contraptions remain available; strategic simulation is additive.
- Strategic populations outside loaded chunks are persistent lightweight records, not permanently ticked entities.
- **No global per-tick strategic scans or distant full-resolution pathfinding.** Distant routes are coarse, cached, and recomputed only for meaningful invalidation/objective changes.
- Distant groups advance from elapsed time; they do not keep chunks loaded simply to move.
- Normal Minecraft entity AI/pathfinding exists only for materialized populations near players.
- A large strategic army may represent hundreds of units while only a bounded tactical subset/wave is materialized at once.
- Siege planning only occurs for loaded encounters after ordinary navigation fails; it is bounded/cached and never a distant global simulation.
- Important hostile groups occupy real strategic positions while unloaded. Do not implement attacks as arbitrary timed spawn events near players.
- Hostile strategic sources are tied to real generated geography and persistent `SourceRecord`s.
- The player-facing Source Core block is not itself authoritative state.
- Legitimate Source Core destruction atomically persists `CLEARED`; replacing/moving/duplicating the block cannot reactivate or duplicate source authority.
- Groups committed before source clearing remain real populations; no new group may commit after `CLEARED` becomes authoritative.
- Wild herds may use persistent strategic records, but named/domesticated/leashed/penned/player-owned animals must not be silently absorbed.
- Sieges path normally first. Breaching is constrained to useful corridors; never implement indiscriminate nearest-block griefing.
- Friends must not manually manage Java, NeoForge, or mod folders.
- Client and server releases come from one locked manifest and must not drift.
- Do not commit generated worlds, third-party jars by default, Java runtimes, model weights, credentials, backups, or large caches.
- Do not add cloud autoscaling that can silently create charges.

## Development order from the current state

`docs/V1_REMAINING_EXECUTION_PLAN.md` is the detailed execution contract from post-8B to release. The critical path is:

1. strategic persistence schema + stable IDs;
2. bounded coarse scheduler + elapsed-time/catch-up semantics;
3. coarse terrain-cost cache/interface;
4. cached route engine + ETA;
5. one fully unloaded moving-group proof;
6. transactional materialization/dematerialization + casualty reconciliation;
7. hostile-source registry + Source Core lifecycle;
8. data-driven patrols/hordes/raids/armies and bounded wave materialization;
9. bounded path-first siege planner;
10. strategic wild herds;
11. normal local-spawn coexistence;
12. cross-system gameplay scenarios;
13. performance hardening;
14. crash/persistence/backup/recovery hardening;
15. V1 RC freeze;
16. hard acceptance and `1.0.0`.

In parallel, advance production-world/pregeneration, production host/ARM benchmarking, immutable release artifacts, server update/backup tooling, and the Windows/Apple Silicon launcher. These converge at the RC freeze.

Do not jump directly to army breadth, siege AI, or herd content before the shared strategic persistence/routing/materialization gates pass.

## Custom mod architecture

Prefer **one NeoForge integration mod with internal modules/adapters** rather than many tiny mutually dependent mods.

Core logic should depend on DrewCraft-owned contracts rather than third-party implementation types. Existing service boundaries include terrain, weather, Create power, vehicle state, and radar. Third-party types belong inside adapter/compat modules so upstream churn stays localized.

Every major custom subsystem should have:

- a server-side feature flag;
- bounded performance behavior;
- admin/debug observability;
- versioned persistence where applicable;
- restart/unload/failure tests where applicable.

## Strategic world contract

`docs/STRATEGIC_WORLD_MODEL.md`, `docs/SOURCE_CORE_SPEC.md`, and Stages 11-17 of `docs/V1_REMAINING_EXECUTION_PLAN.md` are authoritative.

The strategic kernel provides stable IDs, coarse elapsed-time simulation, cached route/ETA state, persistent sources/groups/herds, transactional materialization/dematerialization, and casualty reconciliation. Loaded tactical behavior is replaceable; strategic identity and persistence are not.

The central performance rule is:

> **Keep the world abstract while nobody is looking; materialize only what players can interact with; cache expensive decisions; persist every important consequence.**

## Weather / aviation / radar contract

Project Atmosphere provides weather state. Terrain Diffusion Plus provides terrain/elevation context. DrewCraft adapts both into upstream-independent data used by aviation and radar.

V1 ground radar uses official Create: Radars unmodified. DrewCraft contributes cached weather/terrain integration through the compatibility bridge described in `docs/RADAR_V1.md`. Do not fork or redistribute a modified Create: Radars jar.

## Performance contract

The performance stack owns performance only; it never owns gameplay state or strategic semantics.

- offline pregeneration remains the primary defense against live Terrain Diffusion worldgen cost;
- strategic records remain the primary defense against ticking thousands of distant entities;
- route caches and event-driven invalidation prevent constant distant pathfinding;
- materialized encounters have explicit active-entity/wave budgets;
- cache radar products and terrain masks;
- cap expensive siege planners and run them only for loaded blocked encounters;
- measure p50/p95/p99 MSPT, memory/GC, route/scheduler/siege timings, network, and representative client frame behavior;
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

Do not update a dependency merely because a newer version exists. Existing compatibility evidence is valuable, and changing a base dependency invalidates some of it.

World-generation changes are especially sensitive because they can permanently change new terrain.

A V1 feature is complete only after its relevant dependency-tree gate passes, including restart/unload/performance behavior where required. Working once in a development world is not sufficient.

## User experience

The public-facing name is **DrewCraft**.

The download site should remain deliberately simple: one Windows install path and one Mac install path. Complexity belongs in the launcher/updater, not in instructions for friends.
