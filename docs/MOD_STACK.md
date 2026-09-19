# DrewCraft Mod Stack

## Authoritative V1 profile

`v1_survival_exploration` is the only shipping profile.

### World and survival

- Terrain Diffusion Plus
- Chunky
- Distant Horizons
- Just Enough Items (JEI), on both client and server for recipe synchronization
- Xaero's Minimap (client-only)
- When Dungeons Arise with its complete upstream default structure set
- Vanilla survival systems and structures

### Vehicles and Create

- Immersive Vehicles / MTS
- MTS Official Pack
- Create
- Create Big Cannons
- Create: Gunsmithing
- Create Aeronautics
- Create High Seas
- Create: Radars as ordinary Create content
- Create: Gunsmithing firearm stack, including Sable, NTGL, GeckoLib, Player Animator, and Ritchie's Projectile Library
- required runtime libraries resolved transitively by the manifest

### Performance

The shipping profile selects ModernFix, FerriteCore, Lithium, ServerCore, Chunk Sending, AllTheLeaks, FastSuite, FastWorkbench, FastFurnace, Clumps, Connectivity, Spark, ImmediatelyFast, Entity Culling, and More Culling.

Embeddium and ScalableLux are not selected because the current Aeronautics/Sable stack declares incompatibilities. C2ME remains an isolated world-build experiment. New-client DH LOD radius defaults to 32; the launcher preserves user-edited graphics settings.

## Held out or deferred

- CBC Firepower Components: tested release hard-crashes with the selected Create: Radars release.
- Project Atmosphere, Simple Clouds, Serene Seasons, and their libraries: post-V1.
- DrewCraft-specific radar-height changes, weather returns, weather overlays, terrain masking, cockpit/airborne radar integration, and radar/weather coupling: post-V1. Native Create: Radars functionality remains enabled.
- Illager Invasion/Covenant content and tactical horde/herd candidates: post-V1 research.
- Additional terrain, weather, technology, vehicle, dungeon, and combat ecosystems: excluded unless a measured gap justifies them. The selected NTGL/Gunsmithing firearm stack is the V1 exception and is explicitly in scope above.
- UNU Parts/Vehicles, WarBorn Military Pack, and Golden Airport Pack (GAP): post-V1 compatibility/porting goals. They are expected to be port candidates because MTS packs are largely content archives, but their published Forge jars are not yet validated as drop-in 1.21.1 NeoForge artifacts.

## Dependency policy

Every selected artifact needs an exact provider identity, SHA-256, side classification, license/redistribution treatment, and client/server compatibility evidence. The release manifest references original-provider acquisition URLs where possible instead of rehosting third-party binaries.
