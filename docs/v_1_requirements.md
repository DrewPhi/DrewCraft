# DrewCraft V1 Requirements

This document defines the **hard requirements for DrewCraft V1**.

The V1 philosophy is:

> **Feature-complete and integration-complete, not balance-complete.**

V1 should contain the full DrewCraft experience as currently designed: the large world, transportation stack, weather, aviation, radar, persistent strategic mobs, hostile sources, armies, sieges, animal herds, one-click launcher, reproducible releases, and production server operations. The defining systems and compatibility bridges must work end-to-end.

V1 does **not** require a bespoke difficulty/economy pass. Wherever possible, upstream/default mod recipes and progression should remain intact for the first release. We should play the complete system first, then tune costs, recipes, spawn rates, progression, fuel economics, and difficulty using actual multiplayer experience.

---

## 1. V1 product definition

DrewCraft V1 is a private cooperative Minecraft survival server where:

- geography is genuinely large and meaningful;
- travel infrastructure matters;
- weather is spatial, visible, and mechanically important;
- cars, trains, and aircraft exist in one coherent world;
- radar is physical infrastructure rather than a minimap cheat;
- animal and hostile populations can persist beyond loaded chunks;
- hostile camps/forts/cities can send groups and armies across the world;
- those groups take real strategic travel time to reach players;
- clearing hostile sources changes the long-term world;
- castles and defenses work because hostile forces understand routes and controlled breaching;
- normal Minecraft building, mining, caves, local mob spawning, and farms still work underneath the strategic layer;
- friends install and update the entire game through the DrewCraft launcher without manually managing Java, NeoForge, mods, or configs.

V1 is complete when all of those ideas work together reliably in multiplayer.

---

# 2. Platform and reproducibility

V1 MUST use one locked, reproducible release configuration.

Required baseline:

- Minecraft **1.21.1**
- **NeoForge**
- **Java 21**
- a machine-readable pack manifest containing exact dependency versions and hashes
- explicit `common`, `client-only`, and `server-only` dependency classification
- reproducible client and server pack generation from the repository
- a DrewCraft pack version independent of individual mod versions
- client/server protocol/version compatibility checks

A developer's local `mods/` directory MUST NOT be the source of truth.

Third-party jars, Java runtimes, model files, full worlds, backups, and large generated caches SHOULD NOT be committed directly to Git unless licensing and repository-size considerations explicitly justify it.

---

# 3. Required world stack

## 3.1 Terrain Diffusion Plus

V1 MUST use Terrain Diffusion Plus as the overworld-generation foundation.

Target configuration:

- **World Scale 2**
- geographically large terrain
- meaningful mountain chains, rivers, valleys, climate zones, and long-distance travel
- bounded production world
- production terrain pre-generated before deployment

The live production server SHOULD NOT be expected to perform large amounts of diffusion terrain generation during ordinary play.

## 3.2 Chunk pre-generation

V1 MUST include a reproducible world-build pipeline using Chunky or the final compatible equivalent.

The world pipeline MUST record:

- generation pack version
- world identity / seed where applicable
- Terrain Diffusion configuration
- World Scale
- world-border / generation radius
- generation commands/configuration
- resulting world archive checksum

The production world MUST be restorable from a clean server environment.

## 3.3 Distant Horizons

Distant Horizons is a V1 requirement because the visual experience needs to communicate the scale of the world.

It MUST be tested on:

- Windows
- Apple Silicon macOS
- Ubuntu/Linux x86-64
- the final weather/cloud rendering stack

Pack defaults SHOULD provide a usable experience without expecting every friend to tune advanced graphics settings manually.

## 3.4 Structures

V1 SHOULD use a relatively sparse structure distribution.

The world MUST preserve meaningful empty geography rather than becoming a dense theme park of structures.

Strategically important hostile source structures MAY be custom DrewCraft structures or selected compatible generated structures.

For V1, When Dungeons Arise MUST use an explicit allow-list. Every enabled WDA
structure MUST remain a complete explorable dungeon with its intended mobs and
loot while also serving as a DrewCraft strategic source. All other WDA
structures MUST be disabled for production world generation.

---

# 4. Required base gameplay/mod stack

V1 MUST include, subject to final version-lock compatibility:

- Terrain Diffusion Plus
- Chunky for world-generation operations
- Distant Horizons
- Create
- Immersive Vehicles / MTS
- a curated, minimal set of vehicle content packs containing useful cars/trucks and aircraft
- Project Atmosphere
- Simple Clouds
- Serene Seasons if it remains stable with the final weather stack
- all required support libraries

