# DrewCraft Project Specification

This document is the canonical gameplay/product specification for **DrewCraft**. The GitHub repository may still carry the internal name `ServerMc` until it is renamed; user-facing product/server naming is DrewCraft.

For release scope, `v_1_requirements.md` is authoritative. DrewCraft V1 is **feature-complete and integration-complete, not balance-complete**. Long-term progression goals in this document describe the direction for V1.1+ tuning unless they are explicitly listed as hard V1 requirements.

## 1. Product statement

DrewCraft is a private cooperative survival world designed around the fact that **the world is genuinely large**.

Most Minecraft modpacks respond to large worlds by adding faster teleportation. DrewCraft takes the opposite approach: large geography is the reason to build roads, railways, ports, airports, radar stations, defensive positions, supply chains and vehicles.

The world should feel persistent beyond the player's render distance. Weather systems move across regions. Animal populations can form herds. Hostile settlements can project force over distance. An army can be known to exist before it is physically loaded. A fortified settlement is useful because there are threats against which fortification matters.

The server should nevertheless remain recognizably Minecraft: mining, building, farms, caves, local mobs, redstone/Create contraptions, exploration and ordinary survival remain the substrate.

## 2. Core design rules

Any new mod or feature should pass these tests:

1. **Does it reinforce geography, infrastructure, weather, transportation, strategy or building?**
2. **Does it create a reason to build something in the world rather than bypass the world?**
3. **Does it preserve meaningful long-term progression potential?**
4. **Can it run reliably in multiplayer?**
5. **Can it be distributed and updated without asking friends to perform mod-management work?**
6. **Does it avoid duplicating another system already in the pack?**
7. **Does it have one clear authoritative subsystem owner?**

If the answer is mostly no, it probably does not belong in DrewCraft.

The subsystem ownership matrix in `MOD_STACK.md` should be consulted before adding a new mod.

## 3. World and geography

### 3.1 Terrain

The overworld target is Terrain Diffusion Plus on Minecraft 1.21.1 / NeoForge with **World Scale 2**.

At this scale, continental terrain, mountain chains, watersheds, rivers, valleys and climate zones operate at a much larger spatial scale than normal Minecraft. This is desirable. The map should contain journeys that feel like journeys.

Still Life is not a required dependency. Terrain Diffusion Plus is the baseline on its own unless a later test demonstrates that an additional world-generation layer materially improves the experience without destabilizing compatibility.

### 3.2 World boundary and pre-generation

The production world should be bounded and pre-generated before launch.

Reasons:

- Terrain Diffusion generation includes neural inference and expensive hydrology calculations.
- live generation can create severe latency spikes on a modest dedicated server.
- a bounded world makes storage, backup, strategic simulation, source-structure indexing and Distant Horizons preparation tractable.
- the border can be expanded deliberately in later releases after generating the next ring offline.

The exact initial radius is a benchmark/configuration decision, not hard-coded into the design document.

### 3.3 Structures

Use normal/sparse structures rather than flooding the world with points of interest. Large geography only works if empty space exists.

Strategically important hostile sites may include camps, forts, occupied ruins, towns and larger cities. These can come from carefully selected structure content or DrewCraft-specific structure data, but their density must remain low enough that discovering one matters.

### 3.4 Caves and underground

Terrain Diffusion Plus' 1.21.1 build already integrates its tall-world cave handling. Underground gameplay should remain substantial, but **do not add another general cave overhaul by default**. A second cave system is justified only if testing exposes a real deficiency that cannot be solved in the existing stack.

## 4. Travel and progression

### 4.1 No routine teleportation

Do not add Waystones or an equivalent routine player-teleport network.

Teleportation would remove the primary reason for the transportation/infrastructure stack.

### 4.2 Long-term intended travel progression

The desired eventual progression is approximately:

1. walking, horses, vanilla boats
2. maintained paths, roads, bridges, river routes
3. cars/trucks and local logistics
4. Create railways and industrial transport
5. large ships if a stable compatible implementation is available
6. expensive late-game aircraft and airports

These are not merely faster movement tiers. Each should eventually introduce infrastructure and operational constraints.

**This progression is a post-V1 balance target, not a V1 release blocker.** V1 needs the relevant transport systems to work together reliably; it does not need carefully rewritten recipes, fuel prices or acquisition curves.

### 4.3 Cars and trucks

Immersive Vehicles is the preferred road-vehicle foundation. V1 should provide a stable useful road vehicle set in multiplayer.

Long term, roads, fuel, repairs and acquisition cost should make cars valuable without replacing every other form of travel. Broad tuning of those costs belongs to V1.1+ after the complete system has been played.

### 4.4 Trains

Create trains are infrastructure-heavy by design and therefore fit the project extremely well. **Create is the authoritative rail system; do not add a parallel MTS/other train progression.**

Rail should eventually be particularly effective for repeated routes, heavy cargo, linking established settlements, industrial logistics and strategic supply movement.

V1 requires reliable Create rail functionality, not perfectly tuned rail economics.

### 4.5 Ships

A player-buildable large-ship system is desirable but compatibility-gated. Do not anchor V1 to an abandoned or unstable ship mod merely to satisfy the feature checklist.

