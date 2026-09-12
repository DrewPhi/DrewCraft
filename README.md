# ServerMc

ServerMc is a deliberately integrated, realism-oriented Minecraft survival server built around **geographic scale, infrastructure, weather, transportation, and a living strategic world**.

This is not intended to become a kitchen-sink modpack. The goal is a coherent game where distance matters, players build infrastructure because it is useful, weather matters to travel, aircraft are a late-game capability rather than a toy, hostile populations exist at world scale rather than only inside the simulation distance, and joining the server is effectively one click for non-technical friends on Windows or macOS.

## Project status

**Design/specification phase.** The repository is currently being established as the canonical source of truth for the pack, custom integration code, launcher, server configuration, deployment, and release process.

Target baseline:

- Minecraft **1.21.1**
- **NeoForge**
- **Java 21**
- Windows x86-64 clients
- macOS Intel and Apple Silicon clients
- Linux ARM64 server as the first hosting target

The exact mod lockfile is not considered stable until the full stack passes compatibility and multiplayer tests.

## Design pillars

### 1. Geography should matter

The overworld is intentionally huge and geographically legible. Terrain Diffusion Plus provides large, realistic landforms, climate-driven biomes, rivers, mountains, and long-distance geography. We intend to use **World Scale 2**, a bounded/pre-generated playable region, and Distant Horizons so mountains, storms, settlements, and infrastructure can be perceived at meaningful distances.

There should be no routine teleportation system such as Waystones. Distance is a game mechanic.

### 2. Transportation should be progression

Travel should evolve roughly from:

**walking / horses / boats → roads and cars → rail and large infrastructure → ships → late-game aircraft**

Create supplies the industrial and infrastructure layer. Immersive Vehicles supplies realistic cars and aircraft. Large-ship solutions are compatibility-gated rather than assumed. Aircraft must be sufficiently expensive and infrastructure-dependent that airports, fuel, navigation, weather awareness, and long-distance routes remain meaningful.

The Nether must not erase this progression. Portal distance scaling will be tuned if necessary so the Nether remains useful without making overworld roads, rail, ships, and aircraft pointless.

### 3. Weather should be a system, not an effect

Project Atmosphere + Simple Clouds are the weather baseline. Weather should form, move, and be visible from a distance. Wind, precipitation, visibility, storms, terrain, season, and elevation should matter.

The custom ServerMc integration mod will bridge weather into transportation gameplay: wind and turbulence should affect aircraft, mountainous terrain should influence turbulence/weather where feasible, and players should be able to build functional weather-radar infrastructure.

### 4. Radar should be physical infrastructure

Radar is not just a minimap overlay.

Ground radar should consist of real world blocks: a dish/antenna, power/data connection, radar controller, and **physical display blocks**. Better tiers provide longer range. Antenna height matters through terrain line-of-sight and an effective radar-horizon model, encouraging towers and mountaintop sites. A dish placed unrealistically in the sky without power/data infrastructure should not work.

Aircraft can equip weather-radar instruments connected to the same atmospheric data model.

### 5. The world should continue to exist outside loaded chunks

Strategic populations are a core custom feature.

Generated hostile camps, forts, towns, ruins, and cities can act as persistent sources of hostile populations. Those populations can form patrols, hordes, raiding parties, and armies and move across the strategic world even while their chunks are unloaded. Their travel time is based on distance, terrain/route cost, and unit speed rather than teleportation.

When a strategic group approaches loaded terrain, it materializes into normal Minecraft entities. When it leaves active simulation range, it can collapse back into a persistent strategic representation.

Destroying or clearing a hostile source should permanently reduce that source's ability to send future forces. This gives exploration and conquest a persistent purpose.

### 6. Sieges should reward real defenses without griefing builds randomly

Hostile armies should try to **pathfind first**. They should use gates, roads, bridges, doors, and accessible paths when possible.

Only when no viable route exists should selected siege-capable mobs breach blocks. Breaching should target structural barriers needed to reach a goal, not decorative statues or arbitrary nearby blocks. Defensive walls, gates, chokepoints, elevation, bridges, traps, weapons, and explosives should therefore matter.

### 7. Vanilla-scale ecology and farms should still work

The strategic simulation is additive, not a replacement for all normal spawning.

Normal local hostile spawning remains available (with tuned caps/rules as needed), preserving night danger, caves, conventional farms, and ordinary Minecraft systems. Strategic armies/hordes are a separate macro-scale layer. Animal herds can also be represented strategically so the larger world feels populated without keeping thousands of entities loaded.

### 8. Joining should be almost impossible to mess up

Friends should not manually install Java, NeoForge, mods, configs, or updates.

The friend-facing product is a small ServerMc bootstrapper/launcher with Windows and macOS downloads. It manages a Prism Launcher instance underneath, obtains the correct Java 21 runtime, installs the exact pack version, verifies hashes, updates changed files, checks server compatibility/readiness, and then launches Minecraft.

Microsoft authentication remains the normal one-time Prism/Minecraft login step.

## Initial mod baseline

Required or strongly preferred baseline components:

- **Terrain Diffusion Plus** — world generation; World Scale 2 target
- **Chunky** — offline/pre-release world pre-generation
- **Distant Horizons** — large-scale visual horizon
- **Create** — industry, mechanical infrastructure, construction, trains
- **Immersive Vehicles (MTS)** — realistic cars and aircraft, with curated content packs
- **Project Atmosphere** — dynamic climate/weather
- **Simple Clouds** — cloud simulation/rendering used by Project Atmosphere
- **Serene Seasons** — seasonal integration where compatible
- Required library dependencies such as **Gabou's Libs** where dictated by the weather stack

