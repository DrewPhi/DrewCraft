# DrewCraft Mod Stack

This document defines how dependencies enter DrewCraft and, critically, **which system owns which responsibility**. The pack should not become a kitchen sink. Every dependency adds update risk, client burden, startup time, memory use, and multiplayer failure modes.

The hard rule is:

> **One authoritative owner per subsystem. Other mods may render, consume, optimize, or bridge that state, but they must not create a competing second implementation.**

The current target is Minecraft **1.21.1**, **NeoForge**, **Java 21**.

Candidate artifacts are split across the machine-readable registries under `pack/manifest/`. They are promoted into the production lock only after the relevant compatibility matrix passes and exact artifact SHA-256 values are recorded.

## 1. Responsibility / anti-redundancy matrix

| Responsibility | Authoritative owner | Supporting role | Explicitly avoid |
| --- | --- | --- | --- |
| Overworld terrain, elevation, rivers, climate fields, tall-world caves | Terrain Diffusion Plus | Chunky pregenerates it; DrewCraft reads/bridges its data | another terrain generator or cave overhaul by default |
| Offline chunk pregeneration | Chunky | build/admin tooling only | treating Chunky as player-facing gameplay |
| Long-distance visual LOD | Distant Horizons | client rendering | a second distant-terrain renderer |
| Industry, mechanical infrastructure, logistics, rail | Create | DrewCraft adapters consume Create kinetic power | a second giant tech tree; MTS rail as a competing rail system |
| Cars/trucks and aircraft | Immersive Vehicles / MTS + minimal curated content | DrewCraft adds weather/radar integration | overlapping vehicle ecosystems or novelty-pack sprawl |
| Atmospheric simulation / weather state | Project Atmosphere | DrewCraft weather API consumes it | a second weather simulator |
| Clouds and localized weather rendering | Simple Clouds, under Project Atmosphere control/integration | visual/local precipitation substrate | treating Simple Clouds as an independent competing weather authority |
| Seasonal calendar / foliage / crop-season behavior | Serene Seasons where required/stable | Project Atmosphere integrates with it | a second season system |
| Physical weather radar | DrewCraft custom mod | consumes Project Atmosphere; powered through Create adapter | a separate radar mod/minimap weather cheat |
| Strategic mobs, distant hordes, armies and herds | DrewCraft custom mod | tactical AI helpers only after compatibility tests | a second macro horde/world-simulation mod |
| Loaded hostile horde behavior | selected tactical helper or DrewCraft goals | Enhanced Hordes + Tweaks **or** Zombie Hordes are candidate branches | stacking overlapping horde overhauls; helper spawning strategic strength |
| Loaded wild-herd behavior | selected herd helper or DrewCraft goals | Ethological or Herd Instinct are candidate branches | a second unloaded ecology/population simulator |
| Hostile source architecture/content | selected generated structures + DrewCraft source mapping/core | Towns and Towers + selective WDA is the first spike | treating every structure as a source; indiscriminate structure-pack stacking |
| Hostile source state / Source Core lifecycle | DrewCraft custom mod | structure mods only supply architecture | deriving source state from ordinary spawners or third-party raid state |
| Siege planning and constrained breaching | DrewCraft custom mod | ordinary mob navigation first; external siege code may be studied | generic indiscriminate block-breaking AI |
| Local vanilla spawning and mob farms | Minecraft / selected upstream spawn rules | DrewCraft strategic system is additive | replacing ordinary spawning with the strategic layer |
| Server/core performance | semantics-preserving optimization suite | ModernFix, FerriteCore, Lithium, ServerCore, ScalableLux, etc. | an optimizer becoming a gameplay/system authority |
| Client rendering performance | Embeddium + targeted render optimizers | ImmediatelyFast, Entity Culling, MoreCulling | renderer/culling settings that make required content disappear |
| Profiling | spark + process metrics | evidence for optimization decisions | cargo-cult performance mods without measurement |
| Routine long-distance travel | roads, Create rail, MTS vehicles, vanilla boats; ships if proven stable | Nether remains available subject to a coarse pillar-preserving rule if necessary | Waystones/routine teleportation |

