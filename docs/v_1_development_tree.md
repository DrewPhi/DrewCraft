# DrewCraft V1 Development Tree and Execution Checklist

This document is the **canonical execution order from the repository's current state to DrewCraft V1**. It complements `v_1_requirements.md`, which defines *what V1 must contain*. This file defines **what to build first, what depends on what, what may proceed in parallel, and what must be proven before the next layer is trusted**.

The governing principle is:

> **Retire existential risks before polishing dependent systems. Build thin vertical slices before adding breadth. Never allow a later subsystem to hide an unproven lower layer.**

V1 remains **feature-complete and integration-complete, not balance-complete**. Do not block V1 on broad recipe, fuel-cost, spawn-rate, economy, or difficulty tuning unless an upstream default actively breaks a core DrewCraft design pillar.

---

# 0. Current state

As of the creation of this plan, the repository is still primarily in the specification stage.

Already present:

- [x] project/product specification
- [x] systems architecture
- [x] mod-stack policy
- [x] repository architecture
- [x] launcher/hosting architecture
- [x] high-level roadmap
- [x] explicit V1 requirements
- [x] simple DrewCraft landing-page HTML
- [x] GitHub Pages deployment workflow

Not yet present as implementation trees:

- [ ] `pack/`
- [ ] `mods/`
- [ ] `launcher/`
- [ ] `server/`
- [ ] `infra/`
- [ ] `world/`
- [ ] `tools/`
- [ ] `tests/`
- [ ] full CI/release workflows

GitHub Pages is not a V1 technical dependency. The website may remain disabled until installers exist.

---

# 1. Dependency tree

The following is the intended dependency structure. A child must not be treated as production-ready until its parent gate has passed.

```text
V1 CONTRACT + REPOSITORY BASELINE
│
├── A. REPRODUCIBLE PACK FOUNDATION
│   │
│   └── B. CORE MOD COMPATIBILITY LOCK
│       │
│       ├── C. PRODUCTION WORLD PIPELINE
│       │   └── D. HOST / ARM / PERFORMANCE BASELINE
│       │
│       └── E. RELEASE MANIFEST + PACK ARTIFACT PIPELINE
│           ├── F. CLIENT LAUNCHER TRACK
│           └── G. SERVER DEPLOYMENT / UPDATER TRACK
│
└── H. DREWCRAFT INTEGRATION MOD PLATFORM
    │
    ├── I. ENVIRONMENT ADAPTER TRACK
    │   ├── Terrain Diffusion adapter
    │   ├── Project Atmosphere adapter
    │   ├── Create power adapter
    │   └── Immersive Vehicles adapter
    │       │
    │       ├── J. AVIATION WEATHER
    │       └── K. WEATHER RADAR
    │
    └── L. STRATEGIC WORLD TRACK
        ├── persistence + IDs + coarse clock
        ├── route / ETA engine
        ├── materialization transaction
        │   │
        │   ├── M. HOSTILE SOURCES
        │   ├── N. ARMIES / MULTIPLE FACTIONS
        │   ├── O. SIEGE PLANNER
        │   └── P. ANIMAL HERDS
        │
        └── local-spawn coexistence

A-G + H-P
│
└── Q. CROSS-SYSTEM INTEGRATION
    └── R. RELEASE CANDIDATE / SOAK / RESTORE / FAILURE TESTS
        └── DREWCRAFT V1
```

The **critical path** is approximately:

```text
reproducible pack
→ compatibility lock
→ world pipeline
→ real host performance baseline
→ integration-mod platform
→ adapters
→ aviation/radar + strategic world
→ siege/herds
→ full-stack integration
→ release candidate
→ V1
```

The launcher and server-operations tracks should begin once the pack/release manifest is stable enough to consume. They can then proceed in parallel with custom gameplay systems.

---

# 2. Rules for every development phase

Every phase must obey these rules before its checkbox is considered complete.

- [ ] The implementation is committed to the repository or generated reproducibly from committed inputs.
- [ ] A developer can reproduce the result from a clean checkout without relying on an undocumented local folder.
- [ ] New behavior has an explicit test, smoke procedure, or measurable acceptance criterion.
- [ ] Failure behavior is understood; important custom subsystems have a kill switch where applicable.
- [ ] Logs do not contain unexplained registry, mixin, networking, serialization, or dependency errors.
- [ ] Persistent formats are versioned from their first committed use.
- [ ] Performance-sensitive work exposes enough timing/diagnostic information to detect regressions.
- [ ] The implementation does not introduce a second source of truth for data already owned by an upstream system.
- [ ] No broad game-balance work is added merely because a default recipe feels imperfect.

A phase gate is a **real gate**, not a documentation milestone. If the gate fails, fix the parent layer before continuing substantial work on children.

---

# 3. Stage 0 — Canonicalize the development baseline

## Goal

Make the repository unambiguous before implementation begins.

## Checklist

- [ ] Rename the GitHub repository to `DrewCraft` if that remains the desired repository name.
- [ ] Update old `ServerMc` user-facing references after the rename; retain old internal names only where deliberately chosen.
- [ ] Choose the permanent custom NeoForge mod ID/package naming strategy (`drewcraft` preferred for new code unless migration concerns justify `servermc`).
- [ ] Add `.gitignore` covering worlds, backups, logs, crash reports, runtimes, downloaded jars, Terrain Diffusion model assets, Distant Horizons databases, caches, secrets, and generated release artifacts.
- [ ] Create the top-level repository directories from `REPO_ARCHITECTURE.md`.
- [ ] Add a root development command entry point, e.g. `./tools/...` or a task runner, so common operations are discoverable.
- [ ] Define development version semantics: start with `0.x.y-dev`; reserve `1.0.0` for the V1 gate.
- [ ] Define `worldId`, `worldRevision`, `packVersion`, and custom persistence schema version as separate concepts.
- [ ] Add this document and `v_1_requirements.md` to `AGENTS.md` as mandatory reading.