A large player-buildable ship system is **desired but not a hard V1 blocker**. It should be included only if a stable 1.21.1 NeoForge implementation is proven compatible with the rest of the pack.

V1 MUST NOT add routine teleportation such as Waystones.

V1 SHOULD avoid unnecessary giant tech mods, dimensions, structure packs, or unrelated survival-overhaul systems.

---

# 5. Create and infrastructure

Create is the primary technology and infrastructure language for V1.

V1 MUST support:

- ordinary Create contraptions
- industrial/logistics use
- Create trains
- bridges/tunnels/infrastructure built around large-distance travel
- DrewCraft integrations that consume Create-compatible power where appropriate

DrewCraft SHOULD NOT import a second giant technology tree solely to power radar or other custom systems.

Where custom infrastructure needs electrical-style power, V1 SHOULD use a small DrewCraft adapter that converts Create kinetic input into the custom system's required powered state.

---

# 6. Transportation

## 6.1 Cars and trucks

V1 MUST include at least one stable, useful road vehicle set through Immersive Vehicles.

Cars/trucks MUST function correctly in multiplayer and be useful across the large world.

## 6.2 Trains

Create trains MUST work reliably in multiplayer and provide long-distance infrastructure/logistics capability.

## 6.3 Aircraft

V1 MUST include at least one stable supported aircraft.

Aircraft MUST be integrated with DrewCraft weather effects as defined below.

## 6.4 Ships

Large ships are optional for V1 if no sufficiently stable implementation is available.

Small/vanilla water travel remains valid regardless.

## 6.5 Nether travel

V1 does **not** require a perfectly tuned transportation progression.

However, if vanilla Nether 8:1 distance compression clearly destroys the core geography/transport premise during testing, V1 MAY include a coarse portal-distance rule change.

This is considered preservation of the core world design, not a general balance pass.

---

# 7. Required integration bridges

The V1 DrewCraft NeoForge integration mod MUST contain stable compatibility adapters rather than scattering one-off patches throughout the repository.

At minimum, V1 requires bridges for:

1. **Terrain Diffusion -> DrewCraft terrain/climate interface**
2. **Project Atmosphere -> DrewCraft weather interface**
3. **Project Atmosphere -> Immersive Vehicles aviation effects**
4. **Terrain/elevation -> aviation turbulence effects**
5. **Project Atmosphere -> ground radar**
6. **Project Atmosphere -> aircraft radar**
7. **Create -> radar/infrastructure power adapter**
8. **generated hostile structures -> persistent strategic source registry**
9. **strategic groups -> loaded Minecraft entities**
10. **loaded entity deaths/survivors -> strategic group state**
11. **strategic groups -> siege planner when attacking a defended target**
12. **normal local spawning -> coexistence with the strategic world simulation**

All major adapters MUST fail gracefully or expose a clear diagnostic if an expected upstream mod/API changes.

---

# 8. Weather system

Project Atmosphere + Simple Clouds are the atmospheric source of truth for V1.

V1 MUST provide spatial weather that communicates:

- moving cloud/weather systems
- wind direction and speed
- precipitation associated with weather systems
- storms visible from meaningful distance
- reduced visibility during sufficiently bad weather
- seasonal/climate behavior where supported

DrewCraft SHOULD consume Project Atmosphere state rather than implementing a second independent atmosphere simulation.

---

# 9. Terrain/weather coupling

V1 MUST expose terrain/elevation information to DrewCraft systems that need it.

Minimum V1 terrain-weather coupling:

- elevation available to weather/aviation logic
- climate/biome information available where stable
- terrain/mountain influence on aviation turbulence

More ambitious meteorology such as fully modeled orographic precipitation or lee-side rain shadows is desirable but is **not required if the upstream APIs do not support it robustly**.

The essential V1 requirement is that the relevant systems communicate rather than behave as disconnected mods.

---

# 10. Aviation weather

Weather MUST have real gameplay consequences for supported aircraft in V1.

Required V1 effects:

- wind vector affects flight / ground-relative movement in a meaningful way
- crosswind is detectable
- headwind/tailwind matters
- turbulence can occur
- storms increase turbulence/severity
- terrain/mountain proximity can contribute to turbulence
- poor weather can reduce visibility

Effects MUST be bounded and playable. V1 is not trying to implement a professional flight simulator.

