# DrewCraft Implementation Roadmap

This is the high-level roadmap. The **canonical execution order and checklist** is `docs/v_1_development_tree.md`; the **hard V1 contract** is `docs/v_1_requirements.md`. Where this older/high-level document is less specific, those two V1 documents win.

DrewCraft should be built in layers that retire risky assumptions early. The defining rule is: **do not spend weeks polishing dependent gameplay systems before proving the pack, world, release pipeline, host, and integration boundaries they depend on.**

DrewCraft V1 is **feature-complete and integration-complete, not balance-complete**. Broad recipe/economy/difficulty tuning is post-V1 unless an upstream default clearly destroys a core design pillar.

## Phase 0 — Reproducible repository and upstream ownership

Goal: a clean machine can identify and reproduce one exact development pack from the repository.

Build:

- canonical pack manifest
- Minecraft 1.21.1 / NeoForge / Java 21 lock
- upstream dependency/source registry
- ownership classification for every direct/transitive dependency
- mod/content-pack inventory with exact versions and hashes before promotion
- common/client/server/operational separation
- pack build and verification scripts
- `.gitignore` for generated/binary state
- CI schema/build checks

Rules:

- track every official upstream source;
- fork only when DrewCraft must maintain a real source patch;
- do not vendor every upstream repo merely for packaging convenience.

Exit gate:

- no developer machine's `mods/` folder is needed to reproduce the pack
- every baseline dependency has one documented responsibility and does not duplicate another authoritative subsystem

## Phase 1 — Core compatibility lock

Goal: verify the proposed foundation together before custom feature work.

Test the smallest viable stack containing:

- Terrain Diffusion Plus
- Chunky as pregeneration tooling
- Distant Horizons
- Create
- Immersive Vehicles plus the smallest curated content-pack set providing at least one useful road vehicle and one aircraft
- Project Atmosphere
- Simple Clouds
- Serene Seasons where required/stable with the selected Atmosphere release
- required support libraries

Responsibility rules:

- Terrain Diffusion owns overworld terrain/climate/caves; no second cave/terrain overhaul by default
- Create owns rail/industrial infrastructure
- MTS owns road vehicles and aircraft, not a competing train system
- Project Atmosphere owns atmospheric state
- Simple Clouds supplies the cloud/local-weather rendering substrate under Atmosphere integration
- Serene Seasons owns the season calendar/hooks where used
- DrewCraft owns radar, strategic populations, armies, herds and siege behavior

Required tests:

- dedicated server boot
- Windows client connection
- Apple Silicon macOS connection
- Terrain Diffusion world creation/loading
- Create contraption and train
- car/truck
- aircraft
- dynamic weather/cloud stack
- Distant Horizons
- clean restart/rejoin
- log audit for registry/mixin/network errors

Exit gate:

- one known-good exact mod/content lock exists and is committed

## Phase 2 — Production world pipeline

Goal: prove that the World Scale 2 world is operationally manageable.

Work:

- benchmark candidate world radii before choosing the production border
- generate production candidate using exact locked generation pack
- pre-generate with Chunky on capable hardware
- record world identity, seed/settings, world scale, border and generation pack version
- validate rivers, mountains, structures, Terrain Diffusion cave behavior, Nether and End
- archive world
- generate checksums
- restore archive onto a clean server
- measure compressed size, disk size, backup time and restore time

Exit gate:

- a reproducible world artifact can be generated, uploaded, restored and verified

## Phase 3 — Real host / ARM / performance gate

Goal: determine whether the preferred low-cost host is actually suitable rather than designing around assumptions.

Oracle Ampere A1 is the first benchmark target, not a V1 identity requirement.

Verify especially:

- ARM64 Java 21
- Terrain Diffusion native/ONNX runtime behavior
- pregenerated chunk loading
- weather stack
- Create
- MTS server behavior
- representative multiplayer load

Measure:

