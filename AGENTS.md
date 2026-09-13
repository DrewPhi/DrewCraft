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
7. `docs/STRATEGIC_WORLD_MODEL.md`
8. `docs/STRATEGIC_MATERIALIZATION.md`
9. `docs/STRATEGIC_SOURCES.md`
10. `docs/HOSTILE_FORCES_V1.md`
11. `docs/SIEGE_V1.md`
12. `docs/HERDS_ECOLOGY_V1.md`
13. `docs/SOURCE_CORE_SPEC.md`
14. `docs/RADAR_V1.md`
15. `docs/PERFORMANCE_STACK.md`
16. `docs/MOD_STACK.md`
17. `docs/UPSTREAM_DEPENDENCIES.md`
18. `pack/manifest/README.md` and machine-readable manifests under `pack/manifest/`
19. `docs/PROJECT_SPEC.md`, `docs/SYSTEMS.md`, `docs/REPO_ARCHITECTURE.md`, `docs/LAUNCHER_HOSTING.md`
20. `docs/ROADMAP.md` — high-level only; current execution documents above win on conflicts

## Breakpoint execution protocol

The user uses a deliberate stop/go workflow.

When the user says **"go"**, continue through the **next unfinished breakpoint** in `docs/DEVELOPMENT_BREAKPOINTS.md` without asking for routine confirmation. Stop only when that breakpoint passes its evidence, a genuine blocker prevents progress, or evidence shows the breakpoint definition itself must change.

At a breakpoint, update `docs/CURRENT_BREAKPOINT.md`, report implementation/evidence/CI/current head/known deferrals, and **do not start the next breakpoint until the user says "go" again**.

## Current execution state — 2026-09-12

Platform remains:

- Minecraft **1.21.1**
- NeoForge **21.1.250**
- Java **21**
- candidate profile: **34 dependencies total = 33 exact provider artifacts + one exact Terrain Diffusion Plus source build**

Provider hashes passed `34724313143`; manifest graph passed `34724313201`; dedicated-server baseline remains `34704011609`. Environment/aviation/radar integration through **8B** is implemented at development scope.

Completed strategic breakpoints:

- **BP1** — persistent strategic records + bounded elapsed-time scheduler;
- **BP2** — coarse cached terrain routing/ETA + 10,000-block unloaded/restart proof;
- **BP3** — transactional materialization/dematerialization, bounded waves, idempotent casualties, restart recovery;
- **BP4** — persistent hostile sources, Source Core clearing, bounded source production, clear/launch race safety;
- **BP5** — JSON factions/force roles, variable-size armies, persistent explainable missions, non-omniscient targeting;
- **BP6** — path-first loaded-only bounded/cached siege planner with anti-grief protections;
- **BP7** — explicit persistent strategic wild herds, bounded migration/materialization/restart, independent herd kill switch, and architecture-level proof that ordinary spawning/farms/spawners remain independent.

BP7 final code/test head: `dfa507d0ac9c330c16897afe19f88467c06784a6`; DrewCraft mod CI `34730837899` passed `test + build`.

The next implementation breakpoint is **BP8 — production world + deployment + release/launcher convergence**. Follow `docs/CURRENT_BREAKPOINT.md` and BP8 in `docs/DEVELOPMENT_BREAKPOINTS.md`. Do not begin BP9 until BP8 is reported and the user says **"go"** again.

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
- Normal Minecraft spawning, farms, ordinary spawners, caves, redstone, building, and Create contraptions remain available. Strategic simulation is additive.

### Strategic performance / persistence

