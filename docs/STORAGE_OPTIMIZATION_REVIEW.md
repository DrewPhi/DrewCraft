# Storage review — 2026-09-30

Owner approved retaining one backup and evaluating compression, compaction,
and Linear. No production world format/filesystem conversion was approved
or performed. No Minecraft restart or client update is required for backups.

## Backup policy (installed)

`infra/serverctl.py` now uses Restic `--compression max`, checks a completed
replacement before forgetting older snapshots, and retains one global
DrewCraft snapshot across labels/hosts. Stale receipts are removed only after
the retained snapshot is confirmed. Archive fallback uses gzip level 9 and
retention one; requests to bypass the one-backup policy fail.

Existing compressed Restic data cannot be recompressed in place merely by
changing the compression flag. `infra/migrate_backup_max.py` is running as
`drewcraft-backup-max.service`, Nice=15, CPUQuota=200%, copying only the newest
of eight original snapshots to `/srv/drewcraft/backups/restic-max`. It checks
ALL retained data and verifies the snapshot tree before changing config and
deleting the old repository/seven older restore points. Password contents
are not inspected. The newest restore point dates from September 28; this
operation preserves it, not a new snapshot of current running-world data.

Migration completed successfully at 2026-10-01 00:04:11 UTC (September 30
local time). All 1,136 packs passed full data verification with no errors.
Seven older restore points and their old repository were permanently removed.
Exactly one retained snapshot: `10beba0b249731ca1c6b16b37f870c0687b8a238bca3aaa62da793f948f6bb44`.
Config now points to `/srv/drewcraft/backups/restic-max` with max compression
and retention one. Check:

```sh
sudo systemctl status drewcraft-backup-max --no-pager
sudo journalctl -u drewcraft-backup-max -n 15 --no-pager
sudo cat /srv/drewcraft/state/backup-config.json
```

After completion, confirm exactly one snapshot using the configured repo
and password-file (do not print password contents). Do not rerun the
migration blindly; it intentionally refuses an existing destination.
Cleanup is permanent for the seven older restore points. Space savings
depend on deduplication; do not promise that removing seven snapshots will
recover the entire old 21 GB repository.

## Measured copied-region results

Five self-contained region files restored and verified from the September
28 snapshot; 5,120 occupied chunk slots; 75,976,704 original bytes. These are
a sample, not a whole-world audit or guarantee of identical savings.

| Experiment | Sample result | Deployment decision |
| --- | --- | --- |
| Offline sector compaction | 2,166,784 bytes reclaimed, 2.85%; all payload sectors and timestamps preserved | Format compatible, small benefit. Do not rewrite open live regions. |
| Actual disposable Btrfs, `compress-force=zstd:15` | Data extents 64,761,856 bytes vs 75,976,704 logical bytes: 14.76% reduction; byte-identical readback | Preserves mod-visible files; production requires a filesystem migration and downtime. Not applied to ext4. |
| Linear-layout Zstd level 3 | 38,705,538 bytes, 49.06% smaller | Format experiment ONLY; not a mod runtime pass. |
| Linear-layout Zstd level 15 | 28,869,523 bytes, 62.00% smaller | Around 5–8 seconds encoding each sample region vs ~0.2–0.3 seconds at level 3; not an appropriate blanket hot-path maximum. |

Btrfs metadata/allocation overhead is separate. `btrfs filesystem du` reports
logical referenced extents; physical compression was measured with
`btrfs filesystem df -b`. Disposable loop filesystem was unmounted and its
image removed. No live mount/format/config changes. Compacted copies were
discarded; source world files were never rewritten. Benchmark implementation:
`infra/storage_benchmark.py`.

DH is already Zstd-compressed with `VISUALLY_EQUAL` world compression.
Earlier SQLite read-only audit found 8 free pages out of 1,594,350; vacuuming
is not a meaningful capacity win and no live database vacuum was performed.

## Linear compatibility blocker

October 1 code-only follow-up: a draft DH cold-reader mixin and Linear-aware
controller/inventory are now implemented and compile/unit tests pass. They
are NOT deployed or runtime-verified; the original blocker below describes
the installed production stack. Owner prohibits development Minecraft tests.
See CURRENT_BREAKPOINT for remaining gates, not a compatibility approval.

Reviewed memesgmm/Linear commit
`aa693e448723a817504957eec2a9c923f7af7ef5`. It provides C2ME-specific wrappers
and DH/Chunky pregen tuning, but those do NOT prove our runtime compatible.

- `infra/pregen_controller.py` fingerprints only `r.*.*.mca`.
- `infra/world_size.py` reads Anvil headers only.
- Decompiled installed DH 3.3.1's
  `RegionFileStorageExternalCache_neoforge.getRegionFile` lines 100–106:
  on a cache miss, it constructs `r.x.z.mca` and directly opens a new vanilla
  `RegionFile`. Linear's wrapper in Minecraft's cache cannot cover cold
  uncached regions via that path. Linear's RegionFileMixin only intercepts
  C2ME write/clear; it does not redirect this constructor/disk read.

Therefore Linear is NOT ready to deploy. Need a DH cold-region adapter,
format-aware controller/inventory, Chunky validation, and real
save/reopen/DH/player-flight testing before conversion. The format-level
experiment verifies raw NBT/timestamp bytes through compression only; no
Minecraft client/server was launched for it.

C2ME/Terrain Diffusion code review remains promising but not runtime-proven.
Do not conflate format compression results with a C2ME deployment gate.

Sources:
- https://restic.readthedocs.io/en/v0.16.4/045_working_with_repos.html
- https://restic.readthedocs.io/en/stable/060_forget.html
- https://github.com/memesgmm/Linear

Focused regression suite: 36 tests passed (backup, storage benchmark,
application operations and rollback). Existing unrelated uncommitted pack,
controller and documentation changes remain preserved; no release was
published by this storage review.