Compatibility-gated candidates, not promises:

- a Create-compatible/player-buildable large-ship solution
- restrained navigation/map tooling
- selected animal-herding/ecology enhancements
- selected local horde/spawn-control mods where they complement rather than duplicate ServerMc's strategic simulation

Explicitly avoid by default:

- Waystones/routine teleportation
- giant structure packs that make the world feel saturated
- extra dimensions without a strong design reason
- redundant tech trees
- survival-overhaul clutter unrelated to the core experience
- mods that trivialize cars, trains, ships, aircraft, weather, or geography

See [`docs/MOD_STACK.md`](docs/MOD_STACK.md) for dependency and compatibility policy.

## Custom code we expect to own

A single NeoForge integration mod, tentatively `servermc`, should contain internal modules for:

- Terrain Diffusion ↔ atmospheric climate/elevation integration
- Project Atmosphere ↔ Immersive Vehicles wind effects
- terrain-induced turbulence / aviation weather
- ground weather radar
- aircraft weather-radar instruments
- physical radar displays and power/data-network rules
- persistent strategic world populations
- hostile structure/source lifecycle
- unloaded-chunk strategic movement and ETAs
- materialization/dematerialization of strategic groups
- siege planning and constrained block breaching
- local-spawn coexistence rules
- progression/config integration and server-authoritative state
- compatibility adapters for the curated mod stack

See [`docs/SYSTEMS.md`](docs/SYSTEMS.md).

## Repository responsibilities

This repository should ultimately contain **everything required to reproduce a client and server release except third-party binaries that cannot or should not be redistributed and the enormous generated world data itself**.

Planned shape:

```text
ServerMc/
├── README.md
├── AGENTS.md
├── docs/
├── pack/
│   ├── manifest/
│   ├── common/
│   ├── client/
│   ├── server/
│   └── overrides/
├── mods/
│   └── servermc/
├── launcher/
├── server/
├── infra/
├── tools/
├── tests/
└── .github/workflows/
```

The pack is split conceptually into **common**, **client-only**, and **server-only** inputs. Releases are generated from manifests and checksums; they are not maintained by asking friends to copy arbitrary folders around.

Large artifacts belong in GitHub Releases, object storage, or server storage—not Git history.

See [`docs/REPO_ARCHITECTURE.md`](docs/REPO_ARCHITECTURE.md).

## Launcher and release model

The canonical release flow is:

1. Pin Minecraft, NeoForge, every mod, every content pack, and config revision in the repository.
2. CI validates dependency/version consistency and builds the custom `servermc` mod.
3. CI produces common/client/server packs and a versioned manifest containing hashes.
4. GitHub Release publishes pack artifacts and platform launcher installers.
5. The server updater installs the matching server pack during a controlled restart.
6. A player's ServerMc launcher reads the release manifest, downloads only missing/changed content, verifies it, ensures Java/Prism are usable, verifies the server is on the compatible pack version, and launches.

A player should not be able to accidentally join with a stale mod set.

See [`docs/LAUNCHER_HOSTING.md`](docs/LAUNCHER_HOSTING.md).

## Hosting target

The first hosting target is **Oracle Cloud Ampere A1 ARM** because Java runs well on ARM and the cost target is extremely low.

As of September 2026, Oracle's current Free Tier documentation states a total Always Free Ampere allowance of **2 OCPUs / 12 GB RAM**. Older 4 OCPU / 24 GB guidance must not be assumed. This is a performance target to benchmark, not a guarantee that the full pack will fit comfortably.

Key server strategy:

- pre-generate the Terrain Diffusion world on suitable hardware before deployment
- upload the bounded world to the server
- avoid expensive live terrain inference/generation during normal play
- benchmark the complete stack on ARM64 before declaring Oracle Free Tier production-ready
- keep the server shape fixed; do not silently autoscale into paid resources
- preserve backups outside the VM
- treat billing alerts as alerts, not as the only protection against spend

If 2 OCPU / 12 GB is insufficient, the next step is an explicit, manually approved larger paid shape or alternate host—not invisible autoscaling.

## Documentation

- [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md) — complete gameplay/product specification
- [`docs/SYSTEMS.md`](docs/SYSTEMS.md) — custom system design
- [`docs/MOD_STACK.md`](docs/MOD_STACK.md) — mod policy and compatibility matrix
- [`docs/REPO_ARCHITECTURE.md`](docs/REPO_ARCHITECTURE.md) — target monorepo layout and artifact boundaries
- [`docs/LAUNCHER_HOSTING.md`](docs/LAUNCHER_HOSTING.md) — install/update/server/deployment architecture
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — implementation order and release gates

## Definition of success

A successful ServerMc release should feel like one coherent game:

- a friend downloads one installer and can play without understanding modding
- everyone always launches the same tested pack version
- the world is large enough that geography and weather are strategically meaningful
- cars, trains, ships, roads, bridges, airports, radar towers, and defenses all have practical reasons to exist
- storms can be seen and tracked before they arrive
- flying in poor weather is meaningfully harder than flying in clear conditions
- a distant hostile settlement can send an army that genuinely travels toward the players over time
- destroying that settlement changes the long-term strategic world
- a well-designed castle works because of its layout, not because mobs are simply forbidden to interact with it
- normal Minecraft caves, spawning, farms, building, exploration, and emergent play remain intact underneath the larger simulation

That is the standard against which every dependency and custom feature should be judged.
