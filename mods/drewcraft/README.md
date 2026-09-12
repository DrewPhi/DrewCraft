# DrewCraft integration mod

This module is the single NeoForge integration/custom-gameplay mod for DrewCraft.

## Platform

- Minecraft 1.21.1
- NeoForge 21.1.250
- Java 21
- Mod ID: `drewcraft`

The module intentionally compiles without Terrain Diffusion Plus, Project Atmosphere, Create, or MTS on its classpath at this stage. Core DrewCraft code must remain upstream-independent; each third-party dependency will enter through an isolated adapter package and be compiled against the exact verified artifact selected by the pack resolver.

## Current scaffold

The initial platform provides:

- server configuration and feature flags;
- `/drewcraft status` admin diagnostics;
- `/drewcraft state touch` as a minimal persistence smoke surface;
- protocol compatibility boundary (`DrewCraftProtocol`);
- versioned Minecraft `SavedData` foundation (`DrewCraftSavedData`);
- JUnit tests for protocol compatibility;
- cheap compile/unit-test CI with no Minecraft world boot.

All integration and gameplay feature flags default to `false` until their adapters/features have their own acceptance evidence.

## Build

CI pins Gradle 9.2.1. With Java 21 and Gradle available locally:

```bash
gradle -p mods/drewcraft test build --no-daemon
```

Do not add the expensive full-pack Terrain Diffusion Plus smoke boot to this module's ordinary CI. The certified base-stack smoke is a separate gate.

## Package direction

Keep these layers distinct as implementation grows:

```text
dev.drewcraft
├── core / service contracts        # no third-party implementation types
├── integration
│   ├── terraindiffusion            # Terrain Diffusion Plus types stay here
│   ├── atmosphere                  # Project Atmosphere types stay here
│   ├── create                      # Create types stay here
│   └── mts                         # MTS types stay here
├── environment                     # composes terrain + weather contracts
├── radar
├── aviation
└── strategic
```

Integration preference is always: public API/event -> isolated adapter -> narrow accessor/mixin -> maintained fork only as a last resort and only when licensing permits.

See `docs/INTEGRATION_SURFACE_AUDIT.md` before adding an upstream dependency to this module.
