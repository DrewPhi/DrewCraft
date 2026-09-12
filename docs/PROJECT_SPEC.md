# ServerMc Project Specification

This document is the canonical gameplay/product specification for ServerMc. It records the intended experience before implementation details force accidental design decisions.

## 1. Product statement

ServerMc is a private cooperative survival world designed around the fact that **the world is genuinely large**.

Most Minecraft modpacks respond to large worlds by adding faster teleportation. ServerMc takes the opposite approach: large geography is the reason to build roads, railways, ports, airports, radar stations, defensive positions, supply chains, and vehicles.

The world should feel persistent beyond the player's render distance. Weather systems move across regions. Animal populations can form herds. Hostile settlements can project force over distance. An army can be known to exist before it is physically loaded. A fortified settlement is useful because there are threats against which fortification matters.

The server should nevertheless remain recognizably Minecraft: mining, building, farms, caves, local mobs, redstone/Create contraptions, exploration, and ordinary survival remain the substrate.

## 2. Core design rules

Any new mod or feature should pass these tests:

1. **Does it reinforce geography, infrastructure, weather, transportation, strategy, or building?**
2. **Does it create a reason to build something in the world rather than bypass the world?**
3. **Does it preserve meaningful progression?**
4. **Can it run reliably in multiplayer?**
5. **Can it be distributed and updated without asking friends to perform mod-management work?**
6. **Does it avoid duplicating another system already in the pack?**

If the answer is mostly no, it probably does not belong in ServerMc.

## 3. World and geography

### 3.1 Terrain

The overworld target is Terrain Diffusion Plus on Minecraft 1.21.1 / NeoForge with **World Scale 2**.

At this scale, continental terrain, mountain chains, watersheds, rivers, valleys, and climate zones operate at a much larger spatial scale than normal Minecraft. This is desirable. The map should contain journeys that feel like journeys.

Still Life is not a required dependency. Terrain Diffusion Plus is the baseline on its own unless a later test demonstrates that an additional world-generation layer materially improves the experience without destabilizing compatibility.

### 3.2 World boundary and pre-generation

The production world should be bounded and pre-generated before launch.

Reasons:

- Terrain Diffusion generation includes neural inference and expensive hydrology calculations.
- live generation can create severe latency spikes on a modest dedicated server.
- a bounded world makes storage, backup, strategic simulation, source-structure indexing, and Distant Horizons preparation tractable.
- the border can be expanded deliberately in later seasons/releases after generating the next ring offline.

The exact initial radius is a benchmark/configuration decision, not hard-coded into the design document.

### 3.3 Structures

Use normal/sparse structures rather than flooding the world with points of interest. Large geography only works if empty space exists.

Strategically important hostile sites may include camps, forts, occupied ruins, towns, and larger cities. These can come from carefully selected structure content or ServerMc-specific structure data, but their density must remain low enough that discovering one matters.

### 3.4 Caves and underground

Terrain Diffusion Plus' 1.21.1 build already integrates its tall-world cave handling. Underground gameplay should remain substantial but should not be overloaded with multiple competing cave overhauls unless testing demonstrates a need.

## 4. Travel and progression

### 4.1 No routine teleportation

Do not add Waystones or an equivalent routine player-teleport network.

Teleportation would remove the primary reason for the transportation/infrastructure stack.

### 4.2 Intended travel progression

The desired progression is approximately:

1. walking, horses, vanilla boats
2. maintained paths, roads, bridges, river routes
3. cars/trucks and local logistics
4. Create railways and industrial transport
5. large ships if a stable compatible implementation is available
6. expensive late-game aircraft and airports

These are not merely faster movement tiers. Each should introduce infrastructure and operational constraints.

### 4.3 Cars

Immersive Vehicles is the preferred realistic vehicle foundation. Cars should become useful in the mid-game, especially once roads connect settlements/resources.

Recipes, fuel, repair, speed, terrain handling, and vehicle availability should be tuned so cars are valuable without replacing every other form of travel.

### 4.4 Trains

Create trains are infrastructure-heavy by design and therefore fit the project extremely well.

Rail should be particularly effective for:

- repeated routes
- heavy cargo
- linking established settlements
- moving resources between industrial sites
- strategic logistics during large attacks

### 4.5 Ships

A player-buildable large-ship system is desirable but compatibility-gated. Do not anchor the pack to an abandoned or unstable ship mod merely to satisfy the feature checklist.

Vanilla/small boats remain useful regardless.

### 4.6 Aircraft

Aircraft should be late-game and expensive. They should require meaningful supporting infrastructure such as:

- aircraft acquisition/construction
- fuel
- runway or suitable operating site
- weather awareness
- navigation
- maintenance/resource cost

Aircraft should make enormous geography manageable without making geography irrelevant.

### 4.7 Nether balance

Vanilla's 8:1 portal distance compression risks becoming the optimal solution to every long-distance trip.

ServerMc should test reduced portal compression (for example approximately 2:1) or other portal constraints if normal Nether travel trivializes roads, trains, ships, and aircraft. This remains a tunable balance rule rather than a fixed implementation requirement until playtesting.