- MSPT/tick percentiles
- CPU saturation
- heap/native memory
- GC pauses
- disk I/O
- network
- save/restart time

Exit A:

- preferred A1 target is acceptably playable -> keep it

Exit B:

- it is not acceptable -> intentionally choose a larger/alternate fixed host

Never hide a failed benchmark behind automatic paid scaling.

## Phase 4 — Release artifact contract

Goal: give the launcher, CI and server updater one immutable release language.

Implement:

- versioned `release-manifest.json`
- stable-channel pointer
- deterministic client pack
- deterministic server pack
- SHA-256 verification
- pack/protocol/Minecraft/loader versions
- separate world artifact identity

Exit gate:

- CI can produce and independently verify a synthetic DrewCraft release.

## Phase 5A — One-click DrewCraft installer

Goal: a non-technical friend can install the exact pack without learning Java, NeoForge or Prism.

Implement:

- Windows bootstrapper
- macOS bootstrapper/app
- managed Java 21
- managed Prism installation/instance
- Microsoft login delegated to Prism
- per-file hash verification
- staged/atomic pack updates
- repair mode
- server-version/readiness check
- useful user-facing errors

Website target:

- DrewCraft
- one Windows button
- one Mac button
- no normal setup guide required

Exit gate:

- clean Windows and Apple Silicon machines can install, authenticate, update and join from the DrewCraft page

## Phase 5B — Server deployment and update automation

Goal: client and server never drift into incompatible pack states.

Implement:

- server install script
- systemd service
- health/version endpoint
- server updater
- staged verified releases
- controlled restart policy
- backup-before-update
- startup health verification
- safe application rollback
- off-host backups
- documented restore procedure

Exit gate:

- publish a test pack update and demonstrate client/server convergence without manual mod copying

## Phase 6 — DrewCraft integration-mod platform

Goal: establish stable APIs and persistence before complicated gameplay.

Build:

- NeoForge mod skeleton
- protocol/version handshake
- configuration system
- versioned SavedData persistence
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

- mod builds in CI, connects client/server, persists test state and starts with integrations enabled/disabled cleanly

## Phase 7 — Weather and aviation integration

Goal: make the existing atmospheric system materially affect supported aircraft.

Implement in order:

1. internal weather-sampling adapter
2. wind vector exposure
3. aircraft wind effects
4. crosswind/headwind/tailwind behavior
5. bounded turbulence
6. terrain/elevation contribution
7. storm/severity contribution
8. synchronization and conservative defaults

Exit gate:

- one supported aircraft has stable server-authoritative weather effects

## Phase 8 — Physical weather radar

Goal: create physical sensing infrastructure based on the same real Atmosphere state.

MVP blocks:

- radar dish
- radar controller
- Create-powered adapter
- data/power cable
- physical radar display

MVP mechanics:

- physical connectivity
- range cap
- height-dependent horizon
- coarse terrain masking
- Project Atmosphere precipitation/severity product
- shared cached scan per controller
- physical display rendering
- aircraft radar using the same data pipeline

Exit gate:

- differently sited installations show meaningfully different coverage and correctly display an approaching real weather system

## Phase 9 — Strategic world kernel

Goal: prove unloaded-chunk persistence before attempting armies.

Implement:

- strategic IDs/state schema
- coarse simulation clock
- route/ETA engine
- persistence
- admin inspection commands
- materialization transaction
- casualty tracking
- dematerialization
- restart safety

Test scenario:

1. create a group far from players
2. advance it while destination chunks are unloaded
3. ETA changes consistently
4. player encounters it
5. it materializes exactly once
6. casualties are recorded
7. area unloads
8. survivors remain reduced
9. restart server
10. group continues correctly

Exit gate:

- no duplication, reset or teleport behavior

## Phase 10 — Hostile source lifecycle

Implement:

- sparse generated structure/source indexing
- explicit source-clear objective
- population/reinforcement budget
- launch cooldowns
- target selection
- permanent cleared state
- player/admin feedback

