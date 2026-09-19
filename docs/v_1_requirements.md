# DrewCraft V1 Requirements

**Scope frozen:** 2026-09-16
**Shipping profile:** `v1_survival_exploration`

## Product goal

DrewCraft V1 is a reliable multiplayer survival pack that is fun before any custom endgame exists. Its identity is a beautiful, geographically large Terrain Diffusion world explored with conventional vehicles and aircraft, Create engineering, and selected dungeon adventures.

V1 prioritizes seamless installation, reliable launching, server/client parity, and normal survival Minecraft over custom simulation breadth.

## Required gameplay

- Minecraft 1.21.1, NeoForge 21.1.250, and Java 21.
- Terrain Diffusion Plus owns overworld terrain and caves.
- Distant Horizons provides long-distance terrain presentation.
- JEI provides item and recipe lookup, with server-side recipe synchronization.
- Chunky is available for controlled offline/admin pregeneration; it must not silently generate the live world.
- Normal survival, vanilla structures and villages, mobs, farms, redstone, and multiplayer remain intact.
- Immersive Vehicles/MTS plus the official content pack provide practical cars, trucks, and aircraft.
- Create provides machinery, logistics, factories, and trains.
- The compatible selected Create family is included: Create Big Cannons, Create: Gunsmithing, Create Aeronautics, Create High Seas, and Create: Radars.
- When Dungeons Arise provides its complete upstream default set of explorable structures with its intended generation, mobs, and loot.
- The conservative, verified performance suite is included. Embeddium and ScalableLux remain excluded because of the selected Aeronautics/Sable compatibility constraints.

## Required friend experience

- One download button for each supported target: Windows x86-64, Apple Silicon macOS, and Ubuntu/Linux x86-64.
- One DrewCraft launch starts the game. Prism may remain an implementation detail for Microsoft authentication, but the player must not need to open the instance manually after signing in.
- Downloads and updates show progress, transfer rate, and an ETA when enough data exists.
- Java, Prism, the instance, mods, configs, and release state are installed, repaired, and updated automatically.
- Client and server are built from the same immutable release manifest and the same V1 profile.
- Failed staging or verification reports the exact file and preserves the last working installation.

## Required server and release behavior

- The server boots a fresh V1 world, stops cleanly, and restarts the same world.
- An exact release contains the NeoForge runtime and the verified server tree; world and logs remain persistent outside immutable application releases.
- Updates stage and hash-verify before activation, create a backup, switch atomically, health-check, and roll the application back on failure without blindly rolling back the world.
- The initial benchmark target remains OCI Ampere A1, 2 OCPU and 12 GB RAM. A larger host is a measured migration decision, not an assumption.
- A representative multiplayer smoke session proves terrain exploration, a vehicle, an aircraft, basic Create machinery/train behavior, and at least one enabled WDA dungeon.

## Explicitly deferred

The following are not V1 requirements and must not block the first fun-with-friends release:

- Project Atmosphere, Simple Clouds, seasons, and weather-driven flight;
- DrewCraft weather/terrain coupling for Create: Radars;
- custom hostile sources, Source Cores, factions, armies, unloaded marches, and reinforcements;
- custom sieges, strategic herds, Covenant endgame, and custom invasion progression;
- production-scale custom endgame structures or bombing objectives;
- broad progression, recipe, economy, fuel, and balance redesign.

Completed custom code is preserved behind disabled-by-default feature flags. The detailed designs live in `docs/FURTHER_IDEAS.md` and the archived system documents it links.

## Definition of V1 complete

V1 is complete when one exact `v1_survival_exploration` release:

1. passes resolver/hash checks and fresh-server/restart smoke tests;
2. installs and launches from the DrewCraft entry point on all three supported operating systems;
3. lets matching clients join the matching server without manual mod or instance work;
4. supports a stable multiplayer survival session featuring Diffusion terrain, vehicles/planes, Create, and a WDA dungeon;
5. passes update, repair, backup, and recovery checks with no V1-blocking defect.
