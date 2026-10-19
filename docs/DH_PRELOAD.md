# Optional radius-based DH preloading

Current: pack 0.1.19 completed rollout on October 14. Launcher 0.1.17 was
published October 19 with remembered preload choices and pending-only download
estimates. See `FLIGHT_CACHE_UPDATE.md` and `CURRENT_BREAKPOINT.md` for the
current flight-update checkpoint. October 14 staging notes below are historical,
not current deployment status.

October 14 rollout: native 0.1.16 builds passed (38634525372); the recorder
compiled in 38634214200. Pack 0.1.19 is staged as an immutable prerelease, NOT
promoted. Its integration jar preserves every production entry byte-for-byte
and adds only `LastOverworldLocation.class`; all other managed files are unchanged.
252 local tests pass, including signed-publication and backup-hold rotation.

Production export runs as `drewcraft-lod-export-v2-20261014.service`. SQLite WAL
read snapshot pinning prevents writes from restarting the copy. The consistent
snapshot completed at 20:50:12 UTC; tile packaging follows. Relay job
`drewcraft-lod-relay-first-20261014` adopts only a completed catalog, signs it,
and enables `drewcraft-lod-export.timer` (six-hour idle checks after new DH jobs).
Export jobs are low-priority and preserve a 25 GiB free-space reserve.

Only public verification material lives in Git. A dedicated server RSA key signs
LOD data, not SSH/GitHub operations. The existing health port serves only a signed
envelope and content-addressed visual blobs, never arbitrary/world paths. GitHub
verifies signatures, world identity, payload hashes and uploaded asset sizes,
then promotes catalog last. No owner SSH key or GitHub credential is copied.
Unreferenced relay blobs expire after seven days; current referenced files stay.

The controller requests a Chunky pause after an hour-long slice, waits for async
work to drain, runs saved-terrain DH jobs, then continues the exact checkpoint.
Pausing never advances completed coverage. Live controller is waiting for Chunky
drain; actual new native DH-job start remains to verify. Player pauses remain.

## User experience

Since launcher 0.1.17 the first choice is remembered: subsequent launches check
the saved radius automatically and skip already imported tiles. Disabled preloads
stay disabled. Set `DREWCRAFT_CONFIGURE_LODS=1` to reopen the radius selector, or
remove only `user-data/dh-preload.json`. Archives and imported databases persist.
Network estimates exclude imported tiles and locally cached archives; archive
hashes are checked before import. If no tiles need importing, no extra disk-space
reservation is demanded.

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
It requires the updated DrewCraft integration jar (staged in pack 0.1.19).

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
last. Neither exporter nor launcher uploads/publishes by itself. The signed relay
and GitHub publisher above implement refresh publication; the first full catalog
must still finish before enabling this in a public pack.

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

## Basic validation evidence

- 240 local Python tests pass.
- Native Windows/macOS/Linux candidate tests/builds and ARM Java compilation
  passed: Actions `38628888742`. Publication intentionally skipped on branch.
- Real pinned DH333 export/import/restart passed: Actions `38628963071`.
  Exported/imported rows match byte-for-byte before DH opens/saves the DB.
- `tools/dh_production_preload_probe.py` passed on a bounded read-only production
  sample: 256 base sections + 90 parent sections, 10 tiles, 33,839,298 compressed
  payload bytes. Exact binary/metadata equality and SQLite integrity passed.
  Layout fingerprint `8ac02d06c086b839a50ce847b4f8a0d077ccbf53b3a864ac90592bbae406f9b9`.
  Private result directory: `/srv/drewcraft/state/dh-preload-validation-20261014`.
  No source DB writes, server restart, publication or owner-account launch.

These basic gates are green. Remaining work is release infrastructure: full
catalog export + HTTPS tile/catalog publication + refresh cadence + immutable
pack including the client recorder + launcher release promotion. Real rendered
client acceptance and actual flight performance remain owner tests, not proven
by the database/server fixture.