Vanilla/small boats remain useful regardless.

### 4.6 Aircraft

V1 requires at least one stable supported aircraft integrated with DrewCraft weather.

The long-term target is for aircraft to be expensive and infrastructure-dependent through acquisition, fuel, runways/operating sites, weather awareness, navigation and maintenance. Those cost/progression details are **V1.1+ balance work** rather than prerequisites for V1.

Aircraft should make enormous geography manageable without making geography irrelevant.

### 4.7 Nether balance

Vanilla's 8:1 portal distance compression risks becoming the optimal solution to every long-distance trip.

If testing shows that this destroys the geography/transport premise, V1 may use a coarse portal-distance constraint or compression change sufficient to preserve the core pillar. Fine progression tuning remains post-V1.

There is no requirement to make aircraft practical in the Nether.

## 5. Weather and climate

### 5.1 Authority model

Project Atmosphere is the **sole atmospheric simulation authority**.

Simple Clouds is the cloud/localized-weather rendering substrate used with Atmosphere; it should not become a second independent weather authority.

Serene Seasons owns its season calendar/seasonal gameplay hooks where the selected Atmosphere dependency graph requires or benefits from it. Project Atmosphere consumes/integrates that seasonal state. DrewCraft does not create a third season system.

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

Terrain Diffusion already provides meaningful elevation and climate. DrewCraft should use the strongest stable integration available in this order:

1. biome/elevation coupling already available through the selected weather stack
2. direct bridge to Terrain Diffusion climate/elevation fields if stable APIs/data access make this feasible
3. additional terrain effects such as orographic precipitation, lee-side behavior and terrain-induced turbulence where computationally affordable

Do not duplicate Project Atmosphere's atmospheric simulation. DrewCraft bridges systems rather than rewriting them unnecessarily.

### 5.4 Aviation weather

Weather must have gameplay consequences for supported aircraft.

Required/desired effects include:

- crosswind
- headwind/tailwind ground-speed difference
- turbulence near strong gradients, storms and mountains
- reduced visibility
- storm avoidance incentives

Optional icing or richer severe-weather effects can follow only if they remain understandable and fun.

Gameplay-affecting weather state should be server-authoritative.

## 6. Radar and sensing

### 6.1 Purpose

Radar converts weather from random inconvenience into information players can invest in obtaining.

Radar belongs in the DrewCraft integration mod rather than as a second weather/radar ecosystem.

### 6.2 Ground weather radar

Ground installations should be physical builds, not a menu command.

A working site should require at minimum:

- radar dish/antenna
- controller/core
- power connection
- data/signal connection
- one or more physical screen/display blocks

The exact topology may evolve, but free-floating powered dishes should not be possible.

### 6.3 Height and line of sight

Antenna height should matter. Effective range should be bounded by equipment capability, antenna elevation, terrain obstruction/line of sight, an effective radar-horizon rule and server performance limits.

This gives towers, mountains and siting strategy practical value.

### 6.4 Radar progression

V1 may ship one functional radar tier or preliminary tiers. The eventual progression may vary maximum range, resolution, update frequency, storm-motion projection, severity information and display/network capacity.

**Perfect radar-tier costs and progression are post-V1 balance work.**

### 6.5 Physical displays

Radar screens must exist as rendered world blocks showing the connected radar core's feed. A GUI can exist for configuration, but the primary display concept is physical.

### 6.6 Aircraft radar

Supported aircraft should use the same atmospheric data pipeline for cockpit weather radar. Exact crafting cost, upgrade path and range balance may remain preliminary in V1.

## 7. Living-world simulation

### 7.1 Problem

Minecraft normally stops simulating almost everything outside loaded chunks. In a huge world this makes distance feel empty and prevents strategic threats from existing at the scale of the geography.

### 7.2 Strategic populations

DrewCraft maintains lightweight persistent records for selected populations even when no chunks are loaded.

Examples:

- animal herds
- zombie/undead hordes
- pillager/raider groups
- faction patrols
- large hostile armies

A strategic population record is not thousands of always-loaded entities. It is compact server-side state containing group identity/type, strength/composition, location, destination, speed, source, route and timestamps.

**DrewCraft is the sole macro strategic-population owner.** Do not add a second general world-scale horde/army/ecology simulator.

### 7.3 Materialization

When players approach a strategic group, the record materializes into ordinary entities. When safely distant again, surviving entities may be summarized back into strategic state.

Transitions must preserve casualties/composition so unload/reload cannot reset an army.

### 7.4 Hostile sources

Certain generated sites are persistent hostile sources with faction/type, population budget, reinforcement behavior, action cooldowns, objectives and cleared state.

A source can send groups toward player settlements or other strategic objectives.

### 7.5 Clearing sources matters permanently

Destroying/clearing a source changes persistent world state and stops or sharply reduces that site's future strategic force generation according to an explicit source rule.

Threat timing therefore depends on real geography and the nearest relevant intact source.

### 7.6 Movement across unloaded space

Unloaded movement should be deterministic enough to explain and cheap enough to simulate.

