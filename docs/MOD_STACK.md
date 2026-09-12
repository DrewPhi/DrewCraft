# DrewCraft Mod Stack

This document defines how dependencies enter DrewCraft and, critically, **which system owns which responsibility**. The pack should not become a kitchen sink. Every dependency adds update risk, client burden, startup time, memory use, and multiplayer failure modes.

The hard rule is:

> **One authoritative owner per subsystem. Other mods may render, consume, or bridge that state, but they must not create a competing second implementation.**

The current target is Minecraft **1.21.1**, **NeoForge**, **Java 21**.

Exact artifacts are tracked as candidates in `pack/manifest/upstreams.yaml` and are promoted into the production lock only after the V1 Stage 2 compatibility matrix passes.

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
| Strategic mobs, distant hordes, armies and herds | DrewCraft custom mod | normal Minecraft entities only when materialized | a second macro horde/world-simulation mod |
| Siege planning and constrained breaching | DrewCraft custom mod | ordinary mob navigation first | generic indiscriminate block-breaking AI |
| Local vanilla spawning and mob farms | Minecraft / selected upstream spawn rules | DrewCraft strategic system is additive | replacing ordinary spawning with the strategic layer |
| Routine long-distance travel | roads, Create rail, MTS vehicles, vanilla boats; ships if proven stable | Nether remains available subject to a coarse pillar-preserving rule if necessary | Waystones/routine teleportation |

This matrix is the default answer when a new mod appears to overlap an existing one: **do not add it unless it solves a missing capability that cannot be implemented cleanly through the existing owner or DrewCraft bridge.**

## 2. Baseline dependencies

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

### Distant Horizons

**Role:** communicate the huge world's scale visually using distant LOD rendering.

It must be tested for:

- Windows and Apple Silicon performance
- multiplayer behavior
- memory/GPU burden
- interaction with Simple Clouds
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

This pairing is intentional rather than redundant: Project Atmosphere's own documentation describes its simulation as replacing Simple Clouds' random cloud spawning with climate-driven behavior.

### Serene Seasons

**Role:** season calendar and seasonal world/gameplay presentation where required/stable with the chosen Project Atmosphere release.

Serene Seasons can affect foliage, temperature context, weather and crop growth, so ownership must remain clear:

- Serene Seasons owns its seasonal calendar and seasonal gameplay hooks;
- Project Atmosphere consumes/integrates seasonal state for atmospheric behavior;
- DrewCraft does not create a third season simulation.

Current Project Atmosphere releases explicitly support Serene Seasons, and the selected dependency graph determines whether it is required. Serene Seasons itself requires GlitchCore on modern versions.

### Required libraries

Support libraries such as GlitchCore or Gabou's Libs are dependencies, not gameplay systems. They must be tracked explicitly in the manifest so they never become invisible manual prerequisites.

## 3. Compatibility-gated candidates

These capabilities are allowed only after the baseline passes.

### Large player-buildable ships

Desired role: water logistics/transport between small boats and aircraft.

A ship implementation is **not a hard V1 blocker**. It must support 1.21.1 NeoForge, multiplayer, Create coexistence, acceptable performance, and avoid chunk/contraption corruption.

Do not add multiple ship systems.

### Navigation/map tooling

A restrained map may be useful because the world is huge. It must not provide routine teleportation, omniscient hostile/player tracking, or information that makes physical radar/weather/navigation infrastructure irrelevant.

### Herd/ecology helpers

A nearby-animal behavior mod is allowed only if it complements DrewCraft's strategic distant-herd records. It must not become a second persistent population simulator or explode entity counts.

### Local spawn/horde helpers

Do not add a general horde mod just because hordes are desired. DrewCraft owns macro-scale persistent groups, sources, movement, ETA and armies.

A local spawning/AI helper may be introduced only when a concrete loaded-chunk behavior cannot be implemented adequately in the DrewCraft integration layer. It must remain subordinate to DrewCraft strategic state.

### Structure content

Do not install a giant structure pack for variety. Add only sparse, purpose-specific structure content needed for exploration or hostile source sites, and only after density is measured against the World Scale 2 geography.

## 4. Features that belong in the DrewCraft integration mod

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
- unloaded movement/ETA
- materialization/dematerialization and casualty reconciliation
- army composition
- animal herds
- siege planner
- constrained block breaching
- strategic/local spawn coexistence
- Nether portal-distance rule if testing proves a core-pillar problem

Do not solve these by collecting overlapping standalone mods unless integration into the existing architecture is demonstrably impossible.

## 5. Intentionally excluded by default

- Waystones or routine teleportation
- additional overworld terrain/cave overhauls
- giant structure packs
- extra dimensions without a specific project need
- multiple giant technology/power systems
- separate weather simulators
- generic world-scale horde/army mods
- generic indiscriminate mob block-breaking mods
- unrelated hunger/thirst/body-temperature micromanagement
- novelty vehicle-pack collections
- parallel rail systems that compete with Create trains

## 6. Dependency and source policy

`pack/manifest/upstreams.yaml` is the candidate/source registry. The eventual locked `mods.yaml` / `content-packs.yaml` is authoritative for a release.

Every dependency must record:

- canonical ID/name
- official source repository/provider
- Minecraft version and loader
- exact artifact/version
- exact SHA-256 before lock
- side (`common`, `client`, `server`)
- required/optional state
- redistribution/acquisition policy
- provider IDs/download identity
- compatibility notes
- ownership class (`UPSTREAM_BINARY`, `UPSTREAM_SOURCE`, `DREWCRAFT_FORK`, `DREWCRAFT_OWNED`)

Do not fork a mod merely for convenient packaging. Track upstream source for debugging/API work and fork only when DrewCraft must maintain a source patch that cannot live cleanly in the integration mod.

## 7. Redistribution policy

The builder/launcher must support both:

1. artifacts DrewCraft is legally permitted to redistribute; and
2. artifacts that must be fetched from the original provider at build/install time.

The resulting file is always verified against the locked SHA-256.

Never commit third-party mod jars merely because doing so is convenient.

## 8. Client/server partition

Every dependency is classified as common, client-only, server-only, or operational tooling.

- **Common:** gameplay/content/protocol mods required on both sides.
- **Client:** rendering/UI/performance dependencies that a dedicated server should not load unless a documented multiplayer mode requires it.
- **Server:** admin/profiling/server-only helpers.
- **Operational:** tools such as Chunky when used only for world-build workflows.

The client and server packs must be generated from one source manifest rather than maintained independently.

## 9. Update rules

No dependency update goes directly to production.

Required flow:

1. update candidate/manifest metadata;
2. acquire the exact artifact through an allowed provider;
3. verify SHA-256;
4. build client/server packs;
5. boot dedicated server;
6. connect supported clients;
7. load the existing world where relevant;
8. test affected ownership boundaries (weather, Create, vehicle, worldgen, etc.);
9. inspect registry/mixin/network logs;
10. promote only after the relevant compatibility matrix passes.

World-generation dependency changes require extra caution because newly generated terrain may differ permanently from the existing production world.

## 10. V1 scope rule

DrewCraft V1 is **feature-complete and integration-complete, not balance-complete**.

The V1 mod stack therefore needs working systems and bridges, not broad recipe/economy retuning. Exact vehicle cost, fuel economics, aircraft price, radar progression and army difficulty belong to V1.1+ unless an upstream default demonstrably destroys a core design pillar.

The real version friends play is the **DrewCraft pack version**, not a collection of individual mod version numbers.
