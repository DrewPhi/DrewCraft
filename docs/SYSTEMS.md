# ServerMc Custom Systems

This document describes the functionality that should be owned by the custom `servermc` NeoForge integration mod rather than delegated to a pile of overlapping mods.

The preferred implementation is **one distributable integration mod with clean internal modules**, not many tiny jars that can drift out of sync.

## 1. Module map

Suggested package/module boundaries:

```text
servermc
├── compat/
│   ├── terraindiffusion/
│   ├── atmosphere/
│   ├── immersivevehicles/
│   └── create/
├── weather/
├── aviation/
├── radar/
├── worldsim/
├── siege/
├── spawning/
├── progression/
├── network/
├── persistence/
├── commands/
└── config/
```

Every compatibility module must fail gracefully if the corresponding optional integration is disabled during development.

## 2. Persistence model

Strategic state must not live only in loaded entities.

The server should persist world-simulation state using Minecraft SavedData or an equivalent versioned server-side persistence layer.

At minimum, persist:

- source structures and whether they are intact/cleared
- strategic groups
- strategic routes/destinations
- group composition/strength
- departure and last-update times
- faction/type
- materialization state / encounter identifier
- relevant cooldowns
- radar network identities/configuration where block entities alone are insufficient
- simulation schema version

Persistence writes should be crash-safe and migration-aware.

## 3. StrategicWorldSimulation

### 3.1 Source records

Each strategic source should have a stable ID and data similar to:

```text
SourceRecord
  id
  dimension
  position / region
  sourceType
  faction
  state: INTACT | DAMAGED | CLEARED
  populationBudget
  reinforcementRate
  nextActionTime
  influenceRadius
  metadata
```

Do not use the presence of one ordinary spawner block as the canonical source state.

### 3.2 Group records

A strategic group can be represented approximately as:

```text
StrategicGroup
  id
  faction
  groupType
  sourceId
  dimension
  strategicPosition
  route
  destination
  movementSpeed
  compositionSummary
  strength
  state: MOVING | WAITING | MATERIALIZED | RETREATING | DESTROYED
  lastSimulatedTime
  encounterId
```

The exact serialization format is an implementation choice, but identity must survive restart/unload.

### 3.3 Simulation cadence

Do not tick every group every game tick.

Use coarse scheduled updates or time-delta advancement. For a moving group:

```text
distance_advanced = strategic_speed * elapsed_time
```

Advance along a precomputed or incrementally computed route corridor.

This makes hundreds of distant groups cheap while avoiding teleportation.

### 3.4 Strategic pathing

Do not run vanilla entity pathfinding over unloaded chunks.

Build a lower-resolution strategic cost field from information available for the bounded world. Candidate cells may represent chunks or larger regions.

Costs can encode:

- slope/elevation bands
- water
- roads
- bridges
- mountain passes
- hostile/friendly territory
- impassable regions

Roads should reduce movement cost enough that infrastructure can affect military/logistics movement if this remains computationally practical.

### 3.5 ETA

The simulation should expose an ETA for debugging and potentially player intelligence systems.

ETA should come from remaining route cost / effective speed, not an arbitrary event timer.

## 4. Materialization and dematerialization

### 4.1 Materialization trigger

When a player/load radius intersects a strategic group, create a materialization transaction:

1. mark the strategic group `MATERIALIZING`/locked
2. assign encounter ID
3. spawn entity composition from the strategic summary
4. tag every entity with strategic group + encounter IDs
5. only after successful spawn mark group `MATERIALIZED`

This prevents duplicate armies if a chunk unload/reload occurs during spawning.

### 4.2 Tracking casualties

Tagged entities report deaths/removals back to the encounter record. The strategic summary must decrease accordingly.

### 4.3 Dematerialization

When no relevant players remain nearby for a configurable period:

1. freeze/collect surviving encounter entities
2. convert survivors to strategic composition/health
3. remove those entities
4. restore the strategic group to coarse simulation
5. record current position and timestamp

Never recreate the original army strength after unload.

### 4.4 Encounter edge cases

Tests must cover:

- server restart while materialized
- chunk unload during spawn
- player logout during encounter
- mobs captured/moved far away
- dimension travel
- entity death outside normal damage flow
- two players causing overlapping materialization radii

## 5. Animal herds

Use the same strategic representation for distant herds where possible.

A herd record can contain species, approximate count, center, movement tendency, home region, and last update.

When nearby, materialize ordinary compatible animal entities. When distant, summarize them.

This is preferable to keeping enormous numbers of animals loaded merely to make the world feel populated.

## 6. Hostile source lifecycle

### 6.1 Discovery

