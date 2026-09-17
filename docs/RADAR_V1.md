# DrewCraft V1 Radar Contract

> **Post-V1 design archive (2026-09-16):** Native Create: Radars is V1 content. Everything described below beyond the upstream radar itself—weather products, radar-height behavior, terrain masking, and overlays—is deferred and disabled in V1. See `FURTHER_IDEAS.md`.

## V1 scope

DrewCraft V1 uses **Create: Radars 0.4.9.4 for Minecraft 1.21.1 NeoForge** as the physical radar frontend. DrewCraft does not duplicate its dish, bearing, Create kinetic operation, native entity scanning, filters, network/controller system, monitor blocks, models or textures.

The official unmodified Create: Radars artifact remains an upstream dependency. DrewCraft integrates externally through an isolated fail-closed compatibility bridge and optional `@Pseudo` mixins; no upstream source or art is copied into this repository.

Create: Radars declares **Create Big Cannons >=5.11.2** as a required runtime dependency. DrewCraft pins the current stable **Create Big Cannons 5.11.7** for 1.21.1 NeoForge, which in turn requires **Ritchie's Projectile Library 2.1.2**. These are treated as ordinary pinned upstream dependencies.

### Deferred DrewCraft radar extensions (post-V1)

The following concepts are retained as design notes only. They must remain disabled and absent from the V1 runtime path:

- a cached 9x9 Project Atmosphere precipitation/storm product centered on the radar;
- Terrain Diffusion realized-world terrain masking along each weather beam;
- antenna elevation effects because the terrain ray begins at the physical radar's world position;
- station wind direction/speed and temperature readouts when Project Atmosphere exposes those values;
- an in-world monitor overlay rendered below Create: Radars' normal sweep and contacts;
- the same weather overlay/readout in Create: Radars' full-screen monitor UI.

Weather sampling is server-authoritative and cached for 20 ticks. Every monitor update for the same radar/range reuses that cached product. DrewCraft does not client-scan the world, force-load chunks, or invoke Terrain Diffusion inference.

Terrain samples that are unavailable remain `UNKNOWN`; a positive realized-terrain obstruction masks the weather return. This preserves the V1 rule that a larger dish increases potential hardware range while a higher/better-sited antenna determines how much of that range is usable through terrain. The final representative pre-generated-world acceptance run is the authority for the practical low-site/high-site coverage behavior.

### Native contacts (V1)

Create: Radars continues to render and filter its own players/mobs/animals/contraptions/other supported contacts. DrewCraft's weather is a background layer; it does not replace or reimplement native contact scanning.

### Portable weather radar (post-V1)

Project Atmosphere already provides the V1 handheld **Weather Radar** item and screen. DrewCraft does not add a second handheld radar.

### Aviation boundary (post-V1)

MTS cockpit radar and a dedicated airborne traffic/weather instrument are **post-V1 (V1.1+)**. V1 pilots use Project Atmosphere's handheld weather radar and communicate with player-operated ATC/ground radar stations for traffic/contact information.

The Create: Radars compatibility bridge deliberately ignores its `nonspinning` aircraft/ship radar type in V1 so this boundary is explicit.

## Failure behavior for the deferred bridge

If Create: Radars is absent or its implementation shape changes, the optional mixins do not make DrewCraft fail to compile. If runtime reflection cannot bind, the weather extension fails closed and logs the compatibility failure once. Create: Radars' normal behavior is not replaced.

If Project Atmosphere or Terrain Diffusion data is unavailable, no fabricated meteorological/terrain values are generated. Native Create: Radars contacts continue independently.

## Post-V1 acceptance checklist

The final V1 full-stack acceptance run must verify, in one representative world/build:

1. a powered Create: Radars ground radar assembles and its normal native contacts/filters still work;
2. increasing dish construction increases the hardware range reported by Create: Radars and expands DrewCraft weather coverage to the same range;
3. a low/terrain-obstructed site loses weather cells behind realized terrain while a higher site improves coverage;
4. precipitation/storm cells shown on the Create monitor agree with the same underlying Project Atmosphere weather observed by the existing handheld Weather Radar;
5. wind speed/direction and temperature readouts update from Project Atmosphere values;
6. native contacts remain visible on top of weather returns;
7. multiple monitors do not multiply server weather sampling because they reuse the per-radar/range cache;
8. stopping the Create radar makes the weather product offline and restoring operation recovers cleanly;
9. no radar path force-loads terrain chunks or invokes Terrain Diffusion inference;
10. restart/client reconnect does not leave stale weather overlays.
