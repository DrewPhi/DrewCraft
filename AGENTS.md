# AGENTS.md — DrewCraft / ServerMc

This repository is the canonical source for the **DrewCraft** Minecraft server experience. `ServerMc` is the repository/internal project name; DrewCraft is the friend-facing product/server name.

Before making architectural changes, read:

1. `docs/PROJECT_SPEC.md`
2. `docs/SYSTEMS.md`
3. `docs/MOD_STACK.md`
4. `docs/REPO_ARCHITECTURE.md`
5. `docs/LAUNCHER_HOSTING.md`
6. `docs/ROADMAP.md`

## Non-negotiable design principles

- Minecraft target is 1.21.1 / NeoForge / Java 21 until an explicit migration decision is made.
- Geography must matter. Do not introduce routine teleportation or systems that make roads, rail, ships, aircraft, or weather irrelevant.
- Create is the primary infrastructure/technology language. Avoid redundant giant tech trees.
- Project Atmosphere is the atmospheric source of truth; bridge it rather than building another weather simulation.
- Strategic mobs outside loaded chunks are persistent lightweight records, not permanently loaded entities.
- Hostile source structures must be persistently clearable.
- Normal local Minecraft spawning/farms remain available; strategic spawning is additive.
- Siege mobs path normally first and breach only when needed.
- Siege block damage must be constrained to meaningful breach corridors; never implement indiscriminate nearest-block griefing.
- Radar is physical infrastructure with power/data connectivity and physical displays.
- Radar antenna height/terrain obstruction should matter.
- Friends must not manually manage Java, NeoForge, or mod folders.
- Client and server releases come from one locked manifest and must not drift.
- Do not commit the full generated world, third-party jars by default, Java runtimes, model weights, credentials, backups, or large caches to Git.
- Do not add automatic cloud autoscaling that can silently create charges.

## Development order

Follow `docs/ROADMAP.md`. In particular, prove mod compatibility, world pre-generation, ARM hosting, and launcher/release reproducibility before spending substantial effort on advanced strategic simulation.

## Custom mod architecture

Prefer one NeoForge integration mod with internal modules/adapters rather than many tiny mutually dependent custom mods.

Keep third-party integrations behind explicit adapters so upstream changes are localized.

Every major custom subsystem should have:

- a server-side feature flag
- versioned persistence where applicable
- admin/debug observability
- bounded performance behavior
- tests for restart/unload edge cases

## Performance assumptions

The initial production target is constrained. Therefore:

- no global per-tick scans
- no distant entity ticking
- no full-resolution unloaded-chunk entity pathfinding
- use coarse elapsed-time strategic simulation
- cache radar products and terrain masks
- cap expensive siege planners
- make performance limits configurable

## Release discipline

Do not update a dependency merely because a newer version exists.

A dependency change is complete only after the generated client/server pack boots, connects, loads the existing world where relevant, and the affected integration has been tested.

World-generation changes require special caution because new terrain may differ permanently from existing terrain.

## User experience

The public-facing name is **DrewCraft**.

The download site should remain deliberately simple: Windows and Mac install buttons. Complexity belongs in the launcher, not in setup instructions for friends.
