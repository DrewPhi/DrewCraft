# Covenant endgame overlay — native Illager Invasion worldgen suppression.
#
# Native Illager Invasion structures are NOT the canonical cult architecture.
# The eight cult sites + hidden capital are derived from the xSisyX kit and
# fitted to the pregenerated Terrain Diffusion production world
# (pack/manifest/endgame_content.yaml:50,92-180).
#
# This overlay empties the Illager Invasion has_structure biome tags so no
# illager_fort / illusioner_tower / firecaller_hut / sorcerer_hut / labyrinth
# generates in ANY biome. Upstream files live at
# data/illagerinvasion/tags/worldgen/biome/has_structure/*.json and
# data/illagerinvasion/worldgen/structure{,_set}/*.json.
#
# If upstream renames a tag file, the boot smoke test (server-smoke.yml) must
# fail on unexpected native structures rather than silently generating them.
# Woodland mansion data-marker spawns (Provoker/Warrior/Archivist/invoker via
# WoodlandMansionPieceMixin) have NO datapack hook: per owner decision C3 they
# are DOCUMENTED as ordinary dungeon danger, never strategic sources, unless a
# DrewCraft mixin guard is added later.
#
# Loot decision (C3d): native Illager Invasion loot tables are RETAINED for the
# playtest. They grant items only and create no strategic strength; DrewCraft
# scripture-fragment drops are injected separately with the guaranteed-fallback
# rule, so there is no second progression authority.
