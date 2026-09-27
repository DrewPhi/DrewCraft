# Existing Overworld DH catch-up — 2026-09-27

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
