# ServerMc Mod Stack

This document defines how dependencies enter ServerMc and separates **baseline dependencies**, **compatibility-gated candidates**, and **functionality that belongs in the custom ServerMc mod**.

Do not turn this file into a wish list. Every dependency increases update risk, client burden, startup time, memory use, and multiplayer failure modes.

## 1. Platform lock

Current target:

- Minecraft: **1.21.1**
- Loader: **NeoForge**
- Java: **21**

This combination is intentional because the core stack now has 1.21.1 NeoForge support.

Verified during initial repository specification on 2026-09-12:

- Terrain Diffusion Plus: supports 1.21.1 NeoForge and recommends World Scale 2
- Immersive Vehicles: 1.21.1 NeoForge release exists
- Create: 1.21.1 NeoForge release exists
- Project Atmosphere: advertises 1.21.1 NeoForge support
- NeoForge 1.21.1 requires Java 21

Versions must still be pinned and tested together before the pack is called runnable.

## 2. Baseline dependencies

### Terrain Diffusion Plus

**Role:** overworld generator and large-scale geography.

Target configuration:

- World Scale 2
- bounded production world
- offline pre-generation using Chunky
- no assumption that the production server can cheaply generate new terrain under load

Important operational detail: Terrain Diffusion downloads multi-gigabyte model assets and performs neural inference. The live Oracle ARM server path therefore depends on pre-generation and explicit ARM/runtime testing.

Project: https://github.com/derekvawdrey/terrain-diffusion-plus

### Chunky

**Role:** controlled pre-generation of the playable world.

Chunky belongs in world-build/admin workflows, not in the player experience.

The exact release must match 1.21.1 NeoForge.

### Distant Horizons

**Role:** render the scale of Terrain Diffusion geography.

Must be tested carefully for:

- client memory/GPU impact
- multiplayer LOD behavior
- Apple Silicon
- interaction with Simple Clouds/weather rendering
- pack-default quality settings

It is fundamentally client-facing unless a chosen multiplayer configuration requires server support.

### Create

**Role:** primary technology/infrastructure layer.

Use for:

- mechanical industry
- logistics
- trains
- bridges/tunnels/construction
- infrastructure that makes large geography usable

ServerMc should integrate with Create rather than add a redundant all-purpose tech mod.

Verified current line during specification: Create 6.0.x for Minecraft 1.21.1 NeoForge.

Project: https://www.curseforge.com/minecraft/mc-mods/create

### Immersive Vehicles (MTS)

**Role:** realistic cars and aircraft.

Use a deliberately small set of curated content packs. Do not install every vehicle pack available.

Selection criteria:

- believable visual style
- progression-compatible speeds/capabilities
- stable 1.21.1 behavior
- useful cars/trucks/aircraft rather than novelty spam
- server/client licensing/distribution compatibility

Verified during specification: a Minecraft 1.21.1 NeoForge release exists.

Project: https://www.curseforge.com/minecraft/mc-mods/minecraft-transport-simulator

### Project Atmosphere

**Role:** dynamic climate/weather simulation.

This should be the source of truth for atmospheric state. ServerMc consumes/bridges its state rather than creating a second weather simulation.

Project: https://modrinth.com/mod/project-atmosphere

### Simple Clouds

**Role:** cloud simulation/rendering used by Project Atmosphere.

Test against Distant Horizons and the intended client graphics settings.

### Serene Seasons

**Role:** seasons where supported by Project Atmosphere and the final biome/world setup.

This is included because the weather stack explicitly supports it, not because ServerMc needs a broad farming overhaul.

### Required libraries

Install only libraries required by selected mods, for example Gabou's Libs if required by the locked Project Atmosphere version.

Libraries should be generated into the pack from the dependency manifest; friends should never locate them manually.

## 3. Compatibility-gated candidates

These are desired capabilities, not guaranteed dependencies.

### Large player-buildable ships

Goal: progression between small boats and aircraft, with meaningful ports/cargo.

Candidate must:

- support 1.21.1 NeoForge
- coexist with Create
- be stable in multiplayer
- not corrupt chunks/contraptions
- have acceptable performance
- support the desired realistic-ish style

Do not lock the pack to an unstable ship mod merely because the feature sounds good.

### Navigation/map tooling

A restrained map/navigation option may be useful because the world is huge.

Avoid:

- free teleportation
- omniscient hostile/player tracking
- features that remove navigation/weather/radar gameplay

