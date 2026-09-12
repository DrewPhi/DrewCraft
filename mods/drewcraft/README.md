# DrewCraft integration mod

This module is the single NeoForge integration/custom-gameplay mod for DrewCraft.

## Platform

- Minecraft 1.21.1
- NeoForge 21.1.250
- Java 21
- Mod ID: `drewcraft`

Core DrewCraft code is upstream-independent. Third-party systems enter through isolated adapter packages, and moving upstream source branches are never treated as substitutes for the exact verified artifacts selected by the pack resolver.

## Implemented foundation

The integration platform currently provides:

- server configuration and feature flags;
- `/drewcraft status` admin diagnostics;
- `/drewcraft state touch` as a minimal persistence smoke surface;
- `/drewcraft env sample` as the first environment vertical slice;
- protocol compatibility boundary (`DrewCraftProtocol`);
- versioned Minecraft `SavedData` foundation (`DrewCraftSavedData`);
- DrewCraft-owned `TerrainService`, `WeatherService`, `PowerService`, and `VehicleService` contracts;
- Terrain Diffusion Plus realized-world terrain adapter;
- Project Atmosphere read-only public-API adapter;
- focused JUnit tests and cheap compile/unit-test CI with no Minecraft world boot.

The Terrain Diffusion and Project Atmosphere flags default to `true` because their initial adapters exist and fail closed. Create, MTS, strategic-world and radar flags remain `false` until those milestones are implemented.

## Environment contract

`TerrainDiffusionTerrainService` samples only already-loaded, already-realized server terrain. It never force-loads an unloaded chunk and never calls Terrain Diffusion Plus neural inference. This is a hard performance boundary for future aviation, radar and strategic consumers.

`ProjectAtmosphereWeatherService` queries the upstream read-only `AtmoApi` surface and translates its `WeatherSnapshot` into immutable DrewCraft data. Current public fields are cloud cover, rain intensity, temperature in Celsius, wind speed in m/s, wind angle in radians, storming, and snowing.

The DrewCraft weather contract also reserves optional values for pressure, humidity, visibility in metres, and normalized severity. Project Atmosphere's current public snapshot does not expose those values, so they remain unavailable rather than being guessed or read from internal implementation state.

The Atmosphere adapter uses a fail-closed reflection boundary because the selected `0.9.1.2` provider artifact does not have an exact matching Git tag; a changed API shape yields an unavailable sample rather than leaking moving branch types into core DrewCraft code.

Run `/drewcraft env sample` as an operator to inspect the composed terrain/weather state at the command source position.

## Build

CI pins Gradle 9.2.1. With Java 21 and Gradle available locally:

```bash
gradle -p mods/drewcraft test build --no-daemon
```

The JUnit source set reuses the main Minecraft/NeoForge classpath so adapter tests can use vanilla value types without launching Minecraft.

Do not add the expensive full-pack Terrain Diffusion Plus smoke boot to this module's ordinary CI. The certified base-stack smoke is a separate gate.

## Package direction

```text
dev.drewcraft
├── service                         # DrewCraft-owned contracts/snapshots only
│   ├── terrain
│   ├── weather
│   ├── power
│   └── vehicle
├── adapter
│   ├── terrain                     # Terrain Diffusion Plus boundary
│   ├── atmosphere                  # Project Atmosphere boundary
│   ├── create                      # next: Create kinetic boundary
│   └── mts                         # next: MTS observation/physics boundary
├── environment                     # later composition/cache policy
├── radar
├── aviation
└── strategic
```

Integration preference is always: public API/event -> isolated adapter -> narrow accessor/mixin -> maintained fork only as a last resort and only when licensing permits.

See `docs/INTEGRATION_SURFACE_AUDIT.md` and `docs/V1_EXECUTION_STATUS.md` before adding or changing an upstream dependency.
