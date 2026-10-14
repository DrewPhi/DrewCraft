# Optional radius-based DH preloading — candidate

Branch: `feature/dh-radius-preload`. **Not published or deployed.** The working
launcher 0.1.15 and server pack 0.1.18 remain unchanged.

## User experience

When the shipping manifest supplies an HTTPS `server.dhPreloadUrl`, the launcher
checks its catalog and offers a remembered opt-in checkbox and radius slider.
Zero means skip; the maximum covers all observed finest-detail LOD extents from
the chosen center, not the Chunky target or a claim of continuous LOD coverage.
Compressed size is an upper estimate; cached/applied tiles can cost zero bytes.
The transfer reports per-file progress/ETA. Skip/cancel retains valid completed
tiles and rolls back the current import before launching. Unavailable catalogs
or optional preload errors must not block normal play.

Center: locally recorded last known Overworld location for the exact world,
otherwise world spawn. A client-only recorder samples every ten seconds and at
normal logout. Positions remain local; no public player-position endpoint.
It requires the updated DrewCraft integration jar (not yet released).

DH can choose different name-based folders for direct-connect/server-list joins.
Successful opt-in preloading selects IP_ONLY for this managed instance so DH
uses the known cache on first join; old cache folders remain untouched. Existing
server-provided keys take precedence. Unknown custom folder modes are not guessed.
Guava's exact percent-escaping was checked with a Java probe, including IP dots.

## Data design

`tools/export_dh_preload.py` uses SQLite online backup to obtain a consistent
snapshot without changing world data. It exports finest-detail and parent LOD
rows into immutable gzip/JSON-line tiles, grouped into 16x16 section cells per
detail level. Only the DH migration schema is copied into a fresh empty database
template; no player data/credentials/other world databases are published.

SHA-256 hashes identify payloads. Unchanged tile content retains its prior URL;
new/revised tiles get immutable release URLs. The small HTTPS catalog is promoted
last. Neither exporter nor launcher uploads/publishes by itself. A publishing
job/cadence is still needed before enabling this in a public pack.

The launcher validates world ID/revision/address/dimension, exact DH hash, schema
layout and payload hashes. Per-tile SQLite transactions retain newer client rows
and record successful imports inside the database, not an unrelated marker.
Old applied tiles aren't downloaded again, even after a launcher restart. Normal
DH synchronization still updates live changes during play; this is not a promise
that every server edit appears in the offline catalog immediately.

Imports require the managed game to be closed, with psutil process checks and
SQLite writer locking. The implementation must pass review of process detection
before publication. The launcher itself also serializes preparation. No `.mca`,
`.linear`, inventory, player-save or authoritative world files are imported.

Pack updates preserve `Distant_Horizons_server_data` using SQLite backup for
databases, excluding WAL/SHM sidecars and never hard-linking mutable databases.
Models keep their existing immutable hard-link behavior. Old server/client world
identity is never inferred from raw region extents.

## Gates before public rollout

1. Local tests: radius/negative coordinates/parents, hash/world/schema rejection,
   cancellation rollback, newer-row retention, unchanged-tile reuse, resume,
   no-op skip and WAL-consistent cache preservation.
2. Native Windows/macOS/Linux preparation/import tests and compiled client-only
   Java recorder must pass on this branch. BP8 publication is main-only.
3. Real DH333 fixture: compare exported/imported rows byte-for-byte, then boot
   and save with the imported DB; no owner account, rendering or live world.
4. Export a bounded candidate from actual production DH with an independently
   verified DH level key/seed hash. Validate the actual schema and mapping.
5. Review offline-process/cache locking, destination naming, disk-space needs,
   and compatibility with an existing real client cache. Renderer/flight remains
   owner acceptance; preloaded data cannot guarantee mesh or full-chunk speed.
6. Publish snapshot tiles/template first, catalog last, set up repeat exports
   (idle/after completed DH batches), and build one client/server manifest with
   the client recorder and catalog URL. Only then promote the new launcher/pack.

Current candidate does not stop/restart production, expose a new port, export
private player positions or provision cloud resources. First production export,
automatic publishing/cadence, real-world cache acceptance and public rollout
remain pending. Do not describe this source implementation as live functionality.
