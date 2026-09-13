# AGENTS.md — DrewCraft / ServerMc

This repository is the canonical source for the **DrewCraft** Minecraft server experience. `ServerMc` is the repository/internal project name; DrewCraft is the player-facing product/server name.

## Read first

Before architectural or implementation changes, read these in order:

1. `docs/v_1_requirements.md` — hard V1 product/release contract
2. `docs/v_1_development_tree.md` — dependency-ordered execution checklist
3. `docs/CURRENT_BREAKPOINT.md` — **current stop/go checkpoint and exact next work**
4. `docs/DEVELOPMENT_BREAKPOINTS.md` — breakpoint definitions and stop/report protocol
5. `docs/V1_EXECUTION_STATUS.md` — live gates/evidence
6. `docs/V1_REMAINING_EXECUTION_PLAN.md` — detailed path through `1.0.0`
7. `docs/STRATEGIC_WORLD_MODEL.md` — strategic world behavior contract
8. `docs/STRATEGIC_MATERIALIZATION.md` — strategic ↔ tactical transaction contract
9. `docs/STRATEGIC_SOURCES.md` — hostile source lifecycle/production contract
10. `docs/HOSTILE_FORCES_V1.md` — faction/role/mission/large-army BP5 contract
11. `docs/SIEGE_V1.md` — path-first bounded BP6 siege contract
12. `docs/SOURCE_CORE_SPEC.md` — player-facing source clearing semantics
13. `docs/RADAR_V1.md` — V1 radar scope
14. `docs/PERFORMANCE_STACK.md`
15. `docs/MOD_STACK.md`
16. `docs/UPSTREAM_DEPENDENCIES.md`
17. `pack/manifest/README.md` and machine-readable manifests under `pack/manifest/`
18. `docs/PROJECT_SPEC.md`, `docs/SYSTEMS.md`, `docs/REPO_ARCHITECTURE.md`, `docs/LAUNCHER_HOSTING.md`
19. `docs/ROADMAP.md` — high-level only; current execution documents above win on conflicts

## Breakpoint execution protocol

The user uses a deliberate stop/go workflow.

When the user says **"go"**, continue through the **next unfinished breakpoint** in `docs/DEVELOPMENT_BREAKPOINTS.md` without asking for routine confirmation. Stop only when that breakpoint passes its evidence, a genuine blocker prevents progress, or evidence shows the breakpoint definition itself must change.

At a breakpoint, update `docs/CURRENT_BREAKPOINT.md`, report implementation/evidence/CI/current head/known deferrals, and **do not start the next breakpoint until the user says "go" again**.

## Current execution state — 2026-09-12

Platform remains:

- Minecraft **1.21.1**
- NeoForge **21.1.250**
- Java **21**
- current candidate profile: **34 dependencies total = 33 exact provider artifacts + one exact Terrain Diffusion Plus source build**

Radar-chain additions remain Create: Radars 0.4.9.4, Create Big Cannons 5.11.7, and Ritchie's Projectile Library 2.1.2. Provider hashes passed run `34724313143`; manifest graph passed `34724313201`; earlier dedicated-server baseline remains `34704011609`.

Environment/aviation/radar work through **8B** is implemented at development scope.

Strategic breakpoints completed:

- **BP1** — persistent strategic groups + bounded coarse elapsed-time scheduler;
- **BP2** — coarse terrain-cost routing, cached A*, ETA, 10,000-block unloaded/restart proof;
- **BP3** — transactional materialization/dematerialization, bounded waves, durable tags, idempotent casualties, restart recovery, `100 → 63` proof;
- **BP4** — persistent hostile sources, generated-geography identity, Source Core clearing, bounded source production, launch/clear race safety, restart-permanent clearing;
- **BP5** — JSON-driven factions/force roles, exact variable-size source population accounting, persistent mission/target knowledge, non-omniscient targeting, and bounded large-army/restart proof;
- **BP6** — path-first loaded-only siege runtime, bounded/cached local breach planning, gates/doors/hardness/protection scoring, constrained corridors, and anti-grief safety.

BP6 final code/test head: `1bab32c0c6028e57f99f8684d7097c9c33ed02fa`. DrewCraft mod CI run `34730303373` passed `test + build`; runtime compile run `34730277755` also passed.

The next implementation breakpoint is **BP7 — strategic herds + local-spawn coexistence**. Follow `docs/CURRENT_BREAKPOINT.md` and the BP7 section of `docs/DEVELOPMENT_BREAKPOINTS.md`. Do not begin BP8 production/release convergence until BP7 is reported and the user says **"go"** again.

## CI policy after baseline certification