This matrix is the default answer when a new mod appears to overlap an existing one: **do not add it unless it solves a missing capability that cannot be implemented cleanly through the existing owner or DrewCraft bridge.**

## 2. Foundational gameplay dependencies

### Terrain Diffusion Plus

**Role:** sole overworld generation foundation and source of large-scale terrain/climate geometry.

Target configuration:

- World Scale 2
- bounded production world
- offline pre-generation using Chunky
- no expectation of large live diffusion generation on the production server

Terrain Diffusion Plus already contains the intended tall-world cave handling for the 1.21.1 line. **Do not add YUNG-style Better Caves, Tectonic, TerraForged, Continents, or another general cave/terrain overhaul by default.** A second world-generation layer is allowed only if a concrete deficiency is demonstrated and compatibility is proven.

Its climate/elevation data should be exposed to DrewCraft through a compatibility adapter rather than recreated.

Official source: `derekvawdrey/terrain-diffusion-plus`.

### Chunky

**Role:** controlled pre-generation of the playable world.

Chunky is operational tooling, not gameplay. It exists because Terrain Diffusion generation is expensive and the production world should be built ahead of time.

Offline pregeneration is also DrewCraft's most important performance strategy: ordinary production play should load already-built Terrain Diffusion terrain and source structures rather than generate them while players are flying or driving.

### Distant Horizons

**Role:** communicate the huge world's scale visually using distant LOD rendering.

It must be tested for:

- Windows and Apple Silicon performance
- multiplayer behavior
- memory/GPU burden
- interaction with Simple Clouds
- interaction with Embeddium and the client optimization stack
- sensible pack defaults

Distant Horizons does not own weather, world generation, navigation or strategic simulation.

### Create

**Role:** primary technology/infrastructure language.

Create owns:

- mechanical industry
- logistics
- trains and rail infrastructure
- bridges/tunnels/construction-oriented infrastructure

**Create is the only intended rail/industrial tech system.** Even if a vehicle pack contains rail-capable content, DrewCraft should not establish a second parallel train progression for V1.

DrewCraft should integrate with Create rather than add another all-purpose energy/technology mod. Custom systems that need a powered state should use a small DrewCraft adapter from Create kinetic stress/RPM rather than importing a second electrical tech tree.

### Immersive Vehicles / MTS

**Role:** realistic-ish road vehicles and aircraft.

MTS provides the vehicle physics/content framework; it does not own weather or rail progression.

Use the **smallest curated content-pack set** that provides the V1 road and aircraft capabilities. One content pack may satisfy both requirements. The MTS Official Pack is currently a compatibility candidate because it contains cars/trucks and aircraft in one package; it is not automatically the final V1 content selection, especially if unwanted content cannot be cleanly hidden.

Selection criteria:

- stable 1.21.1 multiplayer behavior
- useful cars/trucks and aircraft
- visual tone compatible with Minecraft/DrewCraft
- no unnecessary duplicate train ecosystem
- no novelty-content sprawl
- acceptable licensing/distribution model

DrewCraft owns the bridge from atmospheric wind/severity to supported aircraft and the aircraft weather-radar integration.

### Project Atmosphere

**Role:** **sole atmospheric simulation authority**.

Project Atmosphere owns atmospheric/weather state. DrewCraft consumes its state; it must not implement a second independent storm model.

This includes the source data used by:

- wind effects
- precipitation/storm severity
- visibility
- ground weather radar
- aircraft weather radar
- aviation turbulence inputs

### Simple Clouds

**Role:** cloud/localized-weather rendering substrate integrated with Project Atmosphere.

Simple Clouds may itself expose localized cloud/weather behavior, but inside DrewCraft it is **not a competing weather authority**. Project Atmosphere is expected to control/integrate the atmospheric behavior, while Simple Clouds supplies the cloud rendering/local visual machinery.