A group stores a route/corridor and advances based on elapsed simulation time and movement speed. Cost may account for broad terrain categories, roads, water, bridges and mountains without running full entity pathfinding over unloaded chunks.

No teleporting armies.

### 7.7 Attraction and objectives

Possible target signals include proximity, player settlement/activity, roads, faction objectives and retaliation after a source attack. The first implementation should stay understandable and deterministic.

## 8. Sieges and block interaction

### 8.1 Path first

Hostiles first use normal paths and accessible entrances: open routes, roads/bridges, usable gates/doors and navigable terrain.

### 8.2 Breach only when necessary

Only selected siege-capable units may meaningfully breach blocks, and only when no reasonable route exists or route cost exceeds an explicit threshold.

### 8.3 Structural targeting

Breaching chooses blocks that meaningfully open a route. It does not break the nearest block or randomly vandalize decoration.

Safeguards include planned breach corridors, hardness/time-based destruction, protected tags, rate limits and preference for sensible weak entrances.

### 8.4 Why this matters

The desired result is that walls, gates, kill zones, bridges, trenches, elevation and defensive weapons matter without making players afraid to build decorative structures.

## 9. Normal mobs, farms and spawners

Strategic simulation must not delete ordinary Minecraft ecology.

### 9.1 Local hostile spawning

Normal local hostile spawning remains enabled with only conservative tuning required for performance/safety. This preserves caves, night danger, mob farms and ordinary exploration encounters.

### 9.2 Strategic spawning is separate

Hostile sources do not replace vanilla spawning. A horde from a ruined city is a macro event layered on top of normal Minecraft mobs.

### 9.3 Spawners

Vanilla/modded spawner blocks may remain useful gameplay objects. Strategic source state is independent, so clearing a strategic hostile site does not require destroying every ordinary spawner/farm mechanic.

### 9.4 Animal herds

Distant herds use the same lightweight strategic architecture where possible. Nearby animals materialize into ordinary entities. A separate persistent ecology simulator should not be added.

## 10. Industry and power

Create is the primary technology/infrastructure mod and the authoritative rail system.

DrewCraft avoids adding a second giant tech/electrical tree merely to power radar. The custom integration exposes a small Create-compatible power adapter/controller converting sufficient kinetic input into DrewCraft's simple powered state/budget.

Do not pretend Create itself provides a generic electrical grid.

## 11. Multiplayer and administration

Required characteristics:

- version-locked clients/server
- reproducible releases
- automated backups
- controlled updates
- no secrets in client builds
- server-authoritative strategic state
- persistence across crashes/restarts
- admin commands for diagnosing weather, strategic groups, source state, radar and version mismatches
- ability to disable a custom subsystem if it destabilizes a play session

## 12. Friend-facing installation

The target experience is:

1. open the DrewCraft page
2. click Windows or Mac
3. run the bootstrapper
4. sign into Microsoft/Minecraft when Prism requests it
5. click Play thereafter

The launcher handles Java, Prism, NeoForge, exact mods/configs and updates. No friend should have to understand a mods folder.

## 13. Hosting

Oracle Ampere A1 ARM is the first low-cost deployment benchmark, not a V1 product requirement.

Critical principles:

- do not generate large amounts of Terrain Diffusion terrain live on the production host
- pre-generate elsewhere and upload the production world
- no automatic paid autoscaling
- keep world/custom strategic state/config/backups recoverable independently of the VM
- benchmark the complete stack honestly

If the preferred A1 target is inadequate, choosing a larger/alternate fixed host is preferable to cutting core V1 gameplay solely to fit it.

## 14. Non-goals

DrewCraft is not trying to be:

- a kitchen-sink pack
- an RPG quest pack
- a collection of every structure mod
- a hardcore realism simulator for its own sake
- a teleport-heavy convenience pack
- an extra-dimensions showcase
- an automation benchmark with competing power systems
- a pack with multiple terrain/cave generators
- a pack with multiple weather simulators
- a pack with multiple rail systems
- a pack with multiple world-scale horde/ecology simulators
- an MMO with thousands of permanently simulated NPCs

Realism is used where it produces interesting decisions, infrastructure and stories.

## 15. V1 acceptance direction

The exact release checklist lives in `v_1_requirements.md` and `v_1_development_tree.md`. At a minimum, one real V1 release candidate must demonstrate:

- clean one-click installation on Windows and Apple Silicon macOS
- automatic update from one pack version to the next
- stable loading of the pre-generated Terrain Diffusion world
- usable Distant Horizons
- functional road vehicles, Create trains and at least one aircraft
- aircraft affected by real weather
- a storm visible/trackable before arrival
- physical ground radar whose coverage responds to siting/height
- aircraft radar using the same weather data pipeline
- strategic hostile sources and unloaded movement with ETA
- casualty-preserving materialization/dematerialization
- multiple hostile compositions and large armies
- path-first constrained siege breaching
- permanent source clearing
- strategic animal herds
- normal local mob spawning/farming/spawners
- backup/restore of world and strategic state

V1 does **not** require a perfected economy or difficulty curve. Those are V1.1+ concerns once the full system can actually be played.