Successful full smoke tests are evidence, not tests to repeat blindly on every commit.

During normal V1 development:

- prefer compile, manifest, schema, unit, and focused integration tests;
- do not run fresh full Terrain Diffusion Plus world creation on ordinary commits;
- do not Chunky-pregenerate a production-scale world in GitHub Actions;
- rerun expensive full-profile/world boot only when dependency/platform changes invalidate evidence or during meaningful V1 acceptance;
- prefer final full-stack/soak/profiling on dedicated/local hardware.

## Non-negotiable design principles

- DrewCraft V1 is **feature/integration complete, not balance complete**. Broad recipe/economy/fuel/spawn/difficulty tuning is V1.1+ unless an upstream default breaks a core pillar.
- Geography matters. Do not add routine teleportation or systems that make roads, rail, aircraft, or weather irrelevant.
- Terrain Diffusion Plus owns overworld terrain/climate/caves.
- Project Atmosphere is the atmospheric source of truth.
- Create owns primary infrastructure/industry/rail.
- Create: Radars owns V1 physical ground-radar hardware/native contacts/networks/monitors/power semantics; DrewCraft adds weather/terrain integration externally.
- MTS / Immersive Vehicles owns road vehicles and aircraft.
- Distant Horizons owns distant terrain LOD.
- Chunky is offline pregeneration tooling, never live simulation.
- Project Atmosphere's handheld Weather Radar is the V1 pilot/explorer weather device. Dedicated MTS cockpit radar remains post-V1.
- DrewCraft owns cross-mod bridges, strategic sources/populations, unloaded movement, factions/armies, materialization, casualties, herds, and siege semantics.
- Normal Minecraft spawning, farms, ordinary spawners, caves, redstone, building, and Create contraptions remain available. Strategic simulation is additive.

### Strategic performance / persistence

- Strategic populations outside loaded chunks are lightweight persistent records, not permanently ticked entities.
- **No global per-tick strategic scans or distant full-resolution pathfinding.**
- Distant routes are coarse/cached and recomputed only for meaningful invalidation/objective changes.
- Distant groups advance from elapsed time and do not keep chunks loaded to move.
- Normal Minecraft entity AI/pathfinding exists only for materialized populations near players.
- A large army may represent hundreds of units while only a bounded tactical subset exists as entities.
- Materialization never subtracts population. Only idempotently confirmed tactical deaths reduce strategic strength.
- Materialization never force-loads chunks.
- Each group has at most one durable active encounter; stale tagged entities are rejected after reconciliation.
- Per-encounter active caps and global per-cycle spawn caps remain mandatory.

### Hostile sources and forces

- Hostile sources are tied to deterministic generated geography and persistent `SourceRecord`s.
- Source discovery/production uses explicit records/structure hooks; never add recurring global chunk/structure scans.
- The Source Core block is not authoritative state and has no portable BlockItem.
- Legitimate Source Core destruction atomically persists `CLEARED`; replacing/moving/duplicating the block cannot reactivate source authority.
- Groups committed before clearing remain real; no group may commit after `CLEARED` becomes authoritative.
- Variable-size production must charge the source's **exact represented group strength** under the same SavedData transaction/lock as clearing.
- Hostile faction/group content belongs in the versioned JSON catalog unless behavior genuinely requires code.
- Strategic group composition counts must equal `totalStrength` exactly.
- Every hostile force carries persistent mission metadata: template ID, target position, issue time, target-knowledge category, and explanation.
- **Do not target the nearest player or hidden player base through a global lookup.** Future intelligence must enter the explicit target-knowledge model.
- Represented army strength and loaded entity count are separate concepts. Do not raise tactical caps because a strategic army is large.

### Siege and ecology

- `docs/SIEGE_V1.md` is authoritative for V1 siege behavior.
- Ordinary Minecraft navigation is always attempted before breaching.
- Siege logic exists only for already-materialized, loaded `RAID`/`ARMY` encounters.
- Only designated breaker entity types may deliberately break blocks.
- Siege planning is local, bounded, and cached; never run it for remote strategic groups.
- Do not force-load chunks for siege snapshots. Unloaded cells are protected/impassable.
- Breaches are constrained useful corridors, never nearest-block griefing.
- Gates/doors/weaker barriers should be preferred when useful; hardness affects cost.
- `#drewcraft:siege_protected` is unbreachable. Block entities are protected by default.
- `#drewcraft:siege_decorative` is high-cost and data-pack extensible.
- Revalidate the exact breach block immediately before destruction.
- Every successful breach invalidates the cached plan so the next destruction requires a fresh world snapshot.
- Keep the BP6 hard work bounds and independent `features.strategicSiege` kill switch.
- Wild herds may use persistent strategic records, but named/domesticated/leashed/penned/player-owned animals must never be silently absorbed.

