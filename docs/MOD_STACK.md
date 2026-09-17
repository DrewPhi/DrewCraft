# DrewCraft Mod Stack

## Authoritative V1 profile

`v1_survival_exploration` is the only shipping profile.

### World and survival

- Terrain Diffusion Plus
- Chunky
- Distant Horizons
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
- required runtime libraries resolved transitively by the manifest

### Performance

The shipping profile selects ModernFix, FerriteCore, Lithium, ServerCore, Chunk Sending, AllTheLeaks, FastSuite, FastWorkbench, FastFurnace, Clumps, Connectivity, Spark, ImmediatelyFast, Entity Culling, and More Culling.

Embeddium and ScalableLux are not selected because the current Aeronautics/Sable stack declares incompatibilities. C2ME remains an isolated world-build experiment.

## Held out or deferred

- CBC Firepower Components: tested release hard-crashes with the selected Create: Radars release.
- Project Atmosphere, Simple Clouds, Serene Seasons, and their libraries: post-V1.
- Illager Invasion/Covenant content and tactical horde/herd candidates: post-V1 research.
- Additional terrain, weather, technology, vehicle, dungeon, and combat ecosystems: excluded unless a measured gap justifies them.

## Dependency policy

Every selected artifact needs an exact provider identity, SHA-256, side classification, license/redistribution treatment, and client/server compatibility evidence. The release manifest references original-provider acquisition URLs where possible instead of rehosting third-party binaries.