## Exit gate

A new coding agent can clone the repository, identify the next unchecked work item, understand naming/version conventions, and know where every new artifact belongs.

---

# 4. Stage 1 — Reproducible pack foundation

## Why this comes first

Everything downstream depends on knowing exactly what “DrewCraft” means. Building bridges against a hand-maintained local `mods/` folder would make every later result irreproducible.

## Build

- [ ] Create `pack/manifest/pack.yaml` with pack ID/version, Minecraft 1.21.1, NeoForge, Java 21, schema version, and release channel.
- [ ] Create dependency manifests for mods, content packs, Java, and any legally redistributable resources.
- [ ] Give every dependency a canonical ID, source/provider, exact version, side, required/optional state, download identity, redistribution policy, and SHA-256.
- [ ] Separate `common`, `client`, and `server` configuration layers.
- [ ] Create a dependency resolver/downloader that fails closed on hash mismatch.
- [ ] Create a pack builder producing deterministic client and server trees.
- [ ] Create a verifier that detects missing files, unexpected files, duplicate mods, wrong side classification, and hash drift.
- [ ] Create an initial versioned `release-manifest.json` schema even before public releases exist.
- [ ] Add schema validation tests.
- [ ] Add CI that validates manifests and builds pack layouts without relying on developer-local state.

## Important design choices

The manifest is authoritative. Do not maintain a launcher mod list and a server mod list separately. Both must be projections of the same committed manifest.

Licensing must be handled here. The builder should support both artifacts we may redistribute and artifacts that must be fetched from the original provider during install/build.

## Exit gate

- [ ] Delete or move aside the developer's local test `mods/` folder.
- [ ] From a clean checkout, regenerate the same client/server dependency set.
- [ ] Verify every resulting artifact hash.
- [ ] Prove that changing one dependency changes the generated release identity predictably.

**Gate result:** one command can reproduce the exact development pack inputs.

---

# 5. Stage 2 — Minimal full-stack compatibility lock

## Goal

Find one exact set of upstream versions that actually coexist before we write significant DrewCraft-specific code.

## Initial test stack

- [ ] Terrain Diffusion Plus
- [ ] Chunky
- [ ] Distant Horizons
- [ ] Create
- [ ] Immersive Vehicles / MTS
- [ ] exactly one representative road vehicle content pack
- [ ] exactly one representative aircraft content pack
- [ ] Project Atmosphere
- [ ] Simple Clouds
- [ ] Serene Seasons if stable
- [ ] required libraries only

Do **not** add optional quality-of-life mods, structure packs, ship mods, or extra content until this base works.

## Compatibility matrix

Test every row and record pass/fail evidence:

- [ ] dedicated NeoForge server boots cleanly
- [ ] Windows client boots
- [ ] Apple Silicon macOS client boots
- [ ] client joins dedicated server
- [ ] clean restart and rejoin
- [ ] Terrain Diffusion world creates and generated chunks reload
- [ ] World Scale 2 behaves as expected
- [ ] Chunky can pregenerate without corrupting Terrain Diffusion output
- [ ] Distant Horizons operates with the generated world
- [ ] Distant Horizons and Simple Clouds render together acceptably
- [ ] Project Atmosphere weather progresses in multiplayer
- [ ] Serene Seasons does not destabilize weather/worldgen
- [ ] Create basic machines work
- [ ] Create train can be assembled, driven, unloaded/reloaded, and survives restart
- [ ] road vehicle works in multiplayer
- [ ] aircraft works in multiplayer before custom weather effects
- [ ] Nether and End remain functional
- [ ] no unexplained fatal/high-severity mixin or registry conflicts
- [ ] memory use is recorded on representative clients

## Optional dependency evaluation

Only after the base lock passes:

- [ ] evaluate a restrained navigation/map option if desired
- [ ] evaluate a large ship mod; mark it V1-optional immediately if stability is questionable
- [ ] evaluate any structure source content needed for hostile sites
- [ ] evaluate any local AI/spawn helper only if the custom strategic layer truly needs it

## Exit gate

Commit a **known-good lock** containing exact versions and hashes. No later dependency update is accepted without rerunning affected portions of this matrix.

---

# 6. Stage 3 — Production world pipeline

## Goal

Treat the world as a build artifact with identity, not as a folder that happened to exist on one computer.

## World-generation tooling

- [ ] Create `world/generation-config/` with Terrain Diffusion settings including World Scale 2.
- [ ] Store seed/world identity metadata where applicable.
- [ ] Store world-border/pregeneration parameters separately from runtime border settings.
- [ ] Script the Chunky pregeneration process.
- [ ] Record generation pack version and all worldgen-affecting dependencies.
- [ ] Produce machine-readable world metadata.
- [ ] Generate archive checksums.
- [ ] Build a restore/verification tool that rejects the wrong archive/hash.

## World-size experiment before final pregeneration

Do not immediately generate the largest imaginable map.