When a qualifying generated structure is first indexed/generated, register a SourceRecord.

### 6.2 Production

Sources can create strategic groups according to faction/type-specific rules, population budget, cooldown, and nearby strategic conditions.

### 6.3 Clearing

Clearing should require an explicit condition that can be communicated to players. Candidate designs:

- eliminate defenders + destroy a marked command/core block
- capture/disable a source controller
- satisfy a structure-specific objective

The final design must avoid hidden conditions that leave players unsure whether a site is actually neutralized.

### 6.4 Persistence

A cleared source remains cleared across restart and unloaded periods unless a later feature explicitly supports recapture/reoccupation.

## 7. Local spawning coexistence

The custom world simulation is additive.

ServerMc should expose configuration hooks for local spawn caps/rules but not globally remove vanilla spawning.

A separate integration layer can coordinate with a spawn-control mod if needed, but the stable principle is:

- ordinary local spawns create ordinary Minecraft encounters and farms
- strategic sources create persistent macro-scale groups
- special structure-local spawns are allowed but must not be the only strategic state

## 8. SiegePlanner

### 8.1 Goal

Create hostile behavior capable of attacking defended settlements without enabling indiscriminate griefing.

### 8.2 Two-level planning

Use a two-stage approach:

1. **normal navigation**: find a viable entity path to the objective
2. **breach planning**: only if normal navigation fails or exceeds configured cost, identify a minimal/low-cost structural breach

### 8.3 Breach candidate scoring

Candidate breach locations should be scored using factors such as:

- expected blocks to remove
- hardness/break time
- whether opening the blocks produces a navigable corridor
- doors/gates vs solid wall
- vertical accessibility
- protected block tags
- distance from group

Do not use nearest-block destruction.

### 8.4 Breach permissions

Only specific mob/unit roles receive breach capability.

Examples:

- ordinary zombies: path/gate pressure, little or no structural breach
- specialized siege mobs: slow structural damage
- explosive/special units: limited high-impact breach behavior

Exact units can use vanilla/modded entities, but their ability should be configured through tags/interfaces rather than hard-coded entity lists where possible.

### 8.5 Decoration safety

A block is eligible for siege damage only if it participates in an active breach corridor or belongs to explicitly breachable interaction categories.

This rule is central to the project. The system should not decide a statue is a good target because it happens to be close.

### 8.6 Performance

Siege planning is expensive. Cache plans, recompute only when meaningful world changes invalidate them, and rate-limit planners per encounter.

## 9. Weather integration

### 9.1 Data adapter

Create a stable internal weather interface so ServerMc logic does not depend everywhere on Project Atmosphere internals.

Example conceptual API:

```text
WeatherSample sample(dimension, position, time)
  temperature
  pressure
  humidity
  windVector
  precipitation
  stormSeverity
  cloudMotion
  visibility
```

The Project Atmosphere adapter populates this structure.

### 9.2 Terrain adapter

Similarly expose Terrain Diffusion information through one adapter:

```text
TerrainClimateSample
  elevation
  temperatureClimate
  seasonality
  precipitationClimate
  precipitationVariability
  biome
```

If direct Terrain Diffusion climate APIs are unavailable/stable only indirectly, return what can be derived and let the bridge fall back to biome/elevation behavior.

### 9.3 Terrain/weather bridge

Start with low-risk effects:

- elevation adjustment
- mountain turbulence
- biome/climate-aware defaults

Only then attempt more ambitious orographic precipitation/lee effects if the atmospheric mod exposes suitable extension points.

Avoid forking Project Atmosphere unless absolutely necessary.

## 10. Aviation weather bridge

### 10.1 Wind

Aircraft should experience a relationship between air-relative velocity and ground-relative velocity.

The bridge should use the atmosphere's wind vector rather than invent a separate wind system.

### 10.2 Turbulence

A gameplay turbulence field can combine:

- local wind variability
- storm severity
- terrain gradient / mountain proximity
- altitude

The resulting effect should be bounded and tunable; realism that makes controls unusable is not the goal.

### 10.3 Authority and networking

Compute authoritative environmental state server-side where practical, then synchronize minimal state required for smooth client rendering/control feedback.

Do not trust a client-only weather value for gameplay-affecting flight physics.

## 11. Radar system

### 11.1 Radar network objects

A ground radar installation can consist of:

- `RadarDishBlockEntity`
- `RadarControllerBlockEntity`
- `RadarDisplayBlockEntity`
- power adapter
- data/power cable network

The controller owns scan settings and cached products; displays subscribe to a controller.

### 11.2 Power

Create does not provide generic electricity by default.

Preferred minimal approach:

