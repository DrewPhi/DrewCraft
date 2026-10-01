# Existing Overworld DH catch-up — 2026-09-27

## Continuous terrain expansion — 2026-09-30

Owner re-enabled Chunky expansion at 22:59 UTC. Continuous mode revalidates
saved circles from spawn, then expands in 1,024-block radius increments.
Each increment requires a fresh Chunky 100% task-finished message before
advancing the completed frontier. A missing task is resumed, not counted as
complete. Between batches DH processes all pending region changes, including
new regions outside the original catch-up radius. Jobs alternate rather than
compete concurrently. Both pause for players and resume after 600 seconds
empty. At the retained 50 GB world target expansion stops but DH maintenance
continues; 55 GB emergency cap and 25 GB free-space reserve are unchanged.
`continuousCompletedRadius`, not historical radius counters, tracks the new
verified-by-task frontier. Initial live start acknowledged radius 1,024;
existing terrain and Minecraft service were preserved.

## Incremental maintenance — 2026-09-30

Live follow-up at 22:49 UTC: controller active, initial catch-up plus eleven
incremental jobs complete, and all 895 nonempty saved region files match the
baseline (zero dirty regions). An additional 1,251 empty/short region
placeholders are not saved terrain. Valid region location entries total
748,237; actual saved chunk extents are X -12,464..8,415 and Z -11,216..7,647
blocks. The 11,328-block catch-up radius around (-1536,-1536) encloses this
footprint. New Chunky-saved regions beyond that initial radius are queued too;
the original radius is not a maintenance boundary. Added regression tests
cover growth in all four directions and exclusion of empty placeholders.
No client or Minecraft restart is needed: this behavior is already deployed.
This confirms the maintenance target and checkpoint, not independent LOD
column completeness.

The controller now computes catch-up bounds from saved Overworld region files,
so newly explored terrain beyond the old 10,304-block scan is included. On
migration it makes one native center-out catch-up pass. After native completion,
it saves the region mtime/size snapshot taken before the pass. While empty, it
checks those fingerprints every 60 seconds and queues only new/changed regions
in 2,048-block squares, ordered nearest spawn first. A quiet world starts no
additional native pass. Persistent active/pending jobs survive restart and
player pauses; changes during processing remain dirty for a follow-up job.
Player count is checked every 10 seconds; jobs resume after 600 seconds empty.
Normal DH live block/biome hashes handle player edits without rebuilding
unchanged chunks. The existing CHUNKS_ONLY/PRE_EXISTING_ONLY settings remain.

Native pregen skips already generated LOD sections. Source inspection of the
exact DH 3.3.1 artifact shows native generation can save LODs without creating
the same ChunkHash records used by live chunk updates. Therefore the missing
hash counts from the 2026-09-30 audit **do not independently prove LOD holes**.
Keep `coverageVerified=false` until actual per-column LOD data is audited;
successful native completion is operational evidence, not a visual proof.
Region diffs scope background catch-up work; they do not force replacement of
completed LOD sections or replace DH's normal live update handling.

Six behavioral tests cover real-bound migration, unchanged-world idling,
changes during processing/new regions, database replacement, player pause and
resume, restart preservation, and targeted job centers.

Owner requested LOD coverage of the entire existing Overworld, without more
terrain expansion. Server-only operational change; no client release required.

## Findings

- DH 3.3.1 uses `generation.chunkMode`, not `generation.mode`. The previous
  controller did not reject the resulting `Incorrect argument` response.
- Its running status is `Generated radius: ...`, which the old parser missed.
  Consequently the recorded DH radius was not evidence of completed coverage.
- Runtime was `SURFACE_THEN_CHUNKS` / `FEATURES`. Catch-up now uses
  `CHUNKS_ONLY` / `PRE_EXISTING_ONLY`, reading saved terrain rather than predicting
  surface terrain or generating new chunks.
- Region-header inventory: 745,849 stored chunk entries, X -701..525 and
  Z -701..477 (chunk coordinates; entries may include partial chunks).
  Old controller radii around 130,000 blocks do NOT describe verified terrain.

## Applied

- Preserve terrain, LOD database, 125-expansion limit and existing size limits.
- Back up controller/state under
  `/srv/drewcraft/state/dh-catchup-20260927T163906Z`.
- Restart only the pregen controller, not Minecraft.
- Set `dhOnly=true`, `phaseAfterDh=complete`, and `dhOnlyRadius=10304` blocks
  around (-1536,-1536). This square native-DH scan encloses every currently
  existing Overworld region plus a 64-block margin. It skips absent terrain.
- Keep the player-join stop and 600-second idle grace behavior. Completion
  leaves terrain expansion disabled; hourly DH refreshes use the same bounds.
- Validate command responses and recognize real DH progress. Require a new
  `Pregen is complete` log event before advancing the completion checkpoint;
  a missing task alone is no longer success. Restart an interrupted pass.
- Retain `coverageVerified=false`: a successful native pass is not an independent
  per-column database audit, and native retrieval failures must still be checked.

## Evidence / follow-up

26 focused Python tests passed. Live at 16:39 UTC: generation settings accepted,
DH reported 3% / 644-chunk radius, approximately 3m13s remaining (early estimate),
and Chunky reported no tasks running. Completion was not waited for.

Next status check: confirm the native completion message, no retrieval failures,
and controller transition to `complete`. Inspect database coverage if holes remain.
If players explore beyond these bounds, enlarge the DH-only scan based on new
region files; do not use the historical Chunky/DH radius counters as coverage.

Follow-up: the controller recorded native pass completion at 16:47:07 UTC and
`phase=complete`, `dhRadius=10304`. This checkpoint survived the 0.1.11 deployment;
maintenance service is active. Independent per-column coverage remains unverified.