- [ ] Generate representative smaller radii.
- [ ] Measure chunk count, generation time, archive size, expanded disk size, backup time, restore time, and server save behavior.
- [ ] Inspect mountains, rivers, valleys, coastlines, climate transitions, caves, structures, and empty-space frequency.
- [ ] Estimate the initial production border from measured storage/backup/operational costs.
- [ ] Verify that the chosen size is large enough to justify cars, trains, aircraft, strategic travel, and radar infrastructure.

## Production candidate

- [ ] Generate the first production candidate using the exact locked generation pack.
- [ ] Validate Overworld samples across widely separated regions.
- [ ] Validate Nether and End.
- [ ] Validate source-structure candidates if already selected.
- [ ] Archive the world.
- [ ] Restore it into a completely clean server installation.
- [ ] Compare expected identity/checksums/metadata.

## Exit gate

The world can be destroyed locally, restored from documented artifacts, and booted again without hidden state.

---

# 7. Stage 4 — Real deployment and performance baseline

## Goal

Determine the server constraints **before** designing expensive strategic/radar systems around imaginary compute.

Oracle Ampere A1 remains the first benchmark target, not a sacred requirement.

## Infrastructure baseline

- [ ] Create reproducible host setup under `infra/`.
- [ ] Provision ARM64 Java 21.
- [ ] Harden basic networking/firewall/SSH exposure.
- [ ] Create dedicated non-root service user.
- [ ] Create server directories with clear separation between application release and persistent world state.
- [ ] Create systemd service.
- [ ] Deploy a restored pregenerated world.

## ARM compatibility gate

- [ ] Terrain Diffusion/ONNX/native libraries load on ARM64.
- [ ] Pregenerated chunks load normally.
- [ ] Minimal accidental generation does not crash the server.
- [ ] Create operates.
- [ ] Project Atmosphere operates.
- [ ] MTS server behavior operates.
- [ ] normal restart/save is clean.

If a required native dependency fails, resolve host architecture or runtime strategy **here**, not after custom gameplay is built.

## Performance baseline

Create a repeatable benchmark scenario and record:

- [ ] idle MSPT
- [ ] active-player MSPT percentiles
- [ ] CPU saturation
- [ ] heap usage
- [ ] native memory
- [ ] GC pauses
- [ ] disk I/O
- [ ] network use
- [ ] save duration
- [ ] restart duration
- [ ] representative Create train/contraption cost
- [ ] representative vehicles cost
- [ ] weather cost

Store benchmark scripts/results in `tests/performance/` or documented artifacts.

## Exit gate

Choose one explicit production target:

- **PASS:** constrained/free ARM target is acceptable; or
- **MIGRATE:** select a larger/alternate fixed host intentionally.

Never compensate with silent autoscaling.

---

# 8. Stage 5 — Release artifact contract

## Goal

Establish the contract that launcher, server updater, CI, and future releases all consume.

## Checklist

- [ ] Finalize versioned `release-manifest.json` schema.
- [ ] Include pack version, protocol version, Minecraft version, NeoForge version, minimum launcher version, file hashes, side, artifact URLs, and artifact hashes.
- [ ] Add stable-channel pointer format (`live.json` or equivalent).
- [ ] Build deterministic client pack artifact.
- [ ] Build deterministic server pack artifact.
- [ ] Generate checksums.
- [ ] Generate release notes metadata.
- [ ] Validate every URL/hash before promotion.
- [ ] Never publish `live.json` until all required release checks pass.
- [ ] Separate world artifact identity from pack artifact identity.

## Exit gate

A synthetic development release can be generated from CI inputs and independently verified without installing it manually.

---

# 9. Stage 6A — Launcher track

This track may proceed in parallel with custom gameplay after Stage 5.

## MVP architecture

Use Prism as the underlying Minecraft launch engine. Do not implement Microsoft authentication or the Minecraft launcher protocol from scratch.

- [ ] Choose implementation language/framework with reliable Windows + macOS native packaging.
- [ ] Implement platform/architecture detection.
- [ ] Implement managed application data directory.
- [ ] Implement managed Java 21 acquisition with hash verification.
- [ ] Implement managed Prism acquisition or supported discovery.
- [ ] Create/import the DrewCraft Prism instance programmatically.
- [ ] Consume the release manifest.
- [ ] Download missing/changed files only.
- [ ] Verify hashes before activation.
- [ ] Stage updates outside the active instance.
- [ ] Atomically switch/promote a verified instance.
- [ ] Preserve user-owned data.
- [ ] Retain a previous known-good application version for rollback/repair.
- [ ] Implement repair mode.
- [ ] Implement useful error messages and log-export path.

## Server-awareness

- [ ] Query safe server health/version state.
- [ ] Handle ready, offline, updating, stale-client, incompatible-client, and newer-server conditions.
- [ ] Never place cloud/SSH/admin credentials in the client.

## Platform gates

- [ ] clean Windows install
- [ ] clean Apple Silicon install
- [ ] Microsoft login through Prism
- [ ] launch game
- [ ] join development server
- [ ] close launcher/game
- [ ] publish a pack update
- [ ] relaunch after update and converge automatically
- [ ] intentionally corrupt/delete a managed file and repair it
- [ ] interrupt an update and verify old installation remains usable

Intel Mac is optional unless explicitly promoted to supported V1 status.

## Final packaging gate

Before V1:

- [ ] Windows installer artifact has stable release naming.
- [ ] macOS `.app`/DMG packaging is non-technical-user friendly.
- [ ] macOS signing/notarization is completed if required for the promised experience.
- [ ] website buttons point at real latest-release assets.

---

# 10. Stage 6B — Server deployment/update track

This track may also proceed in parallel after Stage 5.

## Install/runtime

- [ ] reproducible server install script
- [ ] systemd unit
- [ ] pinned Java runtime behavior
- [ ] persistent-data directories separated from release directories
- [ ] log rotation
- [ ] health/version endpoint containing only safe data

## Update transaction

- [ ] detect selected release
- [ ] download to staging
- [ ] verify artifact/file hashes
- [ ] wait for approved maintenance condition
- [ ] create backup before update
- [ ] cleanly stop Minecraft
- [ ] atomically switch application release
- [ ] start Minecraft
- [ ] verify health/version
- [ ] roll back application files on failed boot
- [ ] never blindly roll back world data after it may have been migrated

## Backup/restore

Backups must include world + strategic state + mod world state + player data + release identity.

- [ ] local backup rotation
- [ ] off-VM backup copy
- [ ] checksums
- [ ] retention policy
- [ ] restore into a clean VM/test host
- [ ] verify custom persistence after restore

## Exit gate

Publish a test release and prove that the server and two clean clients converge on it without hand-copying mods.

---

# 11. Stage 7 — DrewCraft integration-mod platform

## Why the platform comes before feature code

Weather, radar, sources, armies, herds, and sieges all require the same primitives: compatibility adapters, versioned persistence, networking, configuration, IDs, observability, and feature flags. Build these once correctly.

## Mod skeleton

- [ ] create `mods/drewcraft/` (or final chosen mod path)
- [ ] NeoForge 1.21.1 Gradle project
- [ ] build in CI
- [ ] run on dedicated server and client
- [ ] explicit protocol version
- [ ] client/server compatibility handshake
- [ ] common/server/client configuration split
- [ ] feature-flag registry
- [ ] structured logging conventions
- [ ] admin command root
- [ ] GameTest/unit-test foundation where practical

## Persistence platform

- [ ] versioned SavedData/equivalent store
- [ ] stable UUID/ID strategy for sources, groups, encounters, radar networks as appropriate
- [ ] schema-version field from day one
- [ ] migration mechanism
- [ ] crash/restart-safe save behavior
- [ ] test state survives clean restart
- [ ] invalid/corrupt state fails visibly rather than silently resetting the world

## Adapter interfaces

Define internal interfaces before implementing upstream-specific details:

- [ ] terrain/climate provider
- [ ] weather provider
- [ ] vehicle/aircraft adapter
- [ ] Create power adapter
- [ ] structure/source discovery adapter
- [ ] entity materialization adapter

## Observability

At minimum establish command/API skeletons for:

- [ ] `/drewcraft version`
- [ ] weather sample
- [ ] radar inspect
- [ ] strategic group list/inspect/ETA
- [ ] source list/inspect
- [ ] siege inspect
- [ ] performance timing summary

## Exit gate

The mod can be installed in the locked pack, complete a protocol handshake, persist a test record across restart, expose diagnostics, and boot with each optional integration toggled on/off appropriately.

---

# 12. Stage 8 — Environment adapters

## Goal

Create one stable DrewCraft representation for environment data so later systems never depend directly on scattered upstream internals.

## Terrain Diffusion adapter

- [ ] expose elevation
- [ ] expose biome/climate information that is actually available/stable
- [ ] expose coarse slope/terrain samples needed by turbulence and strategic routing
- [ ] provide safe fallback behavior when detailed climate fields are unavailable
- [ ] cache static data rather than repeatedly querying expensive worldgen internals
- [ ] add debug sampling command

## Project Atmosphere adapter

- [ ] expose wind vector
- [ ] precipitation/intensity
- [ ] storm/severity signal
- [ ] visibility signal
- [ ] temperature/pressure/humidity only where useful and stable
- [ ] cloud/storm motion where available
- [ ] server-authoritative sample semantics
- [ ] debug sampling command

## Create adapter

- [ ] define a minimal DrewCraft powered-state/power-budget abstraction
- [ ] convert valid Create kinetic input into that abstraction
- [ ] stop power when mechanical input disappears
- [ ] avoid pretending Create has a generic electricity API it does not have

## Immersive Vehicles adapter

- [ ] identify supported aircraft/vehicle integration hooks
- [ ] isolate all MTS-specific code in compat layer
- [ ] expose aircraft state needed by weather/radar
- [ ] ensure failure does not crash unrelated DrewCraft features

## Exit gate

All four adapters produce inspectable real data in a multiplayer dedicated-server session, with no gameplay effects yet required.

---

# 13. Stage 9 — Aviation weather vertical slice

## Build in this exact order

- [ ] apply uniform wind to one supported aircraft
- [ ] verify server/client authority and smoothness
- [ ] demonstrate headwind/tailwind ground-speed difference
- [ ] demonstrate crosswind
- [ ] add bounded atmospheric turbulence
- [ ] add storm-severity contribution
- [ ] add terrain/elevation/gradient contribution
- [ ] add reduced-visibility behavior where integration permits
- [ ] expose debug telemetry for current weather effects
- [ ] add config bounds/kill switch

## Acceptance tests