There is no requirement to make aircraft practical in the Nether.

## 5. Weather and climate

### 5.1 Baseline

Project Atmosphere + Simple Clouds are the intended weather foundation, with Serene Seasons integration where stable.

Weather should be spatial and persistent rather than a global random toggle. A player should be able to see a storm system approaching from far away.

### 5.2 Desired atmosphere behavior

The experience should communicate:

- wind direction and speed
- moving cloud systems
- precipitation attached to cloud/weather systems
- temperature and seasonal differences
- storm development and decay
- reduced visibility in heavy weather
- distant visual warning of major systems

### 5.3 Terrain coupling

Terrain Diffusion already provides meaningful elevation and climate. ServerMc should use the strongest stable integration available in this order:

1. baseline biome-driven coupling if Project Atmosphere already derives climate from loaded biome/elevation context
2. direct bridge to Terrain Diffusion climate/elevation fields if stable APIs/data access make this feasible
3. additional terrain effects such as orographic precipitation, lee-side behavior, and terrain-induced turbulence where computationally affordable

Do not duplicate Project Atmosphere's atmospheric simulation. ServerMc should bridge systems rather than rewrite them unnecessarily.

### 5.4 Aviation weather

Weather must have gameplay consequences for aircraft.

Candidate effects:

- crosswind component
- headwind/tailwind ground-speed difference
- turbulence near strong gradients, storms, and mountains
- reduced visibility
- storm avoidance incentives
- optional icing/severe-weather effects only if they remain fun and understandable

The server should be authoritative for the weather state used by flight effects.

## 6. Radar and sensing

### 6.1 Purpose

Radar converts weather from random inconvenience into information players can invest in obtaining.

### 6.2 Ground weather radar

Ground installations should be physical builds, not a menu command.

A working site should require at minimum:

- radar dish/antenna
- controller/core
- power connection
- data/signal connection
- one or more physical screen/display blocks

The exact block topology may evolve, but free-floating powered dishes should not be possible.

### 6.3 Height and line of sight

Antenna height should matter.

Effective range should be bounded by:

- hardware tier
- antenna elevation
- terrain obstruction / line of sight
- an effective radar-horizon rule
- optionally weather attenuation for extreme systems if worth the complexity

This gives towers, mountains, and siting strategy practical value.

### 6.4 Radar tiers

Tiers should change meaningful capabilities rather than only crafting cost. Possible dimensions include:

- maximum range
- angular resolution
- update frequency
- storm-motion projection
- vertical/severity information
- network/display capacity

### 6.5 Physical displays

Radar screens must exist as rendered world blocks showing the connected radar core's feed. A GUI can exist for configuration, but the primary display concept is physical.

### 6.6 Aircraft radar

Compatible aircraft can equip a cockpit weather-radar instrument using the same atmospheric data model. Range/quality should be constrained by the installed instrument and aircraft power/configuration.

## 7. Living-world simulation

### 7.1 Problem

Minecraft normally stops simulating almost everything outside loaded chunks. In a huge world this makes distance feel empty and prevents strategic threats from existing at the scale of the geography.

### 7.2 Strategic populations

ServerMc should maintain lightweight persistent records for selected populations even when no chunks are loaded.

Examples:

- animal herds
- zombie hordes
- pillager/raider groups
- faction patrols
- large hostile armies

A strategic population record is not thousands of always-loaded entities. It is a compact server-side state such as group type, strength, composition, location, destination, speed, health/readiness, source, route, and timestamps.

### 7.3 Materialization

When players approach a strategic group, the record materializes into ordinary entities in loaded chunks. When the encounter ends or the group moves far enough away, surviving entities can be summarized back into strategic state.

Transitions must preserve approximate casualties and composition so unload/reload cannot reset an army.

### 7.4 Hostile sources

Certain generated sites are persistent hostile sources.

A source can have:

- faction/type
- population budget
- reinforcement rate
- patrol/army cooldown
- detection/influence radius
- strategic objectives
- destroyed/cleared state

A source can send groups toward players, player settlements, roads, or other objectives.

### 7.5 Clearing sources matters permanently

Destroying/clearing a source should change the persistent world state and stop or sharply reduce that site's future strategic spawns.

Threat timing therefore depends on geography: the nearest intact hostile source may be days of strategic travel away, or a fort may exist just over the mountains.

### 7.6 Movement across unloaded space

Unloaded movement should be deterministic enough to explain and cheap enough to simulate.

A group stores a route or route corridor and advances based on elapsed wall/game time and strategic movement speed. Path cost can account for broad terrain categories, roads, water, bridges, mountains, and other map features without running full Minecraft entity pathfinding over unloaded chunks.

No teleporting armies.

### 7.7 Attraction and objectives

Possible reasons for a hostile group to choose a target:

- proximity
- player settlement/activity score
- noise/industrial activity
- known roads
- faction objective
- retaliation after a hostile source is attacked

The first implementation should stay understandable and deterministic; richer behavior can follow.

## 8. Sieges and block interaction

### 8.1 Path first

Hostiles should first use normal paths and accessible entrances.

They should prefer:

- open routes
- roads/bridges
- gates/doors where their mob type can interact
- navigable stairs/terrain