Gameplay-affecting aviation weather state SHOULD be server-authoritative.

---

# 11. Ground weather radar

Ground weather radar is a hard V1 requirement.

A functioning radar installation MUST be represented physically in the world and require, at minimum:

- radar dish / antenna
- radar controller
- power connection
- data/network connection
- physical radar display block

A floating dish with no meaningful infrastructure MUST NOT function simply because it exists.

## 11.1 Radar height

Antenna height MUST matter in V1.

Higher, well-sited radar installations MUST have a meaningful coverage advantage over poorly sited low installations, subject to equipment limits.

## 11.2 Terrain obstruction

Terrain masking / line-of-sight MUST matter at least approximately.

The implementation MAY use coarse cached terrain-horizon data rather than expensive exact per-block ray tracing.

## 11.3 Radar range

Effective radar range SHOULD be limited by a combination of:

- equipment/tier maximum range
- antenna height / effective horizon
- terrain obstruction
- server performance/configuration limits

## 11.4 Radar products

At minimum, V1 radar MUST display actual relevant Project Atmosphere weather information such as precipitation/storm intensity.

It MUST NOT simply render decorative random weather blobs unrelated to the real weather simulation.

## 11.5 Physical display

The radar screen MUST exist as a rendered physical world block.

A GUI MAY exist for setup/configuration, but the physical display is part of the V1 experience.

## 11.6 Radar tiers

V1 MAY include simple tiers or a single functional tier initially.

Perfect tier progression, recipes, and cost balance are not V1 requirements.

---

# 12. Aircraft weather radar

At least one supported aircraft SHOULD be able to use a weather-radar instrument in V1.

Aircraft radar MUST use the same real atmospheric data model as ground radar.

The exact crafting cost, upgrade progression, range balance, and instrument tiering may remain preliminary.

---

# 13. Persistent strategic world simulation

A living strategic world outside loaded chunks is a hard V1 requirement.

V1 MUST maintain lightweight persistent server-side records for selected distant populations rather than keeping all corresponding entities loaded.

Strategic group records MUST be capable of representing at least:

- group identity
- type/faction
- source identity
- approximate composition/strength
- strategic position
- destination/objective
- route or route representation
- effective movement speed
- state
- last simulation time

Distant groups MUST continue to advance using elapsed/coarse simulation while their chunks are unloaded.

They MUST NOT simply teleport to the player when an attack timer expires.

---

# 14. Hostile sources

V1 MUST include persistent hostile source locations in the generated world.

Possible source types include:

- camps
- forts
- occupied ruins
- towns
- cities
- other intentionally selected hostile structures

A source MUST have persistent server-side identity/state independent of one ordinary mob-spawner block.

A source MUST be able to launch persistent strategic groups toward appropriate objectives.

At least one clear player-understandable method for permanently neutralizing a source MUST exist.

Once legitimately cleared, that source MUST remain cleared across:

- chunk unloads
- player logout
- server restart

A cleared source MUST stop, or dramatically reduce according to an explicit design rule, its future strategic force generation.

---

# 15. Hostile group variety

V1 MUST NOT hard-code the strategic world solely around one zombie horde type.

The architecture MUST support multiple strategic hostile categories/factions.

The V1 content set SHOULD include more than one meaningful hostile composition where practical, for example some combination of:

- zombie/undead hordes
- pillager/raider forces
- other compatible hostile mobs
- specialized siege-capable units

The exact difficulty and frequency distribution may remain conservative/default for V1.

---

# 16. Strategic movement and ETA

Strategic forces MUST move through unloaded geography over time.

V1 movement SHOULD account for coarse terrain/route cost rather than Euclidean teleportation.

The strategic path representation MAY operate at chunk or larger-region resolution.

The simulation SHOULD be capable of accounting for broad categories such as:

- mountains/slope
- water
- roads
- bridges
- passable/impassable regions

V1 MUST expose an admin/debug ETA or equivalent inspection mechanism so strategic movement can be tested and explained.

The travel time of a force reaching a settlement SHOULD depend substantially on where the nearest relevant intact source actually is.

---

# 17. Materialization and dematerialization

When players approach a strategic group, V1 MUST materialize that strategic group into ordinary Minecraft entities.

Materialization MUST be idempotent and resistant to duplication exploits.

Entities belonging to a materialized strategic encounter MUST retain enough identity to reconcile back to the strategic record.

Deaths/casualties MUST reduce the strategic group's future strength.

