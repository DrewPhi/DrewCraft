# Map persistence update (prepared, not deployed)

Next pack: `0.1.11-dev-local`. Required launcher: `0.1.10`.

## Changes

- Include Xaero's World Map 1.40.11 on clients. Existing Minimap 26.1.0 and
  XaeroLib 1.1.0 remain pinned. Both mods' embedded NeoForge dependency ranges
  accept this combination. Newer World Map 1.46.0 requires Minimap 26.4.0+ and
  was deliberately not selected for this focused update.
- Official artifact: https://modrinth.com/mod/xaeros-world-map/version/arbQPyvf
  (author xaero96). Provider SHA-512 verified against downloaded bytes; SHA-256
  and size are recorded in `pack/manifest/candidate_hashes.yaml`.
- Preserve `xaero`, `XaeroWaypoints`, `XaeroWorldMap`, `config/xaero`, and legacy
  `config/xaerominimap.txt`, `config/xaeroworldmap.txt`, `config/xaerohud.txt`
  when upgrading or repairing a versioned instance. These are user-owned, not
  release-managed files. Never put personal map/config files in the pack layout.
- Before convergence, the new launcher takes a one-time recovery copy of these
  paths from retained DrewCraft instances into `<app>/recovery/xaero-v1/`.
  Each old instance has a separate directory and `inventory.json` lists copies.
  Originals are untouched. Nothing is merged into newer map files automatically:
  that could overwrite edits, resurrect intentionally deleted waypoints, or mix
  worlds/dimensions. Interrupted copying can retry before the inventory is marked
  complete. The ordinary active-instance data continues automatically.

## What this does not do

World Map records client exploration; DH's server LOD database does not populate
the fullscreen map. Prior travel without World Map cannot magically be restored
as an explored map. Maps remain local to each computer and world/server identity;
this is not cloud synchronization. A dimension switch legitimately shows its own
map and waypoints.

The laptop inspection found Xaero configuration files but no saved files in
the modern or legacy map/waypoint data paths under its retained managed instances.
No missing waypoints have been recovered here. Other computers may retain data;
their new launcher will archive it before the next update. For an archived file,
close Minecraft, back up the current map directory, then restore only the matching
server/dimension data. Do not blindly overwrite the entire current directory.

## Release order / verification

1. Build and publish launcher 0.1.10 for Windows, macOS and Linux first.
2. Build immutable pack `0.1.11-dev-local` with the unchanged Paradis profile plus
   client-only World Map; require launcher 0.1.10 so old launchers cannot migrate
   this pack while discarding mapping data.
3. Deploy matching server application using normal backup/activation checks,
   preserving world and DH catch-up controller state. No World Map server jar
   is needed; XaeroLib stays common-side.
4. Promote the channel pointer only after server health is confirmed.
5. Owner acceptance: create a waypoint, explore, disconnect/rejoin, restart the
   client, then verify waypoint and map persist. Test after an update/repair too.

Unit tests exercise data preservation during version upgrades and same-version
repair, separate recovery snapshots, and one-time migration. No interactive
Minecraft test or live rollout was performed for this change.
