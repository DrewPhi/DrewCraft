# AGENTS.md — DrewCraft / ServerMc

This repository is the canonical source for the **DrewCraft** Minecraft server experience. `ServerMc` is the internal repository name; DrewCraft is the player-facing product/server name.

## Read first

Before architectural or implementation changes, read these in order:

1. `docs/v_1_requirements.md`
2. `docs/v_1_development_tree.md`
3. `docs/CURRENT_BREAKPOINT.md` — **current stop/go checkpoint and exact next work**
4. `docs/DEVELOPMENT_BREAKPOINTS.md`
5. `docs/V1_EXECUTION_STATUS.md`
6. `docs/V1_REMAINING_EXECUTION_PLAN.md`
7. `docs/BP8_RELEASE_OPERATIONS.md` — production world/release/deploy/launcher ownership
8. `docs/STRATEGIC_WORLD_MODEL.md`
9. `docs/STRATEGIC_MATERIALIZATION.md`
10. `docs/STRATEGIC_SOURCES.md`
11. `docs/HOSTILE_FORCES_V1.md`
12. `docs/SIEGE_V1.md`
13. `docs/HERDS_ECOLOGY_V1.md`
14. `docs/SOURCE_CORE_SPEC.md`
15. `docs/RADAR_V1.md`
16. `docs/PERFORMANCE_STACK.md`
17. `docs/MOD_STACK.md`
18. `docs/UPSTREAM_DEPENDENCIES.md`
19. `pack/manifest/README.md` + machine-readable manifests under `pack/manifest/`
20. `docs/PROJECT_SPEC.md`, `docs/SYSTEMS.md`, `docs/REPO_ARCHITECTURE.md`, `docs/LAUNCHER_HOSTING.md`
21. `docs/ROADMAP.md` — high-level only; current execution documents win on conflicts.

## Breakpoint protocol

The user uses a deliberate stop/go workflow.

When the user says **"go"**, continue through the next unfinished breakpoint without routine confirmation. Stop only when the breakpoint passes its evidence, a genuine blocker prevents progress, or evidence shows the breakpoint definition itself must change.

At a breakpoint, update `docs/CURRENT_BREAKPOINT.md`, report implementation/evidence/CI/current head/known deferrals, and **do not start the next breakpoint until the user says "go" again**.

## Current execution state — 2026-09-12

Platform:

- Minecraft **1.21.1**
- NeoForge **21.1.250**
- Java **21**
- external candidate profile: **34 dependencies = 33 exact provider artifacts + one exact Terrain Diffusion Plus source build**
- provider hashes **34724313143**
- manifest graph **34724313201**
- dedicated-server baseline **34704011609**.

Completed breakpoints:

- **BP1** persistent strategic records + bounded elapsed-time scheduler;
- **BP2** coarse cached terrain routing/ETA + unloaded/restart proof;
- **BP3** transactional materialization/dematerialization + bounded waves/idempotent casualties/recovery;
- **BP4** persistent hostile sources + permanent Source Core clearing + launch/clear race safety;
- **BP5** JSON factions/roles/missions + large abstract armies + non-omniscient targeting;
- **BP6** path-first loaded-only bounded siege planner + anti-grief safety;
- **BP7** explicit persistent herds + unloaded migration + ordinary ecology isolation;
- **BP8** production-world/release/deployment/launcher convergence at implementation/native-build/CI scope.

The next breakpoint is **BP9 — cross-system scale, failure, recovery, and performance hardening**. Follow `docs/CURRENT_BREAKPOINT.md`. Do not begin BP10 until BP9 is reported and the user says **"go"** again.

## CI policy

Successful expensive smoke tests are reusable evidence, not tests to repeat blindly.

- Prefer compile, manifest, schema, unit, and focused integration tests during ordinary development.
- Do not create fresh full Terrain Diffusion worlds or production-scale Chunky pregeneration on ordinary commits.
- Repeat expensive full-world/full-pack work only when platform/dependency changes invalidate evidence or during BP9/BP10 acceptance.
- Final soak/profiling belongs on representative dedicated/local hardware.

## Non-negotiable product/system principles