- Strategic populations outside loaded chunks are lightweight persistent records, not permanently ticked entities.
- **No global per-tick strategic scans or distant full-resolution pathfinding.**
- Distant routes are coarse/cached and recomputed only for meaningful invalidation/objective changes.
- Distant groups advance from elapsed time and do not keep chunks loaded to move.
- Normal Minecraft entity AI/pathfinding exists only for materialized populations near players.
- Large armies/herds may represent hundreds while only a bounded tactical subset exists as entities.
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
- Variable-size production charges the source's exact represented strength under the same SavedData authority as clearing.
- Hostile composition belongs in the versioned JSON catalog unless behavior genuinely requires code.
- Strategic group composition counts must equal `totalStrength` exactly.
- Hostile forces carry persistent mission target + target-knowledge explanation.
- **Do not target the nearest player or hidden player base through a global lookup.** New intelligence must enter the explicit target-knowledge model.
- Represented army strength and loaded entity count are separate concepts.

### Siege contract

`docs/SIEGE_V1.md` is authoritative.

- Ordinary navigation always comes before breaching.
- Siege logic exists only for already-materialized loaded `RAID`/`ARMY` encounters.
- Only designated breaker types may deliberately break blocks.
- Planning is local, bounded, cached, and never force-loads chunks.
- Breaches are constrained useful corridors, never nearest-block griefing.
- Gates/doors/weaker barriers are preferred when useful; hardness affects cost.
- `#drewcraft:siege_protected` is unbreachable; block entities are protected by default.
- `#drewcraft:siege_decorative` is high-cost and data-pack extensible.
- Revalidate the exact breach block before destruction and invalidate/replan after every successful break.
- Preserve BP6 hard work limits and `features.strategicSiege` kill switch.

### Herd / ecology contract

`docs/HERDS_ECOLOGY_V1.md` is authoritative.

- Strategic herds originate only from explicit `WildHerdDescriptor`s; **never scan or absorb existing local animals**.
- Natural, bred, named, leashed, tamed/player-owned, penned/farmed, spawner-created, and mod-created local animals remain ordinary Minecraft entities.
- Herd IDs are deterministic from dimension + species + migration endpoints; registration is idempotent and cannot reset a moving/casualty-bearing herd.
- Herds reuse the shared cached-route/materialization/casualty/restart kernel and remain lightweight while unloaded.
- Do not add global `MobSpawnEvent` cancellation, replace `NaturalSpawner`, rewrite `SpawnPlacements`, manipulate `BaseSpawner`, or otherwise quota ordinary ecology.
- Untagged entity joins must return before strategic stale-entity cancellation.
- `features.strategicHerds` pauses only strategic HERD movement/materialization while preserving herd records; active DrewCraft-tagged herd copies reconcile safely; ordinary animals remain untouched.
- Production-world herd species/counts/corridors are a BP8 world-build responsibility.

### Release / user experience

- Friends must not manually manage Java, NeoForge, or mod folders.
- Client and server releases come from one locked manifest and must not drift.
- Do not commit generated worlds, third-party jars by default, Java runtimes, model weights, credentials, backups, or large caches.
- Do not add cloud autoscaling that can silently create charges.

## Development order from current state

`docs/V1_REMAINING_EXECUTION_PLAN.md` is the detailed contract. Remaining critical path:

1. **NEXT: BP8** — production world / hosting / immutable releases / updater / Windows + Apple Silicon launcher convergence;
2. **BP9** — cross-system scale, crash, restart, persistence, backup, and performance hardening;
3. **BP10** — exact release candidate + hard acceptance → `1.0.0`.

BP8 is where previously parallel production tracks converge: final world/pregeneration and source/herd seeding, production host/ARM benchmark, immutable release artifacts, server update/backup/rollback tooling, and Windows/Apple Silicon launchers.

Do not start BP9 before BP8 is reported and the user says **"go"** again.

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

`docs/STRATEGIC_WORLD_MODEL.md`, `docs/STRATEGIC_MATERIALIZATION.md`, `docs/STRATEGIC_SOURCES.md`, `docs/HOSTILE_FORCES_V1.md`, `docs/SIEGE_V1.md`, `docs/HERDS_ECOLOGY_V1.md`, `docs/SOURCE_CORE_SPEC.md`, and Stages 11-17 of `docs/V1_REMAINING_EXECUTION_PLAN.md` are authoritative.

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
- strategic herds share these bounds and never replace ordinary ecology;
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