### Release / user experience

- Friends must not manually manage Java, NeoForge, or mod folders.
- Client and server releases come from one locked manifest and must not drift.
- Do not commit generated worlds, third-party jars by default, Java runtimes, model weights, credentials, backups, or large caches.
- Do not add cloud autoscaling that can silently create charges.

## Development order from current state

`docs/V1_REMAINING_EXECUTION_PLAN.md` is the detailed contract. Remaining critical path:

1. **NEXT: BP7** — strategic wild herds + normal local-spawn coexistence;
2. **BP8** — production world / hosting / immutable releases / updater / Windows + Apple Silicon launcher convergence;
3. **BP9** — cross-system scale, crash, restart, persistence, backup, and performance hardening;
4. **BP10** — exact release candidate + hard acceptance → `1.0.0`.

In parallel, advance production-world/pregeneration including real source-template/core/faction binding, production host/ARM benchmarking, immutable release artifacts, server update/backup tooling, and Windows/Apple Silicon launchers. These converge before the RC freeze.

Do not start BP8 before BP7 is reported and the user says **"go"** again.

## Custom mod architecture

Prefer **one NeoForge integration mod with internal modules/adapters** rather than many tiny mutually dependent mods.

Core logic should depend on DrewCraft-owned contracts rather than third-party implementation types. Third-party types belong inside adapters/compat modules so upstream churn stays localized.

Every major custom subsystem should have:

- a server-side feature flag;
- bounded performance behavior;
- admin/debug observability;
- versioned persistence where applicable;
- restart/unload/failure tests where applicable.

## Strategic world contract

`docs/STRATEGIC_WORLD_MODEL.md`, `docs/STRATEGIC_MATERIALIZATION.md`, `docs/STRATEGIC_SOURCES.md`, `docs/HOSTILE_FORCES_V1.md`, `docs/SIEGE_V1.md`, `docs/SOURCE_CORE_SPEC.md`, and Stages 11-17 of `docs/V1_REMAINING_EXECUTION_PLAN.md` are authoritative.

The strategic kernel now provides stable IDs, coarse elapsed-time simulation, cached route/ETA state, persistent sources/groups/missions, transactional materialization/dematerialization, exact source production/clearing, data-driven hostile-force composition, explicit target knowledge, casualty reconciliation, and bounded loaded-world siege fallback. Loaded tactical behavior is replaceable; strategic identity and persistence are not.

Central rule:

> **Keep the world abstract while nobody is looking; materialize only what players can interact with; cache expensive decisions; persist every important consequence.**

## Weather / aviation / radar contract

Project Atmosphere provides weather state. Terrain Diffusion Plus provides terrain/elevation. DrewCraft adapts both into upstream-independent data used by aviation/radar.

V1 ground radar uses official Create: Radars unmodified. DrewCraft contributes cached weather/terrain integration through `docs/RADAR_V1.md`. Do not fork or redistribute a modified Create: Radars jar.

## Performance contract

- offline pregeneration is the primary defense against live Terrain Diffusion worldgen cost;
- strategic records are the primary defense against ticking thousands of distant entities;
- route caches/event-driven invalidation prevent constant distant pathfinding;
- source scheduling processes bounded persistent records, not world scans;
- loaded materialization retains explicit encounter/entity/global-spawn budgets;
- siege planning is bounded, cached, and loaded-only;
- cache radar products and terrain masks;
- measure p50/p95/p99 MSPT, memory/GC, route/scheduler/source/materialization/siege/radar timings, network, and representative client frame behavior;
- use `spark` for profiling;
- behavior-changing optimizers require evidence before promotion;
- C2ME remains isolated unless correctness and speed are both proven.

## Upstream dependency / release discipline

- Track official upstream source for third-party dependencies.
- Provider artifacts use exact identity/hash verification.
- Terrain Diffusion Plus source builds use exact source commit/build recipe/model provenance.
- Prefer official binaries plus DrewCraft adapters.
- Do not fork/vendor upstream merely to simplify packaging.
- Fork only when required V1 behavior cannot live cleanly in DrewCraft and licensing permits it; record provenance/build/license details.
- Do not update dependencies merely because newer versions exist; compatibility evidence is valuable.
- World-generation changes are especially sensitive.
- A V1 feature is complete only after its relevant restart/unload/performance gates pass; working once in a dev world is not sufficient.

## User experience

The public-facing name is **DrewCraft**.

The download site stays deliberately simple: one Windows install path and one Mac install path. Complexity belongs in the launcher/updater, not instructions for friends.
