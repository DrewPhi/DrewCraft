# DrewCraft Implementation Roadmap

DrewCraft should be built in layers that prove risky assumptions early. The defining rule is: **do not spend weeks polishing custom world simulation before proving the core mod stack, huge world, ARM hosting, and one-click installation actually work together.**

## Phase 0 — Reproducible repository

Goal: a clean machine can reproduce one exact development pack from this repository.

Build:

- canonical pack manifest
- Minecraft 1.21.1 / NeoForge / Java 21 lock
- mod/content-pack inventory with exact versions and hashes
- common/client/server separation
- pack build and verification scripts
- `.gitignore` for generated/binary state
- CI schema/build checks

Exit gate:

- no developer machine's `mods/` folder is needed to reproduce the pack

## Phase 1 — Core compatibility spike

Goal: verify the proposed foundation together before custom feature work.

Test the smallest viable locked stack containing:

- Terrain Diffusion Plus
- Chunky
- Distant Horizons
- Create
- Immersive Vehicles plus one car and one aircraft content pack
- Project Atmosphere
- Simple Clouds
- Serene Seasons
- required libraries

Required tests:

- dedicated server boot
- Windows client connection
- Apple Silicon macOS connection
- Terrain Diffusion world creation/loading
- Create contraption and train
- car
- aircraft
- dynamic weather
- Distant Horizons
- clean restart/rejoin
- log audit for registry/mixin/network errors

Exit gate:

- one known-good mod lock exists and is committed

## Phase 2 — Production world pipeline

Goal: prove that the enormous World Scale 2 world is operationally manageable.

Work:

- settle initial playable border from benchmarks
- generate production candidate using exact locked generation pack
- pre-generate with Chunky on capable hardware
- record seed/settings/world-scale/border/generation pack version
- validate rivers, mountains, structures, caves, Nether, and End
- archive world
- generate checksums
- restore archive onto a clean server
- measure compressed size, disk size, backup time, restore time

Exit gate:

- a reproducible world artifact can be generated, uploaded, restored, and verified

## Phase 3 — Oracle ARM viability gate

Goal: determine whether Oracle Ampere A1 is actually suitable rather than assuming Java portability means the entire stack is safe.

Test on the current free target:

- ARM64 Linux
- 2 OCPU
- 12 GB RAM total tenancy allowance if using one free A1 VM
- Java 21 ARM64
- pre-generated production-world copy

Verify especially:

- Terrain Diffusion native/ONNX dependencies load on ARM64
- generated chunks load normally
- weather stack operates
- Create operates
- Immersive Vehicles operates server-side
- several representative players/chunks
- no severe GC or native-memory problem

Measure:

- MSPT/tick percentiles
- CPU saturation
- Java heap
- native memory
- GC pause time
- disk I/O
- network
- save/restart time

Exit A:

- free A1 is acceptably playable → keep it as production target

Exit B:

- free A1 is not acceptable → explicitly choose a larger/alternate host

Never hide a failed benchmark behind automatic paid scaling.

## Phase 4 — One-click DrewCraft installer MVP

Goal: a non-technical friend can install the exact pack without learning Java, NeoForge, or Prism.

Implement:

- release manifest schema
- generated client/server release artifacts
- Windows bootstrapper
- macOS bootstrapper/app
- managed Java 21
- managed Prism installation/instance
- Microsoft login delegated to Prism
- per-file hash verification
- staged/atomic pack updates
- repair damaged installations
- server-version/readiness check
- useful user-facing errors

Website target:

- `DrewCraft`
- one Windows button
- one Mac button
- no setup guide required during normal operation

Exit gate:

- clean Windows and clean Apple Silicon machines can install, authenticate, and join from the DrewCraft page

## Phase 5 — Server deployment and update automation

Goal: client and server never drift into incompatible pack states.

Implement:

- server install script
- systemd service
- server health/version endpoint
- server updater
- staged verified server releases
- zero-player controlled restart policy
- backup-before-update
- startup health verification
- safe rollback of application files
- off-VM backups
- documented restore procedure

Exit gate:

- publish a test pack update and demonstrate automatic/near-automatic server + client convergence without manual mod copying

## Phase 6 — Custom `drewcraft` / `servermc` integration mod skeleton

Goal: establish stable APIs and persistence before implementing complicated gameplay.

Build:

- NeoForge mod skeleton
- protocol/version handshake
- configuration system
- SavedData/versioned persistence
- compatibility-adapter interfaces
- commands/observability
- subsystem feature flags
- tests

Adapters:

- Terrain Diffusion
- Project Atmosphere
- Immersive Vehicles
- Create

Exit gate:

- mod builds in CI, connects client/server, persists test state, and starts with optional integrations disabled/enabled correctly

## Phase 7 — Weather and aviation integration

Goal: make weather materially affect travel before building radar.

Implement in order:

1. internal weather-sampling adapter
2. wind vector exposure
3. aircraft wind effects
4. bounded turbulence model
5. terrain/elevation contribution
6. storm/severity contribution
7. synchronization and tuning

