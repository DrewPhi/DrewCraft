# DrewCraft World-Build Stages

DrewCraft must **not** jump directly from subsystem development to the approximately 200 GB production world.

The production world is expensive to generate and expensive to invalidate. World generation therefore proceeds through increasingly representative disposable/replaceable regions before the final pregeneration.

The core rule is:

> **Freeze the generation stack before paying the cost of the production world.**

## Stage A — development world

Target footprint: approximately **4,000 x 4,000 blocks**.

Purpose:

- prove the current Minecraft 1.21.1 / NeoForge / Java 21 profile boots with Terrain Diffusion World Scale 2;
- test selected structures and DrewCraft Source Core binding;
- test Covenant lore/drop plumbing;
- test Create, MTS, weather and new Create combat/mobility dependencies together;
- build and test representative roads, trains, artillery positions, aircraft and ships without paying production-world cost;
- catch obvious structure-placement, terrain, crash, save/restart and client-rendering problems.

This world is disposable. It may use temporary source placement and debug conveniences.

## Stage B — production-seed dress rehearsal

Target footprint: approximately **12,000–20,000 x 12,000–20,000 blocks**.

This stage should use the **intended production seed and intended production world-generation configuration**.

Purpose:

- judge whether DrewCraft actually feels geographically large at normal travel speeds;
- test Distant Horizons over long traversals;
- fly representative MTS routes;
- drive/rail representative routes;
- evaluate Terrain Diffusion mountains, valleys, rivers, coastlines and climate at meaningful scale;
- validate cult-site candidate scoring/spacing and sparse structure density;
- test strategic group ETA over real geography;
- test weather during long-distance flight;
- evaluate Aeronautics/Sable physics in representative terrain/chunk-loading conditions;
- build/test at least one realistic High Seas vessel if the stack passes earlier gates;
- measure generation speed, storage growth, backup/compression behavior and server traversal performance.

This is the point where we should be able to fly around and say: **yes, this feels like DrewCraft.**

If generation settings, structure density, world scale, biome/climate configuration, or a worldgen-relevant dependency changes after this stage, repeat the relevant dress rehearsal before production.

## Stage C — freeze production generation identity

Before generating the large production artifact, freeze and record:

- Minecraft version;
- NeoForge version;
- Java version;
- Terrain Diffusion Plus source/artifact identity;
- Terrain Diffusion model/config identity;
- World Scale 2;
- production seed;
- generation radius/border plan;
- every worldgen-affecting mod/datapack and exact hash;
- cult structure source kit and converted DrewCraft structure assets;
- cult-site placement/scoring rules;
- structure density/spacing configuration;
- initial playable-border configuration;
- hidden-frontier pregeneration plan;
- Chunky/world-build tool versions and commands.

No casual dependency update is allowed after this freeze. A worldgen-relevant change requires an explicit decision about regeneration/migration.

## Stage D — final production pregeneration

Only after Stages A–C pass, generate the full bounded production world, expected to be on the order of **~200 GB** before final measured sizing.

The final build must:

1. use the frozen generation profile;
2. pregenerate offline rather than during ordinary play;
3. run structure/source indexing and validation;
4. validate the eight Covenant major sites;
5. validate roads/access/terrain around those sites;
6. generate/validate the intended initial playable area;
7. pregenerate any hidden endgame frontier that must already exist on disk;
8. archive and checksum the resulting world;
9. restore it onto a clean server and verify startup/restart;
10. record compressed backup size and restore time;
11. run representative traversal/performance tests before declaring it the production artifact.

## Vespera / hidden capital

Do **not** lock the exact final capital site during the tiny development world.

Once the production seed is frozen:

1. inspect/scout terrain outside the initial playable frontier;
2. find an extraordinary mountain/plateau region at approximately the desired real aircraft travel distance from mature DrewCraft territory;
3. choose the exact Vespera location based on the actual Terrain Diffusion terrain;
4. hand-compose/refine the capital around that terrain using the shared cult architectural vocabulary;
5. validate the approach from long-range aircraft view and from ground level;
6. pregenerate/include that hidden frontier in the production artifact while keeping it inaccessible until the campaign opens it.

Vespera should be designed **from airplane silhouette inward**: distant skyline first, district hierarchy second, street-level gameplay third.

## Why this staging matters

A 200 GB pregeneration is not where DrewCraft should discover that:

- structures flatten mountains poorly;
- a structure pack is too dense;
- a mod changes world generation unexpectedly;
- the selected seed produces weak geography;
- Sable/physics dependencies cause chunk/persistence issues;
- long-distance flight feels too short or too long;
- the strategic source spacing is wrong;
- backups/restores are operationally impractical.

Those failures should be discovered in Stage A or B, when regeneration is cheap.
