# Flight/cache update — 2026-10-19

Launcher 0.1.17 remembers the optional LOD preload choice and automatically
checks the selected radius on subsequent launches. Already imported content is
skipped using receipts inside the persistent DH database. Download estimates
exclude imported tiles and locally cached archives; imports with no pending
tiles no longer demand gigabytes of spare disk space.

To change the saved radius, launch with `DREWCRAFT_CONFIGURE_LODS=1`, or delete
only `user-data/dh-preload.json` in the DrewCraft app directory. Do not delete
`user-data/dh-downloads` or the instance's `Distant_Horizons_server_data`.

Flight candidate: replace Chunk Sending with pinned NeoForge 1.21.1
SeamlessChunks 0.1.0-beta.7, with Architectury and YACL. It prioritizes chunks
ahead of movement; it does not permit safe flight through unloaded terrain or
guarantee MTS entity synchronization. No world format, terrain or seed change.
No custom vehicle/passenger freezing hook has been implemented.