- radar controller requires a ServerMc power adapter driven by Create kinetic stress/RPM
- adapter converts sufficient mechanical input into a simple internal powered state/budget
- dish and display require a connected ServerMc cable network

This provides physical infrastructure without importing a giant second tech progression.

### 11.3 Connectivity

A radar installation is valid only if the graph from controller to dish and required displays/power adapters is intact.

Cable length/throughput limits can become progression knobs if useful, but the first implementation should stay simple.

### 11.4 Range model

A scan's effective range should be approximately:

```text
effectiveRange = min(tierRange, horizonRange, configuredSimulationLimit)
```

Then apply terrain masking/line-of-sight where appropriate.

`horizonRange` can use an effective-radius approximation such as:

```text
d ≈ sqrt(2 * R_effective * h)
```

mapped into ServerMc's horizontal scale and tuned for gameplay. It does not need to claim Minecraft is literally spherical; it is a mechanic that rewards antenna height with diminishing returns.

### 11.5 Terrain masking

Use cached/coarse height samples rather than per-block raycasts for every weather cell on every scan.

A polar horizon mask from the antenna is a promising optimization: for each azimuth sector, cache the maximum terrain elevation angle. Recompute when the antenna changes or when nearby terrain changes materially.

### 11.6 Weather products

Candidate radar products:

- precipitation intensity
- severe storm cells
- storm motion vector / short projection
- tornado/hurricane/severe overlays if exposed by Project Atmosphere

Use Project Atmosphere/Simple Clouds data; do not fabricate a separate storm model.

### 11.7 Display rendering

The display block should render a shared/cached radar texture or data product, not make every display independently scan the world.

Multiple screens connected to one controller should be cheap.

### 11.8 Aircraft radar

Aircraft radar uses the same weather sampling/product pipeline with aircraft-specific constraints:

- instrument tier
- aircraft position/altitude
- forward/sector scan if desired
- shorter update/cache lifetime while moving

Integration with Immersive Vehicles should be isolated in the compatibility adapter.

## 12. Networking

Use explicit protocol/versioning for custom packets.

Likely packet families:

- server pack/protocol capability handshake
- radar display updates
- radar configuration changes
- strategic debug/admin data
- client visual weather/aviation state if required

Never stream entire strategic state to normal clients.

## 13. Configuration

Configuration should separate:

- gameplay tuning
- performance limits
- compatibility feature flags
- debug/development behavior

Examples:

```text
worldsim.enabled
worldsim.max_groups
worldsim.materialization_radius
worldsim.coarse_tick_seconds
siege.enabled
siege.max_concurrent_planners
siege.block_damage
radar.enabled
radar.max_scan_radius
radar.scan_interval
aviation.weather_effects
compat.terrain_diffusion
compat.project_atmosphere
compat.immersive_vehicles
compat.create
```

Ship known-good production defaults in the pack. Do not require friends to edit them.

## 14. Commands and observability

Admin/developer commands are essential because these systems operate invisibly across unloaded chunks.

Suggested command surface:

```text
/servermc version
/servermc weather sample <pos>
/servermc radar inspect <pos>
/servermc worldsim list
/servermc worldsim inspect <groupId>
/servermc worldsim eta <groupId>
/servermc source list
/servermc source inspect <sourceId>
/servermc siege inspect
/servermc debug perf
```

Commands should expose reasons and state, not only IDs.

## 15. Performance budgets

The architecture must assume a relatively constrained server.

Rules:

- no distant entity ticking
- no per-tick global scans
- no full-resolution strategic pathfinding over the whole world
- no independent atmospheric simulation inside ServerMc
- no radar product recomputation per display
- cache aggressively where the world is static
- use elapsed-time coarse simulation for unloaded populations
- cap concurrent siege planners
- expose timing metrics

## 16. Failure isolation

Each major custom subsystem should have a server config kill switch.

If, for example, radar rendering has a bug, the server should still be playable with radar disabled while a fix is prepared.

Persisted data should be versioned so turning a system off temporarily does not destroy its state.

## 17. Testing targets

Automated/unit or game tests should eventually cover:

- strategic movement integration over elapsed time
- route determinism
- source clear persistence
- materialization idempotence
- casualty preservation through unload/reload
- no duplicate strategic groups after restart
- siege planner prefers open path over breach
- breach corridor actually opens navigable route
- protected/decorative off-corridor blocks untouched
- radar connectivity graph
- radar power loss behavior
- height/range monotonicity
- terrain masking
- multiple displays sharing one scan
- weather adapter fallback behavior
- compatibility disabled/missing-mod startup

The custom mod should be treated as real server software, not only as a collection of mixins that happened to work once.
