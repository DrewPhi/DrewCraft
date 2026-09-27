# One-time dock guide

Production-world datapack for Minecraft 1.21.1 (pack format 48). Install this
directory into the persistent world's `datapacks/` directory and reload. This
is server-owned world content, not a client mod or application-manifest change.
It contains no terrain/structure/dimension definitions and does not regenerate
the world. Keep it with the world during application upgrades and backups.

A hidden tick advancement rewards exactly one written book per player. Vanilla
stores advancement completion by UUID across relogs, deaths and restarts. Players
already on the server receive it on their next tick after installation; other
players receive it on their next/first join. No recurring tick function or
advancement revocation is used. Full inventories use vanilla advancement reward
delivery (the book drops beside the player). Losing the book does not regrant it.

Normal book copying is allowed. Resetting/removing a player's advancement data
or explicitly revoking this advancement can regrant it; this is not a guarantee
against admin resets or save rollbacks. Keep the advancement ID stable across
book-content updates to avoid distributing duplicates.

Dock entrance: Overworld X -713, Z -180, deck block Y 64. The authoritative
placement and portal caveats are recorded in `docs/AOT_INTEGRATION.md`.

The current edition contains 21 short lore/tutorial pages. See
`docs/AOT_FIELD_GUIDE.md` for the resource/control audit and limitations.
Existing book items keep their previous text; distributing an updated edition
does not reset or revoke the one-time advancement.

To deliberately replace a lost book without resetting the grant marker:

`/loot give <player> loot drewcraft_welcome:dock_guide`