This pairing is intentional rather than redundant: Project Atmosphere's integration is expected to drive climate/weather behavior while Simple Clouds supplies the visible cloud machinery.

### Serene Seasons

**Role:** season calendar and seasonal world/gameplay presentation where required/stable with the chosen Project Atmosphere release.

Serene Seasons can affect foliage, temperature context, weather and crop growth, so ownership must remain clear:

- Serene Seasons owns its seasonal calendar and seasonal gameplay hooks;
- Project Atmosphere consumes/integrates seasonal state for atmospheric behavior;
- DrewCraft does not create a third season simulation.

The selected dependency graph determines whether it is required. Serene Seasons itself requires GlitchCore on modern versions.

### Required libraries

Support libraries such as GlitchCore or Gabou's Libs are dependencies, not gameplay systems. They must be tracked explicitly in the manifest so they never become invisible manual prerequisites.

## 3. Performance baseline

`docs/PERFORMANCE_STACK.md` is the detailed optimization contract and `pack/manifest/performance_candidates.yaml` is its machine-readable candidate registry.

Performance mods **do not own gameplay behavior**. They are allowed only while DrewCraft's simulation semantics remain correct.

### Intended Stage 2 baseline suite

Common/server-side technical baseline:

- **ModernFix** — broad memory/startup/performance fixes
- **FerriteCore** — memory reduction
- **Lithium** — game-logic/ticking optimization
- **ServerCore** — server optimization with conservative semantics-preserving settings first
- **ScalableLux** — lighting optimization
- **Chunk Sending** — smoother/prioritized/cached chunk delivery
- **AllTheLeaks** — leak mitigation
- **FastSuite**
- **FastWorkbench**
- **FastFurnace**
- **Clumps** — XP-orb entity reduction
- **Connectivity** — networking/login reliability helper
- **spark** — profiler/diagnostics

Client performance baseline:

- **Embeddium** — primary NeoForge renderer optimization
- **ImmediatelyFast**
- **Entity Culling**
- **MoreCulling**

Required libraries such as **Placebo** and **Cupboard** are resolved automatically by the pack resolver.

### Configuration rules

Start with correctness-preserving settings.

In particular:

- ServerCore entity-activation/dynamic-distance/mobcap behavior remains off until separately proven;
- no generic AI/entity freezing for strategic encounter entities;
- ScalableLux must pass Create + structure + restart lighting tests;
- Entity Culling/MoreCulling must not hide Create contraptions, MTS content, cloud/weather visuals or DrewCraft radar displays; whitelist renderers when necessary;
- Connectivity may improve resilience but cannot mask a broken custom networking protocol;
- every retained optimizer needs measurable performance value or a concrete reliability benefit.

### C2ME

C2ME is an **isolated compatibility spike**, not part of the first baseline.

Its concurrency could substantially accelerate offline pregeneration, but Terrain Diffusion and large modded structure generation are exactly where asynchronous assumptions need proof. Test the same seed/config with and without C2ME and compare correctness, structures, restart safety, warnings, memory, CPU and chunks/second.

Even if useful on the world-build machine, C2ME does not automatically belong on the production server after the bounded world is pregenerated.

### Deliberately deferred performance mods

- Noisium — archived; do not baseline.
- SuperChunk/GPU worldgen bundles — too aggressive/hardware-specific for V1 baseline.
- DoesPotatoTick?/generic AI freezers — not baseline because they can violate strategic encounter semantics.

DrewCraft's primary mob optimization is architectural: distant armies/herds are records, nearby groups materialize, and large encounters use bounded active entities/waves rather than permanently ticking thousands of mobs.

## 4. Tactical hostile AI candidates

DrewCraft owns macro-scale strategic state regardless of which local helper wins.

### Branch A — Enhanced Hordes + Enhanced Hordes Tweaks

High-priority loaded-behavior spike for:

- horde grouping/wandering;
- collective pursuit;
- stacking/climbing;
- tagged mob participation;
- other local cooperative behavior.

