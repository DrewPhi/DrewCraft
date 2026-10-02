# Linear verification execution — 2026-10-01

Owner authorized BP0–BP7, including isolated server-only tests and conditional
deployment if every safety gate passes. No client/account login is involved.

Production: 0.1.16-dev-local, Anvil, existing world unchanged except normal
generation/play. Launcher channel remains 0.1.16. No Linear promotion yet.

## BP0 progress

- Upstream source pinned at `aa693e448723a817504957eec2a9c923f7af7ef5`.
- Local maintenance patch tracked in `infra/linear-safety.patch`: validates all
  source/target payloads before deleting Anvil, preserves conflicting targets,
  aborts incomplete folder conversion, and prevents silent regeneration of
  corrupt Linear files when per-region backups are disabled.
- Conversion-only property aborts startup BEFORE world loading/ticking after
  conversion; its explicit completion marker, not exit code, is the result.
- NeoForge **21.1.250**, Java 21; isolated-test artifact SHA256
  `db54e76b0e2fa3e562e31e598a0ddfbe075a461428f15fdbf54b2faaa2da2866`
  (server-built, live chain + Java acceptance ran against it). Release builds
  verify provenance instead of whole-jar bytes: pinned commit + tracked patch,
  upstream unit tests on the exact packaged classes, and a structural check
  (`infra/check_linear_jar.py`: pinned 63-entry set, normalized timestamps).
  Whole-jar SHA pinning was abandoned because class bytecode drifts across JDK
  updates for identical sources; per-file integrity of the published release
  is hash-locked in `release-manifest.json` at pack time.
  Final jar includes upstream MIT copyright/license notice.
- Upstream plus real-region/converter tests: **19 passed**; additional focused
  strict-corruption/source-header tests pass, **6 converter safety tests** total.
- DH adapter `test build -PenableLinearAdapter` passes; raw jar SHA256
  `6d6cbbb765b75bb231ef399334472d129c35c2312345c51e41c410331060d41c`.
  Runtime packaging preserves ALL original embedded data resources.
- Backup hold added to both backup entrypoints; world-plus-application recovery
  keeps failed data aside and restores verified world before changing app.
- **64** focused Python backup/recovery/controller/inventory tests passed.
- Full Python suite passed **155** tests, including independent Anvil internal/
  external payload reader checks (after those tests were added).
- Actual runtime/recovery/incremental DH evidence still required; BP0 is not
  blanket compatibility approval.

## BP1 — snapshot and disposable restore

- Stopped empty production, took and checked a fresh snapshot, then resumed it.
- Sole pinned snapshot:
  `0bcaa1e802d6971f2eb64e9bff5f67767c1aac575ccab74d694ac62e70acd2d0`.
- Receipt `/srv/drewcraft/backups/20261001T062606762974Z.restic.json`.
- Hold `/srv/drewcraft/state/backup-hold.json`: future backups fail while pinned.
- Disposable baseline `/srv/drewcraft/linear-verification/baseline`.
- Initial restore interrupted by Ubuntu automatic service restarts at 06:35 UTC.
  Do NOT treat the initial partial restore as verified.
- Resumed service `drewcraft-linear-restore-resume` at 06:43 UTC; uses same
  snapshot and Restic `restore --verify` against ONLY disposable baseline.
- Require `baseline-verified.json` matching snapshot before preparing runtime.
- Production background pregeneration temporarily paused at 06:53 UTC to
  reduce verification I/O contention. Minecraft remains up/joinable. Resume
  `drewcraft-pregen` after maintenance tests; do not leave it paused on handoff.
- Intended runtime `/srv/drewcraft/linear-verification/runtime`, Minecraft
  `127.0.0.1:25585`, separate RCON `127.0.0.1:25586`, independent generated secret,
  no inherited symlinks, no production start script, independent models/cache.

## Continuation

### Runtime chain PASSED at 19:48:09 UTC

All seven runtime-chain stages passed, combining the original run's first three
stages with `drewcraft-linear-chain-retry2`'s final four. Final evidence:
`/srv/drewcraft/linear-verification/chain-evidence-chunky-retry2/state.json`.
Status is `RUNTIME_CHAIN_PASSED`; original evidence remains preserved.

- Existing FULL terrain survived Chunky with terrain NBT unchanged apart from
  the explicitly allowed tick timestamps.
- New scale-3 Terrain Diffusion generation took 810.101 seconds. The chunk was
  saved with FULL status; its native DH LOD passed in another 30.044 seconds,
  with all 3,844 interior columns populated and generation step 9.
- Region storage: 13,210,819,166 Anvil bytes versus 7,968,058,253 Linear bytes,
  a measured 39.69% reduction. Total-world sizes are not comparable because
  staging uses a fresh DH corpus. The resumed report's archived-DH byte count
  is zero because the archive lives in the original evidence directory, not
  the retry directory; this is not evidence that the original DH was empty.
- Truncated Linear data was rejected; the pinned baseline matched its hold.
  Railways baseline/converted errors both numbered 276, with no new entries.
- Isolated test server stopped; production `drewcraft` and `drewcraft-pregen`
  are both active again. No production conversion or launcher promotion.

The apparent stall was a misleading Chunky status: this version removes small
tasks from the active map after submitting asynchronous chunk loads, before
their callbacks finish. Its saved `cancelled=true` can also mean normal task
iteration completion. Neither signal alone proves cancellation or a stall;
require completion logs and saved terrain evidence before accepting a pass.

Remaining release gates are controller runtime handoff/checkpoint/player-pause
fixtures, controlled interrupted-save recovery, Java runtime latency acceptance,
and production migration/release publication. Seven chain passes do not fulfill
these additional gates. There is no reason to rerun the completed chain.