- [ ] same aircraft flying reciprocal headings in wind has meaningfully different ground travel time
- [ ] crosswind is observable without making aircraft uncontrollable
- [ ] calm conditions remain calm
- [ ] storm conditions are perceptibly rougher
- [ ] mountain flight can differ from flat-terrain flight
- [ ] disabling aviation weather returns upstream vehicle behavior
- [ ] multiplayer observers/clients do not diverge catastrophically

## Exit gate

One supported aircraft can make a long trip where choosing route/timing based on real Project Atmosphere weather is useful.

Do not balance aircraft acquisition costs here.

---

# 14. Stage 10 — Ground radar vertical slice

## Build minimal physical system first

- [ ] radar dish block/entity
- [ ] radar controller block/entity
- [ ] Create-driven power adapter block/network integration
- [ ] simple data/power cable connectivity
- [ ] physical radar display block
- [ ] controller-owned cached scan product
- [ ] multiple displays subscribe to the same scan

## Scan pipeline

- [ ] sample actual Project Atmosphere precipitation/severity
- [ ] map samples into a bounded radar grid/product
- [ ] implement equipment maximum range
- [ ] implement height-dependent effective horizon
- [ ] implement coarse terrain masking
- [ ] cache polar terrain horizon or equivalent
- [ ] invalidate terrain mask only when necessary
- [ ] rate-limit scan updates
- [ ] enforce server-configured maximum work

## Physical behavior tests

- [ ] unpowered radar does not scan
- [ ] broken connection disables appropriate components
- [ ] one controller with multiple displays does not multiply scan work
- [ ] low valley installation has worse useful coverage than well-sited high installation
- [ ] terrain blocks coverage in expected sectors
- [ ] radar image corresponds to actual approaching weather
- [ ] moving storm changes display over time
- [ ] restarting server preserves configuration as needed

## Aircraft radar

Only after ground radar's shared data pipeline is stable:

- [ ] reuse the same atmospheric product pipeline
- [ ] connect one supported aircraft instrument
- [ ] constrain range/update behavior appropriately
- [ ] test while aircraft is moving

## Exit gate

A player can see a storm in the distance, observe it on a physically powered radar display, and make an aviation decision using that information.

---

# 15. Stage 11 — Strategic world simulation kernel

## Goal

Prove unloaded persistence with the smallest possible strategic group before building factions, cities, armies, or sieges.

## Data model

- [ ] `SourceRecord`
- [ ] `StrategicGroup`
- [ ] strategic position representation
- [ ] route representation
- [ ] destination/objective representation
- [ ] composition/strength summary
- [ ] group state machine
- [ ] last-simulated timestamp
- [ ] encounter/materialization state
- [ ] schema version

## Simulation clock

- [ ] coarse scheduled updates, not every game tick
- [ ] elapsed-time advancement
- [ ] deterministic bounded catch-up after restart
- [ ] maximum catch-up safeguards for absurd clock gaps
- [ ] instrumentation for simulation work/time

## Strategic routing

Start simple but architect for richer costs.

- [ ] define cell resolution (chunk or coarser)
- [ ] build/access coarse terrain cost data
- [ ] distinguish at least traversable land, difficult terrain/slope, water, and blocked regions
- [ ] compute route
- [ ] advance along route by distance/time
- [ ] derive ETA from remaining route cost
- [ ] cache routes
- [ ] invalidate/recompute only when needed

Road/bridge influence may be added once the base route engine is correct; do not require global rescans every tick.

## Admin simulation first

Before automatic sources launch anything:

- [ ] command creates a test strategic group
- [ ] command assigns destination
- [ ] command inspects route and ETA
- [ ] unloaded group advances correctly
- [ ] server restart preserves position/progress

## Exit gate

A test group travels a known long distance across entirely unloaded geography and arrives near its predicted ETA without teleporting.

---

# 16. Stage 12 — Materialization/dematerialization transaction

This is one of the highest-risk correctness areas. Solve it before automatic armies.

## Materialization transaction

- [ ] lock group as materializing
- [ ] create unique encounter ID
- [ ] determine safe spawn positions/composition
- [ ] tag spawned entities with group + encounter identity
- [ ] only mark group fully materialized after successful spawn transaction
- [ ] prevent a second player/chunk event from materializing the same group again

## Casualty accounting

- [ ] normal mob death updates encounter state
- [ ] non-standard entity removal is handled intentionally
- [ ] remaining strategic strength cannot increase because a chunk unloaded
- [ ] duplicate/replayed death callbacks are idempotent where needed

## Dematerialization

- [ ] wait for no relevant players / safe grace period
- [ ] collect surviving tagged entities
- [ ] reconcile composition/health
- [ ] remove/summarize entities
- [ ] return group to coarse strategic state
- [ ] preserve location/time

## Mandatory edge-case tests

- [ ] two players approach simultaneously
- [ ] chunk unload during materialization
- [ ] server stops during materialization
- [ ] server restarts while encounter is materialized
- [ ] all mobs die
- [ ] some mobs are captured/moved far away
- [ ] player logs out mid-fight
- [ ] entity removed outside ordinary damage path
- [ ] repeated load/unload cycles

## Exit gate

The canonical nine-step persistence test passes: distant movement → materialize once → casualties → unload → reduced strength → restart → continue, with zero duplication/reset.

---

# 17. Stage 13 — Hostile-source lifecycle

## Structure/source registration

- [ ] decide the V1 hostile-source structure strategy
- [ ] assign stable source IDs independent of one spawner block
- [ ] index/register source when structure becomes known/generated
- [ ] persist source state without keeping chunk loaded
- [ ] support admin inspection

