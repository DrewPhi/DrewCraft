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
recipes) rather than ordinary feature-heavy gameplay mods. Community reports and
developer discussions indicate that 1.21-era vehicle packs often continue to
work on newer NeoForge releases because most of the pack is data and assets
rather than executable Java code. This is a strong compatibility expectation,
not a blanket guarantee: packs can still contain loader metadata or
version-specific paths. They must therefore be tested as exact client/server
artifacts in a disposable world before shipping.

If a pack does need conversion, the MTS NeoForge porting checklist includes
replacing the Forge descriptor, removing legacy loader classes and MTL files,
generating item models, flattening item textures, and migrating language/recipe
paths and formats.

The preferred path is still a native 1.21.1 NeoForge release from the authors.
If none exists, porting is a separate compatibility project requiring
author/licensing review, exact client/server artifacts, a disposable-world test,
vehicle spawn and save/reload coverage, and a rollback path. Prioritize UNU
Parts/Vehicles first, then WarBorn, with GAP as the most legacy-heavy candidate.
The official 1.21.1 Immersive Vehicles content pack already remains part of V1.

## Danny's AOT: isolated Paradis adventure plan

**Requested:** 2026-09-26. Planning only; not added to the shipping modpack.

Goal: offer an optional Titan/ODM adventure in Paradis while keeping Titans out
of the Overworld, Nether, and End. Preserve the existing Terrain Diffusion world.

The [official project](https://modrinth.com/mod/dannys-aot) already describes a
Paradis dimension with giant forests, walled villages, Titans, and portal access.
Its published loader is Fabric for Minecraft 1.21.1, not native NeoForge. The
author's [1.0.13 changelog](https://www.curseforge.com/minecraft/mc-mods/dannys-aot/files/7689259)
explicitly mentions Create zinc ore support with NeoForge/Sinytra Connector.
That is evidence for a compatibility route, not proof that the latest release
works with DrewCraft's complete stack. Default dimension isolation is unverified.

Implementation gates, before any live deployment:

1. Select exact AOT, Connector, and required dependency artifacts; review
   acquisition/licensing and conflicts with our existing libraries. Do not
   replace NeoForge or silently change Create/Aeronautics/Sable dependencies.
2. Test a separate client/server compatibility profile: startup, join, ODM,
   combat, portal travel, dimension generation, save/reload, and restart.
   Verify survival access and progression; upstream warns of development bugs.
3. Inspect spawn rules, player shifting, summoning, scripted events, and portal
   transport. Prefer supported configuration; otherwise evaluate a narrow
   server-side restriction. Require Titans and Titan transformations to remain
   in Paradis, including after reconnects and dimension travel. Verify all three
   ordinary dimensions stay free of Titans; do not assume natural-spawn settings
   alone enforce this policy.
4. Verify portal access from the existing world without resetting it, and no
   unintended changes to ordinary dimension generation. Measure Titan AI,
   dimension-generation, client rendering, memory, and storage costs. Keep the
   existing Overworld pregen controller from automatically targeting Paradis.
5. Report compatibility/isolation evidence and any limitations for approval.
   Only then lock one client/server manifest, back up before deployment, and
   define rollback handling for players/items saved in the added dimension.

### Planned ocean dock location

Read-only scouting of the existing production Overworld (world revision 3,
Terrain Diffusion scale 3) identified this provisional location:

- Ocean candidate: **X -2104, Y 64, Z -1976**, sampled surface water in
  `minecraft:lukewarm_ocean`.
- Nearby shore: **X -2040, Y 66, Z -1976**, sampled red sand in
  `minecraft:badlands`.
- World spawn: **X -1536, Y 92, Z -1536**. The ocean candidate is approximately
  **718 blocks northwest of spawn** (horizontal straight-line distance).

The scout sampled 1,600 already-generated chunks near spawn. It did not change
blocks, generate terrain, or place a structure. These coordinates identify an
area to inspect, not a validated structure origin, deck height, or orientation.

Preferred implementation: place one upstream dock at this existing coastline
after the compatibility and Titan-isolation gates pass. First inspect the
actual dock/template footprint, water depth, shoreline, and any player builds;
choose the final anchor and rotation without overwriting player work. Verify
whether upstream supports `/place structure` or template placement and whether
the placed portal needs additional initialization. Back up before placement,
then test entry to Paradis, return travel, and persistence after restart.
Do not regenerate the Overworld to obtain the dock.

Owner decisions confirmed on 2026-09-26:

- Only this planned dock in the Overworld; disable automatic AOT structures,
  including in future chunks. Upstream's dock generator also processes loaded
  existing chunks, so suppression must be active before the first AOT boot.
- Dock/portal access is open to everyone immediately, with no progression gate.
- ODM and ordinary AOT equipment remain usable in all dimensions.
- Titans, Titan transformations, AOT mobs and events are restricted to Paradis.
- Block the special `/daot danny` privileges for everyone, including upstream
  hard-coded accounts. Preserve normal AOT progression and transformation.

Implementation is authorized, but not deployed. The minimal AOT/Connector
dedicated-server boot passed; full-pack/client compatibility, containment,
portal return and persistence are still unverified. See
`AOT_INTEGRATION.md` for pinned audit inputs, findings and remaining gates.
No AOT content or dock has been installed on production.

If compatibility or isolation cannot be made reliable, leave this feature
deferred rather than exposing the production world to uncontrolled Titan behavior.

## Re-entry rule

A post-V1 idea may enter a later release only with a narrow player-facing goal, an explicit dependency/profile change, server/client compatibility evidence, a performance budget, and a rollback path. Completed custom code remains disabled by default until such a release adopts it.