Requirements:

- disable/avoid timed/random spawning that creates strategic strength outside DrewCraft accounting;
- generic block breaking must not override DrewCraft's siege planner;
- materialized strategic IDs/casualties remain authoritative in DrewCraft.

### Branch B — Zombie Hordes

Alternative loaded-horde spike. Test against Branch A rather than stacking both.

Choose the branch that gives the desired behavior with the smallest compatibility and maintenance surface. If neither is clean enough, implement only the required local goals in DrewCraft.

### Reference-only AI

- **Improved Mobs** — useful pathfinding/block-breaking techniques, but too globally invasive for the desired siege rules.
- **Invasion Mod** — useful engineer/bridge/ladder/siege R&D, but its Nexus/wave loop duplicates DrewCraft's strategic system.

See `docs/MOB_STRUCTURE_CANDIDATES.md`.

## 5. Wild-herd AI candidates

DrewCraft owns `HerdRecord`, unloaded movement, materialization and population accounting.

### Ethological

Rich experimental branch for coherent loaded livestock/herd behavior including group movement, rejoining, threat response, grazing/water/rest and pen recognition.

Because it is young and broad, it must earn inclusion through performance and interaction testing.

### Herd Instinct

Narrower fallback focused on shared panic/flee behavior. Lower scope may make it easier to combine with DrewCraft-owned local follow/group goals.

Do not add deep animal husbandry/genetics/sickness/thirst systems merely to obtain herd movement.

## 6. Strategic-source structure candidates

Structure mods supply **architecture**. DrewCraft supplies source identity, Source Core, population budget, outgoing strategic groups, clearing and persistence.

The production world must remain sparse.

### First source-content spike

1. vanilla pillager outpost as a control;
2. **Towns and Towers** for grounded pillager-outpost variants;
3. **When Dungeons Arise**, but with a tiny generation allow-list and aggressively increased spacing.

Candidate WDA concepts include camps, forts and a very small number of major palace/city-class sites. Only those approved structures generate at all in the V1 production world. Each remains a complete dungeon with its normal exploration, mobs and loot while also receiving DrewCraft source identity and Source Core semantics. Disable every other WDA structure and do not accept default density blindly.

### Alternatives

- **CTOV** — initially an alternative to Towns and Towers because both expand village/outpost space.
- **Repurposed Structures** — gap filler only if a source archetype remains missing.
- **Structory** — optional atmospheric exploration texture, not the primary hostile kingdom hierarchy.
- broad 100+ structure collections — avoid unless heavily filtered and a specific need is demonstrated.

### Density tools

Pack-owned structure-set enable/spacing/separation configuration is preferred.

- **Sparse Structures** is a useful fallback spike if global density control is genuinely cleaner.
- **Limited Structures** may eventually help enforce a tiny number of unique capitals.
- **Structurify** is not a default because generic frequency modifiers can conflict with pack-specific generation schemes.

### Structure Essentials

Structure Essentials is an optional world-build/server tooling candidate. Faster locating, spacing/separation, overlap and structure-debug features may help validate pregeneration/source indexing, but it is not required if pack-owned configuration already solves those jobs.

## 7. Other compatibility-gated capabilities

### Large player-buildable ships

Desired role: water logistics/transport between small boats and aircraft.

A ship implementation is **not a hard V1 blocker**. It must support 1.21.1 NeoForge, multiplayer, Create coexistence, acceptable performance, and avoid chunk/contraption corruption.

Do not add multiple ship systems.

### Navigation/map tooling

A restrained map may be useful because the world is huge. It must not provide routine teleportation, omniscient hostile/player tracking, or information that makes physical radar/weather/navigation infrastructure irrelevant.

## 8. Features that belong in the DrewCraft integration mod

Prefer one NeoForge integration mod with internal modules for:

- Terrain Diffusion climate/elevation adapter
- Project Atmosphere weather adapter
- atmospheric wind -> MTS aircraft effects
- terrain/mountain turbulence
- physical weather radar and displays
- aircraft weather radar
- Create-compatible radar power adapter
- strategic populations
- hostile source lifecycle
- Source Core binding/clearing/persistence
- unloaded movement/ETA
- materialization/dematerialization and casualty reconciliation
- army composition
- animal-herd persistence
- siege planner
- constrained block breaching
- strategic/local spawn coexistence
- Nether portal-distance rule if testing proves a core-pillar problem

Do not solve these by collecting overlapping standalone mods unless integration into the existing architecture is demonstrably impossible.

## 9. Intentionally excluded by default

- Waystones or routine teleportation
- additional overworld terrain/cave overhauls
- indiscriminate giant structure packs
- extra dimensions without a specific project need
- multiple giant technology/power systems
- separate weather simulators
- generic world-scale horde/army mods
- generic indiscriminate mob block-breaking mods
- generic AI/entity freezers that can break strategic encounters
- unrelated hunger/thirst/body-temperature micromanagement
- deep animal husbandry micromanagement solely for herd behavior
- novelty vehicle-pack collections
- parallel rail systems that compete with Create trains
- redundant village/outpost overhauls without a demonstrated non-overlapping purpose

## 10. Dependency and source policy

Candidate registries:

- `pack/manifest/upstreams.yaml` — foundational platform/gameplay dependencies
- `pack/manifest/performance_candidates.yaml` — performance baseline and experimental optimizers
- `pack/manifest/mob_structure_candidates.yaml` — tactical AI, herd AI, structure sources and density spikes

The eventual locked `mods.yaml` / `content-packs.yaml` is authoritative for a release.

Every dependency must record:

- canonical ID/name
- official source repository/provider
- Minecraft version and loader
- exact artifact/version
- exact SHA-256 before lock
- side (`common`, `client`, `server`, operational/world-build)
- required/optional state
- redistribution/acquisition policy
- provider IDs/download identity
- compatibility notes
- ownership class where applicable

Do not fork a mod merely for convenient packaging. Track upstream source for debugging/API work and fork only when DrewCraft must maintain a source patch that cannot live cleanly in the integration mod.

## 11. Redistribution policy

The builder/launcher must support both:

1. artifacts DrewCraft is legally permitted to redistribute; and
2. artifacts that must be fetched from the original provider at build/install time.

The resulting file is always verified against the locked SHA-256.

Never commit third-party mod jars merely because doing so is convenient.

## 12. Client/server partition

Every dependency is classified as common, client-only, server-only, or operational tooling.

- **Common:** gameplay/content/protocol or common optimizers required on both sides.
- **Client:** rendering/UI/performance dependencies that the dedicated server should not load.
- **Server:** admin/profiling/server-only optimization/reliability helpers.
- **Operational/world-build:** tools such as Chunky and potentially Structure Essentials/C2ME profiles used for generating/validating the world.

The client and server packs must be generated from one source manifest rather than maintained independently.

## 13. Update rules

No dependency update goes directly to production.

Required flow:

1. update candidate/manifest metadata;
2. acquire the exact artifact through an allowed provider;
3. verify SHA-256;
4. resolve all transitives;
5. build client/server packs;
6. boot dedicated server;
7. connect supported clients;
8. load the existing world where relevant;
9. test affected ownership boundaries and compatibility profiles;
10. inspect registry/mixin/network/render/lighting logs;
11. measure performance when the dependency claims performance benefit;
12. promote only after the relevant compatibility matrix passes.

World-generation dependency changes require extra caution because newly generated terrain may differ permanently from the existing production world.

## 14. V1 scope rule

DrewCraft V1 is **feature-complete and integration-complete, not balance-complete**.

The V1 mod stack therefore needs working systems and bridges, not broad recipe/economy retuning. Exact vehicle cost, fuel economics, aircraft price, radar progression and army difficulty belong to V1.1+ unless an upstream default demonstrably destroys a core design pillar.

The real version friends play is the **DrewCraft pack version**, not a collection of individual mod version numbers.
