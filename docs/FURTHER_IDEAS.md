# DrewCraft Further Ideas

**Status:** post-V1 design backlog  
**Moved out of V1:** 2026-09-16

These ideas are intentionally preserved, not abandoned. They should be reconsidered only after the focused survival/exploration V1 is stable and fun with friends.

## Environment and aviation

- Project Atmosphere as authoritative weather simulation.
- Simple Clouds integration and Serene Seasons.
- Terrain-aware weather, MTS wind/turbulence/visibility effects, and aircraft instruments.
- DrewCraft weather and terrain products on Create: Radars.

Primary archived designs: `RADAR_V1.md`, `PROJECT_SPEC.md`, and `SYSTEMS.md`.

## Strategic world and endgame

- Persistent hostile sources and Source Cores.
- Factions, patrols, hordes, raids, reinforcements, and large abstract armies.
- Unloaded strategic movement, ETA, materialization, and casualty reconciliation.
- Path-first constrained sieges and destructible strategic objectives.
- Covenant/Illager invasion content and a unique endgame that gives aircraft and artillery strategic targets.
- Persistent wild herds and broader ecology.

Primary archived designs: `STRATEGIC_WORLD_MODEL.md`, `STRATEGIC_MATERIALIZATION.md`, `STRATEGIC_SOURCES.md`, `HOSTILE_FORCES_V1.md`, `SOURCE_CORE_SPEC.md`, `SIEGE_V1.md`, `HERDS_ECOLOGY_V1.md`, and `end_game_plans.md`.

## Later polish and expansion

- Weather/cloud visual polish and cockpit radar.
- Additional curated dungeons or objectives after density and performance testing.
- Progression, recipes, fuel economy, vehicle balance, artillery damage policy, and server events.
- Re-evaluation of currently incompatible Create add-ons only after upstream compatibility changes.
- Larger hosting shape only if measured multiplayer performance requires it.

## Post-V1 Immersive Vehicles compatibility goals

These content packs are explicitly deferred until the focused 1.21.1 NeoForge V1
is stable. They must not be added to the shipping profile by renaming or bypassing
the exact-artifact checks:

- UNU Parts / Vehicles packs, beginning with a compatibility investigation against
  the current 1.21.1 MTS release.
- WarBorn Military Pack, currently published for older Forge/Minecraft versions.
- Golden Airport Pack (GAP), whose published files target 1.16.5/1.12.2 Forge.

These are MTS content archives (JSON definitions, models, textures, sounds, and
recipes) rather than ordinary feature-heavy gameplay mods, so a port is expected
to be feasible. They are **not** assumed to be drop-in compatible, however. The
MTS NeoForge porting checklist includes replacing the Forge descriptor, removing
legacy loader classes and MTL files, generating item models, flattening item
textures, and migrating language/recipe paths and formats.

The preferred path is still a native 1.21.1 NeoForge release from the authors.
If none exists, porting is a separate compatibility project requiring
author/licensing review, exact client/server artifacts, a disposable-world test,
vehicle spawn and save/reload coverage, and a rollback path. Prioritize UNU
Parts/Vehicles first, then WarBorn, with GAP as the most legacy-heavy candidate.
The official 1.21.1 Immersive Vehicles content pack already remains part of V1.

## Re-entry rule

A post-V1 idea may enter a later release only with a narrow player-facing goal, an explicit dependency/profile change, server/client compatibility evidence, a performance budget, and a rollback path. Completed custom code remains disabled by default until such a release adopts it.