Exit gate:

- an intact source can produce strategic threats and a legitimately cleared source cannot silently resume them

## Phase 11 — Multiple hostile forces and armies

Add:

- composition summaries
- multiple hostile mob families/factions
- patrols, hordes and armies
- roles/unit classes
- merge/split/reinforcement only where useful
- materialization caps/waves where required for performance

Exit gate:

- a convincingly large persistent force can approach and fight without requiring its full strategic population to remain loaded

## Phase 12 — Siege planning

Implement in layers:

1. normal path-to-objective planning
2. entrance/gate/road preference
3. inaccessible-target detection
4. constrained breach-corridor calculation
5. siege-capable unit assignment
6. hardness/time-based breach
7. protected block tags
8. plan cache/invalidation

Critical tests:

- open gate -> mobs use it; no wall damage
- usable weak entrance -> prefer it
- fully sealed fort -> deliberate breach
- nearby decorative statue off route -> untouched
- breach opens a genuinely navigable path

Exit gate:

- defenders benefit from architecture and mobs do not vandalize arbitrary builds

## Phase 13 — Strategic animal herds and local-spawn coexistence

Implement:

- strategic herd records
- species/count/home-range data
- coarse movement
- nearby materialization
- safe summarization on unload
- coexistence tests with ordinary hostile spawning, caves, mob farms and ordinary spawners

Do not add a second persistent ecology/horde simulator.

Exit gate:

- herds make unloaded geography feel inhabited while ordinary Minecraft ecology remains intact

## Phase 14 — Cross-system integration and conservative defaults

Goal: prove that the systems work together without doing the post-V1 balance pass.

Test:

- Terrain Diffusion -> weather/aviation terrain inputs
- Atmosphere -> flight + ground radar + aircraft radar
- Create -> radar power
- source -> strategic group -> materialization -> siege
- source clearing -> future threat suppression
- strategic herds alongside normal local mobs
- launcher/server release compatibility
- failure of one custom subsystem with its kill switch

Set only conservative safety/performance defaults needed for a playable V1, such as caps that prevent constant armies or excessive planners. Do not redesign the game's economy here.

Exit gate:

- every V1 vertical slice operates on the same candidate release.

## Phase 15 — Hardening and V1

Before `1.0.0`:

- Windows fresh-install test
- Apple Silicon fresh-install test
- Intel Mac only if supported
- automatic upgrade from older development pack versions
- backup/restore drill including strategic state
- world expansion drill
- crash/restart tests during strategic encounters/materialization
- source persistence tests
- siege grief-safety tests
- radar performance tests
- complete-stack multiplayer performance test
- mod-license/redistribution audit
- macOS signing/notarization for final UX
- release notes and rollback procedures

## V1 definition

DrewCraft V1 is reached when:

- joining/updating is one-click enough for non-technical friends
- the large pre-generated world runs reliably
- roads/cars, Create rail and aircraft function as real transport options
- weather affects aviation
- physical radar provides useful real weather information
- distant hostile sources create persistent moving threats
- armies can arrive from unloaded geography
- clearing sources matters permanently
- castles have functional defensive value
- block breaching is constrained and understandable
- strategic animal herds exist
- ordinary Minecraft spawning/farming/building remains intact
- server updates and backups are boring and reliable

V1 does **not** require a perfected recipe/economy/difficulty curve.

## Post-V1 / V1.1+ — Balance and progression pass

Only after playing the complete V1 system should DrewCraft broadly tune:

- vehicle acquisition costs
- fuel economics
- repair/maintenance costs
- train economics
- aircraft cost and airport requirements
- road usefulness
- exact source density and army frequency/difficulty
- radar crafting/tier progression
- ship role if a stable ship implementation exists
- Nether portal distance/compression beyond any minimal V1 pillar-preserving rule

The purpose of V1.1+ is to make the already-complete systems balanced, not to finish missing V1 architecture.