Playtest questions:

- can players feel a crosswind without controls becoming annoying?
- can storms be avoided intentionally?
- does mountainous flight feel different?
- are effects predictable enough to learn?

Exit gate:

- one supported aircraft has stable server-authoritative weather effects

## Phase 8 — Physical weather radar

Goal: create the first major infrastructure system unique to DrewCraft.

MVP blocks:

- radar dish
- radar controller
- Create-powered adapter
- data/power cable
- radar display

MVP mechanics:

- physical connectivity
- tier range cap
- height-dependent horizon
- coarse terrain masking
- Project Atmosphere precipitation/severity product
- shared cached scan per controller
- physical display rendering

Then add:

- better tiers
- storm motion
- aircraft radar
- richer products if useful

Exit gate:

- two installations at different useful antenna heights demonstrate meaningfully different coverage and correctly display an approaching storm

## Phase 9 — Strategic world simulation MVP

Goal: prove unloaded-chunk persistence using one simple hostile group before attempting armies.

Implement:

- source registry
- one source type
- one strategic group type
- coarse movement
- route/ETA
- persistence
- admin inspection commands
- materialization
- casualty tracking
- dematerialization
- restart safety

Test scenario:

1. source launches a group far from players
2. server advances it while destination chunks are unloaded
3. command-reported ETA changes consistently
4. player meets group
5. group materializes exactly once
6. player kills part of it
7. area unloads
8. surviving strength remains reduced
9. restart server
10. remaining group continues correctly

Exit gate:

- no duplication, reset, or teleport behavior across all steps

## Phase 10 — Hostile source lifecycle

Goal: make conquest alter the long-term world.

Implement:

- structure/source indexing
- explicit source-clear objective
- reinforcement/population budget
- launch cooldowns
- target selection
- permanent cleared state
- player/admin feedback that a source is neutralized

Exit gate:

- a source can attack repeatedly while intact and cannot produce another force after being legitimately cleared

## Phase 11 — Army composition and large encounters

Goal: scale the strategic representation beyond a small horde without scaling distant entity count.

Add:

- composition summaries
- roles/unit classes
- patrols vs hordes vs armies
- reinforcement/merge/split behavior if useful
- materialization caps/waves if required for performance
- multiple hostile mob families/factions

Performance rule:

- army size in strategic state does not imply all members must be loaded simultaneously if doing so would destroy TPS

Exit gate:

- a convincingly large strategic force can approach and fight without permanently exhausting server resources

## Phase 12 — Siege planning

Goal: make castles function as defenses without enabling random griefing.

Implement in layers:

1. normal path-to-objective planning
2. entrances/gates/roads preference
3. detect inaccessible target
4. calculate constrained breach corridor
5. assign breach-capable units
6. hardness/time-based breach
7. protected block tags
8. plan cache/invalidation

Critical tests:

- open gate → mobs use gate, no wall damage
- closed accessible door/weak entrance → prefer it appropriately
- fully sealed fort → planned breach
- nearby decorative statue not on route → untouched
- breach opens an actually navigable path

Exit gate:

- defenders benefit from architecture and mobs do not vandalize arbitrary builds

## Phase 13 — Herds and broader living world

Goal: apply the same strategic-state architecture to peaceful populations.

Implement:

- strategic herd record
- species/count/home-range data
- coarse movement
- nearby materialization
- safe summarization on unload

Only add nearby-herd AI mods if they improve behavior without duplicating the strategic layer or exploding entity count.

## Phase 14 — Transportation/progression balance

Goal: ensure every transportation tier remains useful after the complete world is in place.

Tune:

- vehicle costs
- fuel costs
- train economics
- road usefulness
- aircraft acquisition and operation cost
- runway/airport requirements
- ship role if a compatible ship implementation passes testing
- Nether portal distance ratio if vanilla 8:1 bypasses the entire progression

Desired result:

- cars beat walking on developed routes
- trains beat cars for repeated heavy logistics
- aircraft beat both for enormous distances but require far more infrastructure/cost
- Nether remains useful without being the universal optimal answer

## Phase 15 — Hardening and 1.0

Before 1.0:

- Windows fresh-install test
- Apple Silicon fresh-install test
- Intel Mac test if supported
- automatic upgrade from multiple older pack versions
- backup restore drill
- world expansion drill
- server crash/restart tests during strategic encounters
- hostile-source persistence tests
- siege grief-safety tests
- radar performance tests
- several-player performance test
- mod-license/redistribution audit
- signing/notarization for final macOS UX
- release notes and rollback procedures

## 1.0 definition

DrewCraft 1.0 is not "all desired mods installed."

It is reached when:

- joining is one-click enough for non-technical friends
- the huge world runs reliably
- transport progression works
- weather affects aviation
- physical radar provides useful information
- distant hostile sources create persistent moving threats
- armies can arrive from unloaded geography
- clearing sources matters permanently
- castles have functional defensive value
- block breaching is constrained and understandable
- ordinary Minecraft spawning/farming/building remains intact
- server updates and backups are boring and reliable

That is the finish line.