If the encounter unloads, surviving entities MAY be summarized back into strategic state.

Unloading/reloading MUST NOT reset an army to its original strength.

The system MUST handle server restarts without duplicating or restoring destroyed groups.

---

# 18. Large hordes and armies

V1 MUST support convincingly large strategic hostile forces.

The strategic force size MUST NOT require every represented mob to remain physically loaded at all times.

If performance requires it, a large army MAY materialize in controlled waves or bounded active populations as long as:

- total strategic strength remains persistent;
- casualties remain persistent;
- the encounter still feels like one large force;
- unloading does not erase progress.

---

# 19. Siege behavior

Siege behavior is a hard V1 requirement because defensive architecture is a core gameplay pillar.

## 19.1 Path first

Hostile forces MUST attempt viable normal navigation before structural breaching.

They SHOULD prefer meaningful routes such as:

- open entrances
- roads
- bridges
- gates
- doors where appropriate
- navigable terrain/stairs

## 19.2 Breach only when required

Only explicitly siege-capable mobs/units SHOULD receive meaningful structural breach abilities.

Breaching SHOULD occur only when the planner determines that no reasonable route exists, or the available route exceeds an explicit cost threshold.

## 19.3 Structural targeting

V1 breach planning MUST target blocks that plausibly open a route to the objective.

It MUST NOT use indiscriminate nearest-block destruction.

A decorative statue that is near an attacking mob but not part of a useful breach corridor SHOULD remain untouched.

## 19.4 Breach rules

V1 SHOULD support:

- block hardness / breach time
- protected/unbreakable tags
- preference for doors/gates/weaker barriers when sensible
- constrained breach corridors
- rate-limited structural damage

## 19.5 Castle value

A V1 fortress MUST gain practical defensive value from design choices such as:

- walls
- gates
- chokepoints
- elevation
- bridges
- trenches
- fallback positions
- traps/weapons/explosives available through the pack

The system should make fortification useful without making decorative building unsafe.

---

# 20. Normal local mobs, farms, and spawners

The strategic system MUST be additive rather than a replacement for ordinary Minecraft spawning.

V1 MUST preserve ordinary local hostile spawning sufficiently to retain:

- caves
- nighttime danger
- ordinary exploration encounters
- conventional mob farms

Strategic sources MUST NOT require destroying every ordinary vanilla/modded spawner mechanic.

Players MAY preserve/use ordinary spawners without that preventing them from permanently clearing a strategic hostile source.

---

# 21. Animal herds and peaceful strategic populations

Strategic animal herds are a V1 requirement.

Distant herds SHOULD be represented using lightweight strategic state rather than thousands of always-loaded entities.

A V1 herd record SHOULD support:

- species/type
- approximate count
- strategic location / center
- movement/home range
- last simulation time

When players approach, herds SHOULD materialize into normal compatible animal entities.

When safely distant again, they MAY be summarized back into strategic state.

Exact ecology, reproduction rates, migration realism, and species balance are not V1 requirements.

---

# 22. DrewCraft launcher

A one-click friend-facing launcher is a hard V1 requirement.

The public-facing experience MUST be approximately:

1. open the DrewCraft page;
2. click **Download for Windows**, **Download for Mac**, or **Download for Linux**;
3. install/run DrewCraft;
4. sign into Microsoft/Minecraft through the normal Prism flow if required;
5. click Play.

Friends MUST NOT be required to manually install or manage:

- Java
- NeoForge
- mod jars
- library dependencies
- configs
- pack updates

The launcher MUST:

- identify platform/architecture
- install or locate a managed compatible Java 21 runtime
- install/manage Prism or the final chosen launch engine
- create/manage the DrewCraft instance
- read the release manifest
- download exact required content
- verify hashes
- repair missing/modified pack-managed files
- perform staged/atomic updates
- preserve user-owned data appropriately
- check server pack/protocol compatibility before launch where possible
- present useful errors instead of raw technical failure messages

Microsoft account authentication SHOULD remain delegated to Prism rather than being reimplemented by DrewCraft.

---

# 23. Windows, macOS, and Linux support

V1 MUST support:

- Windows x86-64
- Apple Silicon macOS
- Ubuntu/Linux x86-64

A polished macOS V1 SHOULD be packaged as a normal `.app`/installer experience and SHOULD avoid requiring friends to disable Gatekeeper.

Intel Mac support is desirable but not a hard blocker unless it remains straightforward to provide.

---

# 24. DrewCraft download website