Coordinates/maps are acceptable; bypassing travel is not.

### Herd/ecology helpers

Mods that improve nearby animal behavior may complement ServerMc's distant strategic herd simulation.

Candidates are only useful if they:

- support 1.21.1 NeoForge
- do not duplicate the persistent world simulation
- do not explode entity counts
- do not radically rewrite survival balance

### Local spawn/horde helpers

Spawn-control or local-horde mods may be useful as adapters for ordinary loaded-chunk behavior.

Examples previously considered conceptually include In Control!-style spawn tuning and horde behavior mods. They are **not baseline dependencies until compatibility is verified**.

ServerMc's strategic world simulation remains authoritative for unloaded macro-scale groups.

## 4. Features that should NOT be separate mods unless necessary

Prefer implementing these inside the single `servermc` integration mod:

- Terrain Diffusion climate/elevation bridge
- atmospheric wind → aircraft effects
- mountain/terrain turbulence
- weather-radar logic
- physical radar blocks/screens/network
- Create-compatible radar power adapter
- strategic populations
- hostile source lifecycle
- unloaded movement/ETA
- materialization/dematerialization
- siege planner
- constrained block breaching
- strategic/local spawn coexistence
- Nether portal-balance rule if needed

This keeps the defining gameplay systems versioned together and avoids dependency spaghetti.

## 5. Mods/categories intentionally excluded by default

### Waystones and routine teleportation

Conflicts directly with the large-world transportation design.

### Giant structure packs

A huge density of structures makes the world feel small and destroys the value of travel/discovery. Add individual structure content only when it has a clear purpose.

### Extra dimensions

Do not add dimensions simply because they exist. The Overworld is the project.

### Multiple giant technology mods

Create is the primary technology language. Add a second major tech system only if it solves a critical problem Create + ServerMc cannot solve cleanly.

### Unrelated survival difficulty overhauls

Hunger/thirst/body-temperature systems are not automatically more realistic in a useful way. Project Atmosphere temperature can matter where it supports weather/travel, but the server is not intended to become a micromanagement survival pack.

### Novelty vehicle packs

Vehicle content should match the project's visual/progression tone.

## 6. Dependency manifest policy

Never treat the `mods/` folder on one developer machine as the source of truth.

The repository should hold a machine-readable manifest containing for every dependency:

- canonical ID/name
- provider/source
- Minecraft version
- loader
- exact version
- expected SHA-256
- side: `common`, `client`, `server`
- required/optional
- redistribution policy
- download URL/API identifier where legally/technically appropriate
- notes/compatibility constraints

Example conceptual entry:

```yaml
- id: create
  side: common
  minecraft: 1.21.1
  loader: neoforge
  version: 6.0.10
  required: true
  sha256: TO_BE_LOCKED
  source: curseforge
```

Do not copy that example into production without obtaining and verifying the actual artifact/hash.

## 7. Redistribution policy

Many Minecraft mods have licenses or platform rules restricting redistribution.

Therefore the release builder must support both:

1. **redistributable artifacts** included in generated releases when permitted
2. **download-at-install artifacts** referenced by provider/version/hash when redistribution is not permitted

The launcher must verify the resulting file regardless of how it was obtained.

Never commit third-party mod jars to Git merely because they are convenient.

## 8. Common/client/server partition

Every dependency must be classified.

### Common

Required on both client and server, for example world/gameplay mods whose protocol/content must match.

### Client-only

Rendering/UI/performance utilities that the dedicated server should never load.

### Server-only

Administration, backup, profiling, or other dedicated-server tooling that should not be sent to players.

The release system generates separate client and server packs from these categories.

## 9. Update rules

No dependency update goes directly to production.

Required flow:

1. update manifest on a development branch
2. build the entire pack
3. run startup smoke test
4. run client/server connection test
5. test world load
6. test weather
7. test Create basics
8. test at least one vehicle
9. test custom ServerMc protocol
10. inspect logs for mixin/registry errors
11. only then publish a new pack version

World-generation dependency changes require extra caution because they may make newly generated terrain incompatible with the existing production world.

## 10. Versioning principle

The real version of the game friends play is **the ServerMc pack version**, not a list of individual mod versions.

Example:

```text
ServerMc 0.3.0
  Minecraft 1.21.1
  NeoForge <locked>
  Create <locked>
  Atmosphere <locked>
  ...
  servermc-mod 0.3.0
```

The launcher and server compare the ServerMc pack/protocol version before connection.
