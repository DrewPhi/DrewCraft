# Paradis field guide and crafting audit

2026-09-27. Audited the installed official Danny's AOT 2.4.3 artifact
(Modrinth version `p2GQ0M4J`, SHA-256 recorded in `AOT_INTEGRATION.md`). These
findings come from the jar's recipes, biome definitions, client key registration,
tooltips and generator/processing logic, not a complete survival playthrough.

## Welcome book

The server datapack's book now has 21 short pages: DrewCraft-specific pacifist
Paradis lore, the actual dock entrance, and a practical equipment guide. The
pacifist oath is our fictional framing, not a claim about upstream NPC AI or
Attack on Titan canon. No loot tables, NPC behavior or Titan spawning were
changed to implement the story. Scattered supplies are not a guarantee that
every finished weapon can be looted from the city.

Guide coverage: ODM/APG equipment, hooks and boost, blade maintenance, gas,
APG aiming/firing, thunder spears, flares, armor/boots/cloaks, crafting parts,
furnace processing, resource locations, syringes, shifter defaults, and other
special field items. Decorative variants use normal item controls. Creative
spawn eggs and the blocked special-account powers are not survival tutorials.
Defaults may conflict with other mods: notably AOT assigns H to both the right
hook and cloak hood. Players must resolve conflicts in Controls.

The hidden advancement ID is unchanged. Previously issued written books are
item snapshots and do not update automatically. Administrators can provide a
replacement with `/loot give <player> loot drewcraft_welcome:dock_guide` without
resetting the player's one-time grant record.

## Does Paradis contain everything?

The core AOT material chain is supported in Paradis:

- Iron bamboo patches are generated in the **Giant Forest** biome, outside
  walls and paths. Ordinary Overworld jungle bamboo is not a substitute.
- Iceburst ore is generated only in Paradis by a chunk-load generator near
  deep cave surfaces. Seeded vein centers are Y -64 through -1; individual
  search/placement offsets can extend outside that center interval.
- The generator includes coal, iron, copper, gold, redstone, lapis, diamond and
  emerald ores, and explicitly supports Create zinc when installed.
- Iceburst Furnace processing: iron bamboo + **raw iron** produces hardened
  iron bamboo; hardened iron bamboo + **iron ingot** produces ultrahard steel.
- The 56 bundled crafting recipes also use vanilla leather, wool, dyes,
  gunpowder, string, iron equipment, spruce materials, etc. Some special items
  come from progression/loot rather than ordinary crafting recipes.

Do **not** promise a wholly self-sufficient dimension. Its biomes list sheep,
rabbits, horses, wolves and/or goats, but no cows in the audited spawn lists.
Leather can still come from rabbits/horses or loot; importing a supply is easier.
Green dye is used by several recipes, and cactus generation was not established
by this audit. An Overworld desert/badlands cactus supply is the practical
recommendation, not proof that every possible alternative route is impossible.
Likewise, check JEI for vanilla dye and wood requirements rather than assuming
every ingredient is available in every Paradis biome.

Conclusion: mine/forage Paradis for the special AOT resources; keep an Overworld
supply line for ordinary materials. No specific Overworld-biome visit unlock
was found in the audited normal crafting recipes.

## Audit targets

`data/dannys-aot/recipe/*.json`, `data/dannys-aot/worldgen/biome/*.json`,
`ParadisChunkGenerator`, `IceburstOreGenerator`, `IceburstFurnaceBlockEntity`,
`DannysAotClient`, `ODMTickHandler`, `APGInputHandler`, and the ordinary equipment
item tooltips. Source/decompiled third-party code is not redistributed here.
