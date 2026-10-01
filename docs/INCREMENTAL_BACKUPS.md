# Incremental server backups

The production backup helper supports Restic snapshots instead of repeated full
gzip archives. A configured host selects Restic through
`/srv/drewcraft/state/backup-config.json`; unconfigured hosts retain the legacy
archive backend, and old archive restores remain supported.

## Initialize once

Install Ubuntu's `restic` package, then run as root:

```bash
python3 /srv/drewcraft/bin/serverctl.py backup-init
```

This initializes a version-2 repository at `/srv/drewcraft/backups/restic` and
creates a random password file at `/etc/drewcraft/restic-password` with mode
0600, without printing its contents or overwriting an existing key. Preserve
that key securely outside the VM before relying on this for disaster recovery.
The repository and key are both needed; `.restic.json` receipts are not backups
on their own. Never commit the key or repository.

## Capture and restore

The existing `serverctl.py update` transaction now automatically takes an
incremental snapshot when configured. It stops Minecraft before capture,
backs up the entire persistent tree (including all dimensions, players,
operators, server properties, and model caches), checks repository structure,
then activates the release. Restic partial-backup exit status is a hard failure;
no successful receipt is written and update activation must not proceed.

For a manual backup, stop the pregen controller and Minecraft first, then use:

```bash
python3 /srv/drewcraft/bin/serverctl.py backup /srv/drewcraft/current/.drewcraft-release-manifest.json --label manual
```

Restart the services after success, or investigate a failure before continuing.
Receipts under `backups/*.restic.json` record snapshot ID, world identity,
release metadata, repository location, password-file path (not its contents),
and Restic's byte statistics. To restore into a separate, empty directory:

```bash
python3 /srv/drewcraft/bin/serverctl.py restore /srv/drewcraft/backups/RECEIPT.restic.json --target-root /srv/drewcraft/staging/restore-test
```

Restore uses `--verify`, rejects nonempty targets, and verifies world identity.
Never restore over the running world's files. Repoint repository/password paths
in a copied receipt when doing an off-host restore. The legacy `--copy-dir`
option is rejected for Restic: copying a receipt cannot replicate its backup.

## Verification and retention

Before removing a superseded full archive, perform `restic check --read-data`,
restore the whole snapshot into scratch space, and compare file hashes against
the stopped source. A repeat snapshot should add only small metadata changes
when the world is unchanged. Keep historical archives until separately
approved for deletion; a current snapshot cannot recreate older world states.

As approved September 30, keep exactly one DrewCraft restore point. A new
snapshot must complete and pass `restic check` before global `--keep-last 1`
retention/pruning removes old snapshots across labels and hosts. Both Restic
and archive defaults retain one; overrides are rejected. Restic uses maximum
compression for new data. Existing data requires a verified repository-copy
rewrite to change compression, not just a flag. See
`STORAGE_OPTIMIZATION_REVIEW.md` for the in-progress rewrite and tests.
Never delete individual repository pack files manually.

The first snapshot must store the data once; future snapshots reuse unchanged
chunks. New terrain and changed region data still cost space. The first full
restore test temporarily needs another world-sized directory. This saves disk
space and repeated compression work, not a guaranteed amount of RAM or time.
The local repository is on the same boot disk as the world: it protects against
logical mistakes, not loss of the VM/disk. Off-host replication is still needed
for disaster recovery and requires choosing a destination.

References: [Restic backups](https://restic.readthedocs.io/en/stable/040_backup.html),
[repository verification](https://restic.readthedocs.io/en/stable/045_working_with_repos.html),
[restoring snapshots](https://restic.readthedocs.io/en/stable/050_restore.html).

## Production migration evidence (2026-09-27 UTC)

- Restic 0.16.4 on the OCI ARM64 host, repository format 2.
- Initial snapshot `6e2fe85c649ca7830d44f89877bd62b06172ee24c63a75f8534b3081bf123b32`:
  3,393 files, 26,307,060,074 source bytes; first capture/check took 324 seconds.
- Full `check --read-data`: 1,126 packs checked with no errors.
- Entire snapshot restored with `--verify` to an isolated directory. An
  independent parallel SHA-256 comparison matched all 3,439 file/directory/link
  entries, including file sizes, permission modes, and symlink targets.
- Second snapshot/check took 1.94 seconds and added 3,167 bytes with no gameplay
  changes (only backup metadata changed). This is not a timing guarantee for
  backups after substantial terrain generation or player activity.
- Removed only the interrupted 533,217,280-byte September 27 gzip archive and
  the temporary restore directory after verification. Older completed archives
  remain available; no historical restore points were discarded.
- Machine-readable evidence: `/srv/drewcraft/state/restic-migration-proof.json`.