### Background runtime chain submitted at 18:49:16 UTC

Full comparison PASSED at 17:49:48 UTC: 2,735 regions, 994,754 raw chunk/entity/
POI payloads, and 827 checked non-region files with only the documented startup
metadata and SQLite sidecar exceptions. Elapsed 288.35 seconds. Converted server
reached RCON readiness; explicit save-all flushed every dimension, and its next
boot reached readiness again. SIGINT stop exits 130 despite prior successful
saving; the chain requests normal RCON shutdown instead.

`infra/linear_verification_chain.py` is submitted as `drewcraft-linear-chain`.
Preflight confirmed exact scale-3 world identity, localhost-only test ports,
a saved FULL cold-read fixture, a missing new-generation fixture, disk reserve,
and ready isolated server. The 52 controller/backup/recovery/inventory regression
tests passed; runner syntax compiles. No owner client/account login.

Stages run automatically: restart/save integrity; preserve the disposable
Overworld DH database and generate fresh native LODs; mutate one disposable
chunk and check its LOD update; Chunky existing FULL terrain preservation;
bounded new Terrain Diffusion generation; pinned baseline/corrupt-file checks
and storage/reader measurements; original-versus-converted Railways log review.
The new Chunky fixture may require costly neural inference. Each stage has an
explicit completion/evidence gate and timeout; storage reserve is checked while
waiting. Failures stop the chain rather than skipping to another gate.

Durable progress/results: `linear-verification/chain-evidence/state.json`.
Journal: `journalctl -u drewcraft-linear-chain`. Resubmission against existing
evidence is refused. On exit, stop the isolated generators/server and resume
production `drewcraft-pregen`. No live world mutation or channel promotion.

IMPORTANT: This chain does not yet cover every BP0–BP7 acceptance gate. It
records remaining controller runtime/checkpoint, controlled-save failure,
Java latency, and production cutover/release-publishing gates explicitly.
There is NO automatic deployment command chained after these tests. Format-aware
production migration and fresh snapshot rotation still need implementation;
do not use the fuel-only app rollback/deployment scripts for Linear.

The full comparison `drewcraft-linear-verify` reached the non-region checks
then failed at `level.dat` at 16:31:05 UTC. All region payload comparisons and
the missing/extra region-file checks preceded that failure. Its last progress
line reports 2,700 regions and 960,942 payloads; these are intermediate counts,
not the complete inventory. Do not claim the full verification passed.

Read-only typed NBT inspection proved `level.dat` differs ONLY at
`/Data/LastPlayed` (1790835965723 -> 1790854130747) and
`/fml/LoadingModList` (added Linear 1.3.3, no removed/changed existing mods).
Hash inspection of all 827 non-region files found exactly four differences:
`level.dat`, `level.dat_old`, `data/DistantHorizons.sqlite-shm`, and
`data/DistantHorizons.sqlite-wal`. No blanket exclusions were added to the
verifier. `level.dat_old` and the SQLite journals still require explanation.

The metadata diagnostic completed successfully. `level.dat_old` has the same
two startup-only differences as `level.dat`. The only other differing files
are DH `-shm`/`-wal` sidecars. Main SQLite bytes are identical; immutable SQL
comparison confirmed all schemas and rows identical, including 724,949
`ChunkHash` rows and 169,455 `FullData` rows. The first metadata run could not
open SQLite read-only without a shared-memory file; rerunning with SQLite
immutable mode completed cleanly. No data-loss difference was found.

The original full verifier completed all region comparisons but stopped at the
startup metadata difference. A tightened verifier now accepts only the forward
`LastPlayed` timestamp and a single Linear 1.3.3 loaded-mod-list addition in
`level.dat`/`level.dat_old`; it still compares every other metadata field and
all other persistent files exactly. DH sidecar differences are allowed only
alongside byte-identical main databases and the completed immutable SQL row
comparison above. Five focused verifier tests pass. Final full-world comparison
is running as `drewcraft-linear-verify`; require its final JSON success summary
before proceeding to ordinary ticking or the DH/Chunky runtime tests.

Conversion-only completed at 11:38:14 UTC with its explicit completion marker;
the maintenance process exited successfully before ticking. Production remains
Anvil and joinable; production background pregeneration is still paused.

Latest actual runtime evidence:

- Resumed baseline restore PASSED at 06:53:55 UTC.
- Original 0.1.16 Anvil application booted the restored world on localhost;
  ready at 08:15:04 UTC, RCON list confirmed zero players; clean stop followed.
- Original test world retained at `linear-verification/anvil-boot-world`.
- Pristine pre-ticking conversion copy prepared at 08:22:34 UTC.
- First conversion failed safely on our overly strict allocated-sector check:
  valid final entity sectors need not be padded to 4096 bytes. No evidence of
  corrupt live world. Corrected check validates actual payload and rounded
  allocation bound; explicit valid-unpadded and truly invalid-header tests pass.
- Retry `drewcraft-linear-convert-only` uses hash above. Require completion
  marker and independent comparison; do not infer success from process exit.

1. Wait for restore service; check result and verified marker. Never rerun the
   original baseline creator against existing staging/pinned backup.
2. Run isolated preparation, conversion-only server, independent full payload
   comparison (`infra/verify_region_conversion.py`) before ordinary ticking.
3. Follow BP2–BP7 in `LINEAR_VERIFICATION_PLAN.md`. Do not bypass failed gates.
4. Keep one snapshot pinned until recovery/acceptance; production remains Anvil
   until technical gates pass. No promise of zero corruption risk.