### 8.2 Breach only when necessary

Selected siege units may breach blocks only when the planner determines no viable route to the target exists or a route exceeds configured cost limits.

### 8.3 Structural targeting

Breaching should choose blocks that meaningfully open a route. It should not simply break the nearest block or randomly vandalize decoration.

Candidate safeguards:

- only blocks lying on a planned breach corridor
- hardness/time-based destruction
- protected/unbreakable block tags
- no arbitrary block breaking outside an active siege objective
- rate limits and group-specific breach capability
- prefer doors/gates/weaker materials before thick structural walls

### 8.4 Why this matters

The desired result is that building a castle is a real engineering decision. Walls, gates, kill zones, bridges, trenches, elevation, fallback lines, and defensive weapons should matter.

The system must create reasons for good architecture without making players afraid to build decorative structures.

## 9. Normal mobs, farms, and spawners

Strategic simulation must not delete ordinary Minecraft ecology.

### 9.1 Local hostile spawning

Normal local hostile spawning remains enabled with tuning as required for performance/balance. This preserves:

- caves
- night danger
- normal mob farms
- ordinary exploration encounters

### 9.2 Strategic spawning is separate

Hostile structures do not need to replace every vanilla spawn. A zombie horde coming from a ruined city is a macro event layered on top of normal zombies.

### 9.3 Spawners

Vanilla/modded spawner blocks may remain lootable/preservable gameplay objects. A strategic source should be represented by persistent source state rather than relying on one vanilla spawner block, so players do not have to choose between keeping a useful farm block and ending world-scale attacks.

### 9.4 Animal herds

Herd behavior should make large landscapes feel inhabited while controlling entity count. Strategic herd records are preferable for distant populations; nearby animals can materialize into normal entities.

## 10. Industry and power

Create is the primary technology/infrastructure mod.

ServerMc should avoid adding a second giant tech tree merely to power radar. The custom integration can expose a Create-compatible power adapter/controller. Radar/data cabling can be ServerMc-specific if needed.

Create's core system is rotational stress rather than conventional electricity, so the implementation should be explicit: either consume Create kinetic power through a dedicated adapter or add a very small ServerMc electrical abstraction backed by Create generation. Do not pretend Create itself provides a generic electrical grid.

## 11. Multiplayer and administration

The server is intended for friends rather than a public MMO, but it should be operationally robust.

Required characteristics:

- version-locked clients/server
- reproducible releases
- automated backups
- controlled updates
- no secrets in client builds
- server-authoritative strategic state
- persistence across crashes/restarts
- admin commands for diagnosing weather, strategic groups, source state, and version mismatches
- ability to disable a custom subsystem via configuration if it destabilizes a play session

## 12. Friend-facing installation

The user experience target is:

1. open the ServerMc download page
2. click Windows or macOS
3. run the bootstrapper
4. sign into Microsoft/Minecraft once when Prism requests it
5. click Play thereafter

The launcher handles Java, Prism instance creation, NeoForge, exact mods/configs, and updates.

No friend should have to understand a mods folder.

## 13. Hosting

Oracle Ampere A1 ARM is the first deployment target because it can potentially provide the required Java server at extremely low/no compute cost.

The current Always Free baseline must be treated as 2 OCPU / 12 GB total and benchmarked honestly.

Critical constraints:

- do not generate large amounts of Terrain Diffusion terrain live on the A1 host
- pre-generate elsewhere and upload the production world
- no automatic paid autoscaling
- keep world, strategic database/state, configuration, and backups recoverable independently of the VM
- benchmark tick time with representative Create contraptions, Atmosphere simulation, loaded mobs, and a materialized siege

If free A1 is inadequate, scaling is an explicit owner decision.

## 14. Non-goals

ServerMc is not trying to be:

- a kitchen-sink pack
- an RPG quest pack
- a collection of every structure mod
- a hardcore realism simulator for its own sake
- a teleport-heavy convenience pack
- an extra-dimensions showcase
- an automation benchmark with five competing power systems
- an MMO with thousands of permanently simulated NPCs

Realism is used where it produces interesting decisions, infrastructure, and stories.

## 15. Acceptance criteria for the eventual 1.0 server

A 1.0-quality build should demonstrate all of the following in a real multiplayer test:

- clean one-click installation on Windows and Apple Silicon macOS
- automatic update from one pack version to the next
- server rejects or launcher repairs stale clients before connection
- stable world loading from the pre-generated Terrain Diffusion map
- Distant Horizons usable without unacceptable client burden
- cars and trains useful for materially different travel/logistics roles
- at least one tested aircraft with wind/weather integration
- a storm visible and trackable before arrival
- a ground radar site whose useful range improves with siting/height
- a physical radar display
- a strategic hostile source that launches a group
- that group advances while unloaded and arrives at approximately the predicted time
- the group materializes without duplication/reset exploits
- a siege attempts valid paths before any block breach
- clearing the source prevents future forces from that source
- normal local mob spawning/farming still works
- backup/restore recovers both world blocks and strategic state

Until those tests pass, the project is still a development build regardless of how many mods are installed.
