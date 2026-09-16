# DrewCraft

DrewCraft is a focused Minecraft 1.21.1 multiplayer survival experience built around a beautiful large-scale Diffusion world, vehicles and planes, Create engineering, and selected dungeon exploration.

## V1

The authoritative shipping profile is `v1_survival_exploration`:

- Terrain Diffusion Plus, Distant Horizons, and normal survival Minecraft;
- Immersive Vehicles/MTS with its official vehicle and aircraft pack;
- Create, Create Big Cannons, Create: Gunsmithing, Create Aeronautics, Create High Seas, and Create: Radars;
- When Dungeons Arise with only five approved dungeons enabled, retaining their normal mobs and loot;
- a conservative performance/diagnostic stack;
- one-click Windows, Apple Silicon macOS, and Ubuntu/Linux launchers;
- one immutable release manifest shared by clients and the server.

Weather, clouds, seasons, custom armies, sources, sieges, herds, radar/weather coupling, and a custom endgame are intentionally deferred until after V1. Existing implementations are preserved but disabled by default. See [Further Ideas](docs/FURTHER_IDEAS.md).

## Platform

- Minecraft 1.21.1
- NeoForge 21.1.250
- Java 21
- Windows x86-64, Apple Silicon macOS, and Ubuntu/Linux x86-64 clients
- Linux dedicated server; OCI Ampere A1 2 OCPU / 12 GB is the first benchmark target

## Friend experience

Friends download DrewCraft from the website, authenticate with Microsoft through the managed Prism runtime once, and then use DrewCraft to update and launch directly. Friends do not manually manage Java, NeoForge, Prism instances, mods, or configs.

Downloads are staged and hash-verified with visible progress, rate, and ETA. Client and server content is generated from the same exact profile and manifest.

## Repository map

- `pack/manifest/` — dependency registries and the shipping profile
- `mods/drewcraft/` — integration mod and preserved post-V1 systems
- `launcher/` — cross-platform installer/updater/launcher
- `infra/` — server deployment, health, update, and backup tooling
- `world/` and `tools/` — reproducible world/release tooling
- `site/` — download page
- `docs/` — requirements, status, operations, and future design archive

Start with [V1 Requirements](docs/v_1_requirements.md), [Current Breakpoint](docs/CURRENT_BREAKPOINT.md), and [V1 Execution Status](docs/V1_EXECUTION_STATUS.md).