## Minimal source behavior

- [ ] population/strength budget
- [ ] reinforcement rule
- [ ] launch cooldown
- [ ] group composition template
- [ ] target-selection rule
- [ ] launch creates a real strategic group at source location

## Clearing

Choose one explicit, understandable V1 objective, for example clearing defenders + destroying/disabling a source-core object.

- [ ] player can tell whether site is still active
- [ ] clearing operation writes permanent state
- [ ] cleared state survives unload
- [ ] cleared state survives restart
- [ ] ordinary mob spawners remain logically independent
- [ ] cleared source can no longer launch new forces under the V1 rule

## Geography test

- [ ] create two equivalent player targets with hostile sources at different route distances
- [ ] verify attack ETA reflects actual source geography

## Exit gate

An intact source repeatedly produces strategic threats over time; after legitimate clearing, that exact source cannot produce another force.

---

# 18. Stage 14 — Factions, hordes, and armies

Only now expand from one test group to the intended living threat system.

## Architecture

- [ ] faction/type data-driven registry
- [ ] group-type registry: patrol / horde / raid / army as needed
- [ ] composition summaries by role/unit class
- [ ] multiple hostile mob families, not zombie-only
- [ ] source types can choose appropriate force templates
- [ ] specialized siege-capable role tags

## Large encounter scaling

- [ ] define active-entity cap per materialized strategic force
- [ ] if necessary, implement encounter waves while preserving total strategic strength
- [ ] preserve casualties across waves
- [ ] preserve remaining unmaterialized strength across restart
- [ ] ensure “army of 500” does not imply 500 permanently ticking entities
- [ ] benchmark worst expected V1 encounter

Merge/split/reinforcement behavior is optional unless required for the V1 experience; do not overcomplicate before one army works reliably.

## Exit gate

At least two materially different hostile strategic compositions can originate from persistent sources, travel unloaded, materialize, lose forces permanently, and complete/die without corrupting state or TPS.

---

# 19. Stage 15 — Siege planner

## Layer 1: normal route first

- [ ] define siege objective position/area
- [ ] request normal viable path toward objective
- [ ] detect usable gate/entrance/road/bridge access
- [ ] prove open entrance produces zero arbitrary wall damage

## Layer 2: breach decision

- [ ] breach is unavailable to ordinary units unless explicitly tagged
- [ ] only invoke planner if normal path fails or exceeds a defined cost threshold
- [ ] rate-limit concurrent planners
- [ ] cache plan
- [ ] invalidate on meaningful structural changes

## Layer 3: corridor scoring

Candidate score should consider:

- [ ] blocks that must be removed
- [ ] hardness/break time
- [ ] whether the resulting opening is actually navigable
- [ ] doors/gates/weaker barriers
- [ ] vertical accessibility
- [ ] protected block tags
- [ ] distance/approach feasibility

## Layer 4: execution

- [ ] siege unit moves to assigned breach location
- [ ] break progress is bounded and visible/understandable
- [ ] block is eligible only as part of active breach corridor or explicit interaction category
- [ ] once corridor opens, units resume normal pathing
- [ ] plan aborts/recomputes when obsolete

## Non-negotiable safety tests

- [ ] open gate → use gate; no breach
- [ ] obvious weak doorway → prefer doorway appropriately
- [ ] sealed wall → produce deliberate breach
- [ ] decorative statue beside attack route → untouched
- [ ] decorative facade not on required corridor → untouched
- [ ] protected blocks → never broken
- [ ] breach actually yields traversable route
- [ ] planner cannot run globally every tick

## Exit gate

A deliberately built test castle provides meaningful defensive value while off-route decoration remains safe.

---

# 20. Stage 16 — Strategic animal herds

Use the already-proven strategic kernel rather than inventing a separate distant-animal simulator.

## Checklist

- [ ] `HerdRecord` or generic peaceful-group specialization
- [ ] species/type
- [ ] approximate count
- [ ] home range / movement tendency
- [ ] strategic position
- [ ] last simulated time
- [ ] coarse movement
- [ ] materialization near players
- [ ] safe dematerialization away from players
- [ ] normal player interaction does not reset the herd incorrectly
- [ ] herd state persists through restart
- [ ] entity counts remain bounded

Detailed migration/reproduction/ecology modeling is post-V1 unless it is trivial after the core system exists.

## Exit gate

Travel through a sparsely loaded large landscape can encounter persistent herds without the server continuously ticking all animals.

---

# 21. Stage 17 — Local spawning coexistence

This must be explicitly proven rather than assumed.

- [ ] vanilla/local hostile spawning still works at night
- [ ] cave spawning still works
- [ ] conventional mob farm still works
- [ ] ordinary spawners remain usable according to upstream rules
- [ ] strategic source state is not inferred from an ordinary spawner block
- [ ] strategic encounter entities are distinguishable from ordinary local spawns where accounting requires it
- [ ] strategic population caps do not accidentally suppress all normal ecology
- [ ] normal local mobs cannot accidentally mutate a strategic group's persistent strength

Use conservative V1 defaults. Fine spawn-rate/difficulty tuning is V1.1+.

## Exit gate

Normal Minecraft spawning/farming feels intact while a strategic horde can exist simultaneously.

---

# 22. Stage 18 — Cross-system integration pass

Individual subsystem success is not enough. DrewCraft V1 exists only when they interact coherently.

