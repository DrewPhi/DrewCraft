# DrewCraft Cult Lore Content

This directory is the runtime/content source of truth for the Covenant of the Closed Sky campaign.

- `config.json` — faction identity, the Eight Chains, coordinate-fragment probabilities, drop routing, and Divided Waymark template.
- `books/*.json` — all 40 authored enemy-drop books, split five per Chain (four field books plus one sealed Vespera fragment).
- `../../../docs/lore/cult_lore_bible.md` — human-readable canon.
- `../../../docs/lore/IMPLEMENTATION.md` — runtime implementation contract.

Coordinates are resolved from the production `cult_sites.json` registry at item-drop time. Do not bake production coordinates into these files.