- DrewCraft V1 is **feature/integration complete, not balance complete**. Broad recipe/economy/fuel/spawn/difficulty tuning is V1.1+ unless an upstream default breaks a core pillar.
- Geography matters; do not make roads, rail, aircraft, or weather irrelevant with routine teleportation.
- Terrain Diffusion Plus owns overworld terrain/climate/caves.
- Project Atmosphere is atmospheric truth.
- Create owns primary infrastructure/industry/rail.
- Create: Radars owns V1 physical ground-radar hardware/native contacts/networks/monitors/power semantics; DrewCraft adds weather/terrain integration externally.
- MTS / Immersive Vehicles owns road vehicles and aircraft.
- Distant Horizons owns distant terrain LOD.
- Chunky is offline pregeneration tooling, never live simulation.
- Project Atmosphere handheld Weather Radar is the V1 pilot/explorer weather device; dedicated MTS cockpit radar is post-V1.
- Normal Minecraft spawning, farms, spawners, caves, redstone, building, and Create contraptions remain available. DrewCraft strategic systems are additive.

## Strategic performance / persistence

Central rule:

> **Keep the world abstract while nobody is looking; materialize only what players can interact with; cache expensive decisions; persist every important consequence.**

- No global per-tick strategic scans or distant full-resolution pathfinding.
- Distant groups/herds are lightweight records; routes are coarse/cached/event-invalidated.
- Distant movement uses elapsed-time arithmetic and does not keep chunks loaded.
- Minecraft AI/pathfinding exists only for materialized populations near players.
- Armies/herds can represent hundreds while only a bounded tactical subset exists as entities.
- Materialization never subtracts population; only idempotently confirmed deaths do.
- Never force-load chunks to materialize strategic populations.
- One durable active encounter max per group; stale tagged entities are rejected.
- Per-encounter and global spawn budgets remain mandatory.

## Hostile source/force contract

- Sources are deterministic generated geography + persistent `SourceRecord`s.
- Use explicit structure/index hooks; never recurring global chunk/structure scans.
- Source Core block is not authoritative and has no portable BlockItem.
- Legitimate core destruction atomically persists `CLEARED`; replacing/moving/copying the block cannot restore authority.
- Groups committed before clear remain real; nothing may commit after `CLEARED` becomes authoritative.
- Variable launches charge exact represented strength under the same SavedData authority as clearing.
- Hostile composition belongs in versioned JSON unless behavior truly requires code.
- Composition totals must equal strategic strength.
- Hostile missions carry explicit destination + target-knowledge reason.
- **Never globally target the nearest player/hidden base.** New intelligence must enter the target-knowledge model.
- Represented army strength and loaded entity count are separate.

## Siege contract

`docs/SIEGE_V1.md` is authoritative.

- Ordinary navigation always comes first.
- Siege exists only for loaded `RAID`/`ARMY` encounters.
- Only designated breaker entity types break blocks deliberately.
- Planning is local/bounded/cached and never force-loads chunks.
- Breach useful corridors, not nearest-block griefing.
- Prefer useful gates/doors/weaker barriers; hardness matters.
- `#drewcraft:siege_protected` is unbreachable; block entities are protected by default.
- `#drewcraft:siege_decorative` is high-cost/data-pack extensible.
- Revalidate every breach block and invalidate/replan after each successful break.
- Preserve BP6 hard bounds and independent kill switch.

## Herd/ecology contract

`docs/HERDS_ECOLOGY_V1.md` is authoritative.

- Strategic herds originate only from explicit descriptors; never absorb existing local animals.
- Natural, bred, named, leashed, tamed/player-owned, penned/farmed, spawner-created, and mod-created local animals remain ordinary entities.
- Herd identity is deterministic and registration cannot reset living/casualty-bearing records.
- Herds reuse the common routing/materialization/casualty/restart kernel.
- Do not cancel global mob spawns, replace `NaturalSpawner`, rewrite `SpawnPlacements`, or manipulate `BaseSpawner`.
- Untagged entity joins return before strategic stale-entity cancellation.
- `features.strategicHerds` affects only strategic HERD records/entities.

## BP8 production/release ownership

`docs/BP8_RELEASE_OPERATIONS.md` is authoritative.

### World identity