## Required integrated scenarios

### Scenario A — Long-distance infrastructure

- [ ] spawn far from a remote destination
- [ ] travel normally / by road vehicle
- [ ] establish Create rail route
- [ ] fly supported aircraft
- [ ] verify all modes function on production-scale geography

### Scenario B — Weather-informed aviation

- [ ] storm exists remotely
- [ ] radar sees it before arrival
- [ ] aircraft route can avoid or cross it
- [ ] crossing it produces corresponding flight effects
- [ ] radar and aircraft use the same atmospheric state

### Scenario C — Persistent invasion

- [ ] intact source launches hostile force
- [ ] force moves while all relevant chunks are unloaded
- [ ] ETA remains explainable
- [ ] player encounters force en route or at destination
- [ ] casualties persist
- [ ] force can siege defended target
- [ ] server restarts during campaign without duplication

### Scenario D — Conquest

- [ ] player travels to hostile source
- [ ] clears source through explicit objective
- [ ] cleared state persists
- [ ] future force generation from that source stops
- [ ] ordinary local mobs/spawners still exist

### Scenario E — Living landscape

- [ ] distant herd advances/coheres strategically
- [ ] herd materializes near player
- [ ] player leaves
- [ ] herd safely summarizes back to strategic state

### Scenario F — Infrastructure failure

- [ ] radar loses Create power and stops
- [ ] cable break disconnects expected components
- [ ] reconnect restores operation without corrupting state

## Exit gate

All six scenarios succeed on the same pack build and same persistent test world.

---

# 23. Stage 19 — Performance-budget pass on the complete V1 feature set

Repeat performance testing now that the expensive custom features actually exist.

## Representative worst-normal-case scenario

Run with:

- [ ] several players
- [ ] Project Atmosphere active
- [ ] Distant Horizons clients
- [ ] representative Create infrastructure/train
- [ ] several vehicles
- [ ] at least one aircraft receiving weather effects
- [ ] multiple strategic groups moving unloaded
- [ ] animal herds in strategic state
- [ ] one materialized large hostile force
- [ ] active siege planner
- [ ] multiple radar installations/displays
- [ ] normal local mobs

## Measure

- [ ] MSPT p50/p95/p99 or equivalent useful percentiles
- [ ] long-tick incidence
- [ ] CPU
- [ ] heap/native memory
- [ ] GC
- [ ] network
- [ ] radar scan work
- [ ] strategic simulation work
- [ ] siege-planner work
- [ ] entity counts
- [ ] save duration
- [ ] backup duration

## Optimization priority

Optimize algorithms/cadence/caching before deleting V1 features. Examples:

1. reduce scan frequency/resolution before removing radar behavior;
2. coarsen strategic cadence/cells before abandoning unloaded movement;
3. cap materialized encounter entities/use waves before eliminating large armies;
4. cache siege plans before simplifying to random block breaking.

## Exit gate

The chosen production host provides acceptable multiplayer behavior in the complete representative scenario, or the host is explicitly upgraded/migrated.

---

# 24. Stage 20 — Failure, persistence, and recovery matrix

V1's unusual systems make restart correctness more important than ordinary happy-path testing.

## Restart/crash matrix

Test server stop/restart during:

- [ ] strategic group moving unloaded
- [ ] group materialization
- [ ] active combat
- [ ] dematerialization
- [ ] source clearing
- [ ] active siege breach
- [ ] radar scan/update
- [ ] server release update
- [ ] backup creation

## Persistence migration

- [ ] increment test schema version
- [ ] migrate a fixture from old → new
- [ ] reject unsupported future schema clearly
- [ ] ensure disabling a subsystem does not erase its persisted state

## Backup drill

- [ ] make production-format backup
- [ ] destroy disposable test host/state
- [ ] restore on clean host
- [ ] confirm player/world state
- [ ] confirm source cleared/intact states
- [ ] confirm moving group state/ETA
- [ ] confirm materialized encounter reconciliation
- [ ] confirm pack/world version identity

## Exit gate

A backup restores **the living strategic world**, not merely Minecraft region files.

---

# 25. Stage 21 — V1 UX and release candidate

## Freeze

- [ ] freeze upstream dependency versions for RC
- [ ] freeze world-generation dependencies
- [ ] stop adding major gameplay ideas
- [ ] only bug fixes, reliability work, required bridges, packaging, and severe design-preservation changes enter RC

## Recipes/balance policy

- [ ] leave upstream recipes intact wherever practical
- [ ] give custom DrewCraft blocks simple functional recipes
- [ ] do not perform broad economy rebalance
- [ ] do not hand-tune every vehicle/aircraft fuel cost
- [ ] only change Nether compression or similarly dominant defaults if testing proves they destroy a core design pillar
- [ ] record balance observations for V1.1 backlog rather than blocking release

## Fresh-install matrix

- [ ] fresh Windows machine/user profile installs from DrewCraft website artifact
- [ ] fresh Apple Silicon macOS machine/user profile installs from website artifact
- [ ] user signs in through Prism
- [ ] launcher obtains exact live release
- [ ] server reports compatible version
- [ ] user joins
- [ ] no Java/NeoForge/mod-folder instructions are needed

## Update matrix

- [ ] install an older test version
- [ ] publish RC update
- [ ] launcher stages update
- [ ] server updates safely
- [ ] old client cannot silently join wrong server state
- [ ] client repairs/upgrades
- [ ] joins successfully