V1 MUST provide the intentionally simple DrewCraft download page.

The friend-facing page SHOULD remain minimal:

- DrewCraft name
- one short description
- **Download for Windows**
- **Download for Mac**
- **Download for Linux**

It SHOULD NOT become a complicated mod-installation tutorial.

Download buttons SHOULD point at the latest validated platform release artifacts.

---

# 25. Client/server release synchronization

V1 MUST make client/server mod mismatch difficult to create accidentally.

Required behavior:

- one canonical DrewCraft release/version manifest
- matching client/server artifacts
- server exposes safe version/readiness information
- launcher compares local pack version/protocol with the server
- stale clients are updated/repaired before normal launch/join
- an updating or incompatible server produces a useful message

Friends SHOULD NOT discover incompatibility only after Minecraft shows a long mod mismatch error.

---

# 26. Server deployment and updates

V1 MUST include reproducible dedicated-server deployment.

Required operational capabilities:

- server install from generated release artifact
- hash verification
- system service / reliable startup
- graceful stop
- staged server updates
- backup before update
- controlled restart
- post-start health/version check
- recovery path if application update fails

World-data migrations MUST be handled explicitly and MUST NOT be blindly rolled backward along with application files.

---

# 27. Hosting

Oracle Ampere A1 ARM remains the preferred low-cost initial hosting target, but **Oracle is not itself a V1 product requirement**.

V1 requires that the complete server be deployable reproducibly to a suitable Linux host.

The Oracle target MUST be benchmarked honestly on ARM64 with the complete stack.

If the complete V1 experience cannot run acceptably on the available free A1 shape, the project SHOULD move to a deliberately selected larger/alternate host rather than removing defining gameplay systems merely to fit the host.

Automatic cloud scaling that can silently create charges MUST NOT be part of V1.

---

# 28. Backups and persistence

V1 MUST back up all state required to restore the world correctly, including:

- world region/data files
- player data
- DrewCraft strategic SavedData/database
- hostile-source state
- relevant mod-specific world data
- required server configuration
- DrewCraft pack/version identity

Backups MUST exist independently of the live server VM/storage at some reasonable cadence.

At least one restore test MUST be successfully performed before V1 is considered production-ready.

---

# 29. Administration and observability

Because many DrewCraft systems operate while chunks are unloaded, V1 MUST provide admin/debug visibility.

At minimum, the custom mod SHOULD expose commands or equivalent diagnostics for:

- DrewCraft version/protocol
- weather sample at a position
- radar state/connectivity
- strategic group list
- strategic group state/position
- strategic ETA
- hostile source list/state
- siege planner state
- subsystem/performance diagnostics

Major custom systems SHOULD have server-side feature flags so a malfunctioning subsystem can be temporarily disabled without making the entire server unusable.

---

# 30. Performance requirements

V1 does not require infinite scale, but it MUST be designed around bounded server cost.

The implementation MUST avoid:

- ticking distant strategic mobs as real entities
- full-world per-tick scans
- full-resolution entity pathfinding over unloaded chunks
- recalculating the same radar scan independently for every display
- unconstrained simultaneous siege planners
- duplicating Project Atmosphere with a second expensive global weather simulation

V1 SHOULD use:

- coarse elapsed-time strategic simulation
- cached terrain/radar data
- bounded materialization radii
- bounded active army entity counts when needed
- cached siege plans
- explicit performance limits/configuration

---

# 31. V1 testing requirements

Before V1 release, the project MUST demonstrate at least the following end-to-end tests.

## Installation / release

- clean Windows install from DrewCraft download page
- clean Apple Silicon macOS install from DrewCraft download page
- clean Ubuntu/Linux x86-64 install from DrewCraft download page
- Java provisioned automatically
- Prism/instance provisioned automatically
- successful Minecraft authentication flow
- successful connection to the server
- automatic update from an older DrewCraft release
- repair of a deliberately deleted/corrupted pack-managed file
- stale client prevented from silently joining an incompatible server

## World

- production pre-generated world restored to a clean server
- Terrain Diffusion world loads reliably
- Distant Horizons works on supported clients
- normal Nether and End function

## Base mods

- representative Create contraption works
- Create train works
- supported car/truck works
- supported aircraft works
- Project Atmosphere weather behaves correctly
- Simple Clouds renders correctly alongside the client stack

## Aviation/weather

