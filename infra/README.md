# DrewCraft production host contract

BP8 targets **Ubuntu ARM64 on OCI Ampere A1 first**, with a deliberate fallback to another fixed-size VM if the real DrewCraft workload misses the performance gate.

## Current OCI sizing assumption

As of September 2026, Oracle's current Always Free documentation advertises **1,500 A1 OCPU-hours and 9,000 GB-hours per month**, equivalent to **2 OCPUs / 12 GB RAM** for a continuously running instance. Older DrewCraft notes that assumed 4 OCPUs / 24 GB are obsolete.

The first production benchmark therefore uses:

- `VM.Standard.A1.Flex`;
- 2 OCPUs;
- 12 GB RAM;
- one instance only;
- no instance pool;
- no autoscaling;
- no automatic scale-up;
- fixed boot/block storage chosen before provisioning.

If a paid OCI tenancy is used, create a dedicated DrewCraft compartment and enforce A1 resource quotas (`compute-core / standard-a1-core-count` and `compute-memory / standard-a1-memory-count`) before deploying. Budget alerts are useful but are not treated as hard billing limits.

## Files

- `bootstrap_ubuntu_arm64.sh` — one-time non-root host/runtime/firewall setup;
- `drewcraft.service` — Minecraft systemd unit;
- `drewcraft-health.service` + `health_server.py` — read-only client compatibility endpoint;
- `serverctl.py` — staged releases, exact hash verification, world-identity guard, backup, activation, application-only rollback, and restore.
- Configured production backups use Restic deduplicated snapshots; see `docs/INCREMENTAL_BACKUPS.md` for initialization, verified restore, key custody, and retention. Legacy archive restores remain supported.
- `start-server.sh`, `server.properties`, `user_jvm_args.txt`, and `eula.txt` — production runtime templates. `allow-flight=true` is intentional so legitimate MTS aircraft do not trigger vanilla's flying-player kick.
- `pregen_controller.py` + `drewcraft-pregen.service` — resumable, size-targeted Overworld-only generation. The controller waits until the server is empty, advances Chunky in 1,024-block radius batches, then lets DH trail 512 blocks behind the confirmed Chunky frontier. Jobs pause on player join (10-second polling) and resume after 600 seconds empty. On completion or in DH-only mode, one native center-out catch-up pass encloses the actual saved region bounds. Thereafter a cheap 60-second region mtime/size check queues only new/changed areas, grouped into 2,048-block squares and ordered nearest spawn first. Unchanged terrain causes no new native pass. DH's own live chunk hashing handles player edits and skips unchanged chunks. Task snapshots, queues, and baselines persist across restarts; changes during a pass remain dirty for the next check. Nether and End are never selected or bordered by this controller. The older `--dh-maintenance-interval-seconds` flag is accepted for existing service units but no longer schedules whole-world hourly sweeps.

## Filesystem contract

```text
/srv/drewcraft/
  releases/<packVersion>/     immutable application releases
  current -> releases/...     atomic application pointer
  persistent/world/           authoritative Minecraft world + DrewCraft SavedData
  persistent/terrain-diffusion-models/ reusable pinned model downloads
  persistent/terrain-diffusion-cache/  reusable Terrain Diffusion runtime cache
  persistent/operator/        whitelist, operators, and ban lists
  backups/                    Restic repository/receipts and legacy archives
  logs/                       persistent logs
  state/                      active-release.json + health.json
  staging/                    incomplete release downloads
  bin/                        stable host helper scripts
```

`current/world`, `current/logs`, model caches, whitelist, operators, and ban lists are symlinked to persistent storage at activation/startup. Application rollback changes only `current`; it never restores an older world automatically.

## Deployment transaction

1. Read and validate `release-manifest.json`.
2. Verify `persistent/world/drewcraft-world.json` matches manifest `worldId`, `worldRevision`, and `generationPackVersion`.
3. Download the server/common release into staging.
4. Verify every size and SHA-256.
5. Stop Minecraft (and the pregeneration controller).
6. Create and verify a pre-update backup of the entire persistent tree; configured hosts use incremental Restic snapshots.
7. Atomically switch `current`.
8. Start Minecraft and run health checks.
9. Publish `health.json` as `ready` only after the check passes.
10. On application failure, restore only the prior application pointer and restart it against the unchanged persistent world.

## Performance decision gate

OCI A1 2/12 is accepted only if BP9 representative load testing meets the final MSPT/memory/GC/player-experience limits. The architecture does not depend on Oracle: the release and persistent-world layout can be moved as a unit to another fixed-size ARM64/x64 Linux host.

A paid VM must not be silently resized. Any migration or larger shape is a deliberate operator action.
## Canonical live world-size command

After SSH login, run `sudo drewcraft-world-size`. For automation, run
`sudo drewcraft-world-size --json`. Source: `infra/world_size.py`; install with
`sudo install -m 755 infra/world_size.py /usr/local/bin/drewcraft-world-size`.
The draft Linear-aware version also requires `region_inventory.py` beside
the installed command, and beside `/srv/drewcraft/bin/pregen_controller.py`.
Deploy those files together; do not overwrite only the controller/command.
Linear slot inspection requires system `libzstd`; Anvil inspection does not.
This draft is not yet installed on production.

This read-only command measures current world files, rather than cached size
counters. It labels all-dimension world usage (including DH), allocated disk
space, DH usage, storage target, Chunky-confirmed completed circle,
in-progress target, playable border and irregular saved-chunk extents
separately. Empty/short region placeholders do not count as saved chunks.
Legacy radius counters are ignored. Output is a live non-atomic snapshot;
task-confirmed radius is not an independent chunk-status/LOD audit.