## Website

- [ ] repository/URLs use final DrewCraft paths
- [ ] Pages enabled when desired
- [ ] Windows button downloads real installer
- [ ] Mac button downloads real DMG/app artifact
- [ ] no technical setup guide is required for normal use

---

# 26. Stage 22 — V1 acceptance test

Every item below is a hard release gate unless `v_1_requirements.md` explicitly marks it optional.

## Reproducibility

- [ ] clean checkout can build/resolve exact pack
- [ ] client/server release artifacts are hash-verified
- [ ] release manifest is authoritative

## World

- [ ] World Scale 2 Terrain Diffusion production world loads reliably
- [ ] production border lies within pregenerated area
- [ ] world artifact can be restored
- [ ] Distant Horizons is usable on supported clients

## Transportation

- [ ] road vehicle works
- [ ] Create train works
- [ ] supported aircraft works
- [ ] optional ship failure/absence does not block V1

## Weather/aviation

- [ ] actual Atmosphere wind affects supported aircraft
- [ ] head/tailwind works
- [ ] crosswind works
- [ ] storm/terrain turbulence works within playable bounds
- [ ] poor weather visibility behavior works where supported

## Radar

- [ ] physical ground radar is buildable
- [ ] Create-derived power matters
- [ ] physical connectivity matters
- [ ] height improves coverage
- [ ] terrain masking works
- [ ] display represents real weather
- [ ] aircraft radar works if kept as a hard V1 requirement in final requirements

## Strategic world

- [ ] hostile source registered persistently
- [ ] source launches group
- [ ] group moves while unloaded
- [ ] ETA is based on route/distance
- [ ] materializes exactly once
- [ ] casualties persist
- [ ] dematerializes safely
- [ ] restart does not duplicate/reset group
- [ ] more than one hostile composition/faction is supported
- [ ] convincingly large army can be represented without permanently loading all members

## Siege

- [ ] normal paths are preferred
- [ ] sealed target can trigger controlled breach
- [ ] only allowed units breach
- [ ] decorative off-route structure remains safe
- [ ] breach opens real navigable route

## Normal Minecraft coexistence

- [ ] night/cave spawning works
- [ ] ordinary farm works
- [ ] spawners remain separate from strategic-source state
- [ ] building/mining/Create gameplay remains recognizable

## Herds

- [ ] strategic herd persists unloaded
- [ ] materializes nearby
- [ ] summarizes safely when distant

## Operations

- [ ] server update transaction works
- [ ] backup-before-update works
- [ ] off-host backup exists
- [ ] restore drill passes
- [ ] health/version endpoint works
- [ ] subsystem kill switches work

## Friend UX

- [ ] one-click-enough Windows install
- [ ] one-click-enough Apple Silicon Mac install
- [ ] automatic pack update
- [ ] stale/corrupt client repair
- [ ] useful server-offline/updating errors

## Performance

- [ ] complete representative scenario meets the chosen host's acceptable tick/performance target
- [ ] no unbounded per-tick global scans
- [ ] no distant entity ticking
- [ ] no radar rescan per display
- [ ] siege planner is bounded/cached

**When every hard box above passes on the same release candidate, promote the pack from `0.x` to `1.0.0`.**

---

# 27. What explicitly waits until V1.1+

Unless required to prevent a core system from being trivialized or unusable, defer these until after real multiplayer V1 experience:

- broad recipe rewrites
- exact vehicle acquisition costs
- exact aircraft acquisition/maintenance costs
- fuel-economy tuning
- perfect train economics
- detailed radar tier/crafting progression
- fine hostile-source density tuning
- fine army frequency/difficulty curves
- elaborate faction diplomacy
- sophisticated strategic merge/split behavior
- realistic animal reproduction/migration ecology
- advanced meteorology beyond stable upstream data
- detailed orographic precipitation/rain-shadow simulation
- multiple radar product modes beyond the useful V1 set
- extensive quest/RPG systems
- unrelated survival-realism mechanics

Create issues/backlog notes for these findings during playtests instead of slipping them into the V1 critical path.

---

# 28. Recommended development cadence

For each major system, use the same loop:

```text
1. smallest reproducible implementation
2. automated/unit test where practical
3. dedicated-server smoke test
4. multiplayer vertical-slice test
5. restart/unload failure test
6. performance measurement
7. commit gate
8. only then add breadth
```

Do not build five versions of a subsystem before one end-to-end path works. For example:

- one aircraft with real wind before supporting every aircraft;
- one radar installation with real weather before radar tiers;
- one strategic group with perfect persistence before five factions;
- one hostile source with permanent clearing before cities everywhere;
- one safe breach planner before exotic siege units.

This ordering is intentionally conservative because **correct persistence, compatibility, and operations are harder to retrofit than content breadth**.

---

# 29. The first implementation sprint

The immediate next work from the repository's present state is therefore:

- [ ] Stage 0 repository/naming cleanup
- [ ] create target directory skeleton and `.gitignore`
- [ ] define manifest schemas
- [ ] lock exact NeoForge + baseline mod versions/hashes
- [ ] implement dependency resolver + pack builder + verifier
- [ ] add CI validation
- [ ] generate first reproducible development client/server pack
- [ ] run Stage 2 compatibility matrix

**Do not begin radar, armies, siege AI, or recipe tuning before this first sprint passes.**

That first known-good pack is the foundation on which every genuinely interesting DrewCraft feature depends.