- aircraft experiences wind
- crosswind/headwind/tailwind behavior is observable
- turbulence occurs under intended conditions
- mountain/terrain contribution is observable
- bad weather/visibility matters

## Radar

- radar requires valid infrastructure/connectivity
- physical screen renders real current weather
- higher/better-sited radar demonstrates increased useful coverage
- terrain masking is observable
- multiple displays can share a controller without duplicating scan cost excessively
- aircraft radar works if included in the final V1 instrument set

## Strategic hostile world

- intact hostile source launches a strategic group
- group advances while relevant chunks are unloaded
- ETA/position diagnostics update consistently
- approaching group materializes exactly once
- casualties persist
- unloading does not reset the force
- server restart does not reset or duplicate the force
- source can be explicitly cleared
- cleared source remains cleared after restart
- cleared source no longer produces normal future strategic forces

## Siege

- open route causes pathing rather than wall destruction
- accessible gate/entrance is preferred over arbitrary breaching where appropriate
- sealed defended location can trigger a planned breach
- breach targets a meaningful structural corridor
- unrelated decorative blocks are not randomly selected
- breach creates an actually useful navigable route

## Herds

- distant herd exists as strategic state
- approaching herd materializes
- herd can unload/summarize without obvious duplication

## Persistence / operations

- backup captures strategic state as well as world blocks
- restore returns the server to a coherent state
- server update flow preserves world and custom persistence
- one representative multi-player performance test remains within an acceptable gameplay envelope

---

# 32. Explicitly NOT required for V1

The following are **post-V1 balance/polish work unless a severe problem makes one necessary to preserve the core experience**:

- broad vanilla recipe rewrites
- broad Create recipe rewrites
- carefully engineered car/truck crafting costs
- carefully engineered aircraft crafting costs
- perfect fuel economy
- perfect train economics
- a fully designed transport tech tree
- elaborate radar crafting progression
- perfectly tuned radar tier costs
- precise hostile-city density balance
- polished army difficulty curves
- carefully tuned reinforcement rates
- perfect raid frequency
- complete weapon-vs-army balance
- detailed animal ecology/reproduction balance
- hardcore hunger/thirst/body-temperature systems
- large quest/progression systems
- extra dimensions
- cosmetic feature expansion unrelated to the core pillars

Custom DrewCraft blocks MUST still have functional recipes where crafting is required, but those recipes may be simple and provisional in V1.

Basic safety/default tuning is still required. For example, V1 cannot ship with armies spawning continuously or radar consuming zero resources if that makes the system unusable. The distinction is that V1 needs **sane defaults**, not a comprehensive economy/difficulty design.

---

# 33. V1 balance philosophy

For V1:

- preserve upstream recipes/configuration wherever reasonable;
- modify only what is necessary for compatibility, functionality, safety, or preservation of a core DrewCraft design pillar;
- avoid speculative balance work before real multiplayer playtesting;
- collect actual observations from friends after V1;
- use V1.1+ for deliberate recipe, progression, economy, frequency, and difficulty tuning.

The correct question before a V1 balance change is:

> **Does this need to change for DrewCraft to function as intended, or are we merely guessing what will eventually feel balanced?**

If it is the latter, defer it.

---

# 34. Scope freeze rule

Once this V1 requirements document is accepted, new major gameplay concepts SHOULD NOT be added to the V1 critical path unless they are required to:

- make one of the systems above function;
- bridge two existing V1 systems correctly;
- fix a stability/performance/security problem;
- prevent a core design pillar from being trivially bypassed.

Interesting new ideas should normally become V1.x or V2 work.

This rule exists so DrewCraft actually becomes playable rather than remaining an indefinitely expanding design document.

---

# 35. Definition of DrewCraft V1 complete

DrewCraft V1 is complete when the following statement is true:

> A non-technical friend can click the correct DrewCraft download button, install and launch the exact supported pack, join the production server, explore a massive Terrain Diffusion world using normal Minecraft/Create/vehicle systems, see and react to real moving weather, fly an aircraft affected by that weather, build and use physically meaningful radar infrastructure, encounter distant animal herds and hostile forces whose state persists outside loaded chunks, be attacked by armies that genuinely traveled from persistent hostile sources, defend a castle whose architecture affects the siege, permanently clear those hostile sources, log out and return later without the strategic world resetting, and receive future DrewCraft updates without manually managing the modpack.

If that statement is true and the system is stable enough for normal friend-group play, it is V1.

Perfect recipes, progression, economy, and difficulty are intentionally **not** part of that definition.