- Application version and world identity are separate.
- Production compatibility uses explicit `worldId`, `worldRevision`, and `generationPackVersion`.
- Current world-generation compatibility identity is **`drewcraft-worldgen-1`**.
- Do not invent/freeze a final seed or pregeneration radius without the measured/visual candidate gate.
- Production world candidate lock must verify archive SHA, clean restore, measurements, and terrain/source/herd reviews.
- Offline world indexing decides source/core/herd seeds; runtime never scans the world for them.
- Generic Source Core placement: **horizontal structure center -> nearest accessible interior floor**.
- Strategic seed import must fail closed on world-identity mismatch and never force-load source chunks.

### Release contract

- **One immutable `release-manifest.json` is client/server application truth.** `live.json` is only a channel pointer.
- Client/server must never maintain independent mod lists.
- Every managed file has exact side/path/size/SHA/acquisition identity.
- DrewCraft's own compiled mod must be explicitly injected/hash-recorded into both verified trees.
- Exact locked provider artifacts should use official provider acquisition URLs when available; do not rehost third-party jars just to simplify packaging.
- DrewCraft public payload contains only DrewCraft/source-built/runtime-owned files plus manifest/evidence/checksums.
- Terrain Diffusion source builds keep exact commit/build/model provenance.
- Do not update dependency versions merely because newer versions exist; certified compatibility evidence has value.

### Server deployment

- An immutable server release includes exact NeoForge runtime + verified server tree; a mod directory alone is not a deployable release.
- Persistent world/logs are outside immutable application releases.
- Updates stage and hash-verify before activation, create a pre-update backup, atomically switch the application pointer, then health-check.
- Failed application rollout restores application pointer/metadata only. **Never blindly roll the world backward.**
- World-generation compatibility must be validated before activation.
- Production host automation must not silently autoscale or create surprise charges.
- Initial benchmark target remains fixed OCI A1 2 OCPU / 12 GB; BP9 returns `PASS` or explicit `MIGRATE`.

### Client launcher

- Friends must not manually manage Java, NeoForge, Prism instances, mods, or configs.
- Exact Java + Prism runtime archives are pinned by URL/size/SHA per supported OS/architecture.
- Prism owns Microsoft authentication; DrewCraft owns convergence/update/repair.
- Real Prism instance metadata declares exact Minecraft + NeoForge components.
- Staged updates verify before atomic promotion and preserve explicitly user-owned local data.
- Client checks safe server pack/protocol/health metadata before launch.
- Windows public artifact filename: `DrewCraft-Windows.exe`.
- Apple Silicon public artifact filename: `DrewCraft-macOS.dmg`.
- Do not claim production macOS distribution complete until Apple Developer signing/notarization passes.
- Do not publish a stable `live.json` pointing at unavailable private artifacts.

## Current critical path

1. **NEXT: BP9** — generate/select/freeze final world; deploy exact release; A1 `PASS`/`MIGRATE`; cross-system multiplayer scale/performance/crash/restart/backup/recovery; real client-machine acceptance evidence.
2. **BP10** — exact RC freeze, production signing/notarization/public promotion, hard acceptance, tag `1.0.0`.

Do not start BP10 before BP9 is reported and the user says **"go"** again.

## Custom mod architecture

Prefer **one NeoForge integration mod with internal modules/adapters**. Core logic depends on DrewCraft contracts; third-party implementation types stay in adapters/compat modules. Major subsystems require feature flags, bounded behavior, diagnostics, versioned persistence where relevant, and restart/unload/failure tests.

## Performance contract for BP9

Measure representative worst-normal-case workload, including multiple players, Atmosphere/Simple Clouds, Distant Horizons clients, Create machinery/train, MTS road+aircraft, multiple distant strategic groups/herds, one materialized army, siege, Create radar, and ordinary local mobs/spawners.

Capture at minimum server MSPT p50/p95/p99, long ticks, CPU, heap/native memory, GC, disk I/O, network, save/backup duration, entity counts, strategic scheduler/routing/materialization/siege/radar costs, plus representative Windows/macOS client frame-time/FPS/memory.

Optimize caching/cadence/budgets before cutting gameplay. Never silently trade away strategic correctness to make benchmarks look good.

## User experience

The public-facing name is **DrewCraft**. The download site remains deliberately simple: one Windows button and one Mac button. Complexity belongs in the bootstrapper/updater, not in instructions to friends.
