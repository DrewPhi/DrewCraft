# MTS recipe integration

The V1.1 integration profile uses Create iron sheets, Crafts & Additions iron
rods and copper wire, and vanilla iron nuggets instead of MTS generic stock.
MTS functional components and final vehicle assembly remain in use.

The generator owns both `mtscraftingoverrides.json` (MTS workbench recipes)
and the integration datapack (crafting-table recipes). IR sensors now use
Crafts & Additions copper wire and iron rods. The original plating, screw,
metal-tube and copper-wire crafting recipes are disabled with NeoForge false
conditions under their original recipe IDs. Item registrations remain intact
to preserve existing inventories.

The four retired items are hidden via `c:hidden_from_recipe_viewers`, with
optional entries and without replacing other mods' tag values. The pinned JEI
19.51.0.418 recognizes this tag. The pinned MTS 24.0.0 JEI workbench category
calls `PackMaterialComponent.parseFromJSON`, using the same ingredient
definitions as MTS crafting rather than a separate set of display recipes.

When the integration overlay is present, `inject_drewcraft_mod.py` bundles its
data into the generated DrewCraft jar before recording the release hash. This
makes recipes, loot overrides and the JEI tag available in existing worlds
and single-player without manually enabling a loose datapack. Profiles without
that overlay do not acquire the integration data.

Validation: focused generator/injection tests pass; exact Official Pack V29
ingredient audit checks normal recipes plus subtype/repair ingredient lists.
An in-game JEI/workbench crafting comparison is still required after release.
These changes do not reset the world or change terrain generation.
