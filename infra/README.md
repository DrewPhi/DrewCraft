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

## Filesystem contract

```text
/srv/drewcraft/
  releases/<packVersion>/     immutable application releases
  current -> releases/...     atomic application pointer
  persistent/world/           authoritative Minecraft world + DrewCraft SavedData
  persistent/terrain-diffusion-models/ reusable pinned model downloads
  persistent/terrain-diffusion-cache/  reusable Terrain Diffusion runtime cache
  backups/                    checksummed persistent-state archives
  logs/                       persistent logs
  state/                      active-release.json + health.json
  staging/                    incomplete release downloads
  bin/                        stable host helper scripts
```

`current/world` and `current/logs` are symlinked to the persistent trees at activation/startup. Application rollback changes only `current`; it never restores an older world automatically.

## Deployment transaction

1. Read and validate `release-manifest.json`.
2. Verify `persistent/world/drewcraft-world.json` matches manifest `worldId`, `worldRevision`, and `generationPackVersion`.
3. Download the server/common release into staging.
4. Verify every size and SHA-256.
5. Create a checksummed pre-update backup of the entire persistent tree.
6. Stop Minecraft.
7. Atomically switch `current`.
8. Start Minecraft and run health checks.
9. Publish `health.json` as `ready` only after the check passes.
10. On application failure, restore only the prior application pointer and restart it against the unchanged persistent world.

## Performance decision gate

OCI A1 2/12 is accepted only if BP9 representative load testing meets the final MSPT/memory/GC/player-experience limits. The architecture does not depend on Oracle: the release and persistent-world layout can be moved as a unit to another fixed-size ARM64/x64 Linux host.

A paid VM must not be silently resized. Any migration or larger shape is a deliberate operator action.
