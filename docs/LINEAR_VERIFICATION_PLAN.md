# Linear verification: steps and breakpoints

Status: EXECUTION AUTHORIZED on 2026-10-01, including conditional deployment
after all gates pass. Production remains Anvil on pack 0.1.16. No world reset.
The owner authorized isolated server-only tests. No client/account login,
rendering or manual gameplay is required for the core safety gates.

Planning estimate: 1–3 hours if integration works, not a promise. Full-copy
conversion/restore, Terrain Diffusion inference and fixes may take longer.
Record actual durations at each breakpoint before estimating production downtime.

## BP0 — code and artifact safety

Already proven: builds/unit tests, real pinned-MTS schema, and actual Linear
library write/cold-reopen equality for 5,120 copied chunk payloads. Fuel update
is shipped; it is not waiting for Linear.

Remaining code checks:

- Pin/hash the Java-21 Linear artifact and adapter sources for NeoForge 21.1.250.
- Inspect/test conversion before deleting Anvil sources. Upstream converter
  currently deletes an `.mca` if the matching `.linear` already exists: file
  existence alone is NOT proof of a complete equivalent conversion. Harden
  this path to validate/reopen/compare source payloads, or fail and retain both.
- Test malformed headers, oversized/external `.mcc` chunks, missing regions,
  partial chunks and mixed/interrupted conversions. Preserve each chunk's
  status; occupied header slots are not proof of complete generation.
- Add a backup hold/pin and format-aware deployment transaction. The current
  serverctl rollback restores APPLICATION ONLY and cannot undo conversion.
  Prevent automatic backups from replacing the sole pre-conversion restore
  point until acceptance; reject a backup attempt while it is pinned.
- Ensure Linear's own per-region backup/recompression settings do not silently
  create an additional full-world backup or collide with controller scheduling.

Pass: tests/evidence recorded; unsafe deletion and rollback paths addressed.
Stop: any unexplained data mutation, unverified deletion or unsafe rollback.
Resume artifact: source commit, jar hashes, test reports and exact commands.

## BP1 — consistent staging baseline and isolation

- Measure CURRENT world, DH, backup and free space; reserve at least 25 GB.
  Budget a restore baseline plus converted copy and any temporary native data.
  Abort if the budget does not fit; do not add paid disk/compute silently.
- Plan a short maintenance window: pause generators, stop/save the server,
  create and verify one fresh consistent Restic snapshot, then resume production.
  Do not copy changing `.mca`/SQLite files as the final integrity baseline.
- Restore to disposable staging. Verify restored files against snapshot hashes.
  Keep the one snapshot; temporary staging copies are not additional retained
  backup histories. Do not replace this snapshot during this test run.
- Give the test server separate directories, ports, RCON secret, state and
  service. Bind to localhost; prevent real players joining. No production
  symlinks, credentials, release/channel pointers or persistent paths.
- Establish resource limits; pause/limit test load if production needs resources.
  Disable automatic pregeneration in staging until deliberately exercised.

Pass: consistent restored baseline, measured capacity, isolation verified.
Stop: inadequate space or any test path that resolves into production.
Resume artifact: snapshot ID, baseline hash inventory, test paths/ports/service.

## BP2 — actual converter and restart integrity

- First exercise representative copied regions through the actual conversion
  path, not just our format-layout compressor or library write helper.
- Include mountains, coast/ocean, structures/builds, block entities, entities,
  POI, partial regions and external chunks where present.
- Before normal ticking, compare occupied slots, decompressed NBT and chunk
  statuses against the Anvil baseline. Document intentional storage-header
  timestamp changes separately; never excuse block/inventory loss as metadata.
- Start/stop/reopen the isolated server twice. Check mixin application, config,
  reads/saves and absence of newly created empty Anvil fallbacks.

Pass: converter equality and server restart checks pass with no unexplained loss.
Stop: dropped chunks/entities, invalid saves, adapter errors or fallback files.
Resume artifact: conversion log, before/after inventories, payload comparisons.

## BP3 — DH cold reads and incremental updates

- Keep staging DH data separate. Select known saved terrain outside warm caches.
- Run native DH `CHUNKS_ONLY` / `PRE_EXISTING_ONLY`; verify LOD output represents
  the selected real chunks, not merely successful command completion.
- Verify the reader uses the shared Linear-backed storage and reads dirty
  in-memory data consistently without creating `.mca` placeholders.
- Modify a disposable test chunk through a controlled server-side test, save,
  and verify changed-region catch-up refreshes its LOD. Verify unchanged regions
  do not continuously queue full-world regeneration. No production edits.

Pass: cold and changed-chunk LOD checks pass; no unintended terrain generation.
Stop: missing/empty LOD coverage, stale reads, incorrect coordinate accounting.
Resume artifact: tested coordinates, LOD evidence, controller queue/state.

## BP4 — Chunky, coordination and limits

- Prove Chunky skips existing FULL chunks in converted terrain; partial chunks
  are handled correctly, not incorrectly counted as complete.
- Generate a deliberately bounded small new area on the staging world using
  the SAME Terrain Diffusion generator/scale, then save/reopen and inspect it.
  This may incur one expensive inference tile; do not substitute vanilla.
- Verify idle Chunky → DH handoff, persisted checkpoints and restart recovery.
- Test player-count pause/resume with a code-controlled test fixture or protocol
  harness, not the owner's account/client. If unavailable, record it as a later
  production gameplay check rather than claiming it tested.
- Verify storage accounting includes every dimension/DH, and simulated budget/
  reserve exhaustion pauses both jobs. Test border advancement only after real
  completion evidence. No change to live target/border during these tests.

Pass: skip/new-generation/coordination/limit assertions pass.
Stop: duplicate generation, skipped missing terrain or lost checkpoint progress.
Resume artifact: task logs, state transitions, inventory and size reports.

## BP5 — failure and restore drill

- On disposable copies only, interrupt conversion and a save at controlled
  points; test corrupt/incomplete Linear data and near-budget exhaustion.
- Verify source preservation/recovery rules; do not erase the evidence on error.
- Restore the retained Anvil snapshot into an EMPTY disposable target, verify
  contents, and start it using the original application. Never restore over
  the live running world or run the old application against converted files.
- Prove the backup hold prevents retention from deleting the needed snapshot.

Pass: restored baseline boots, verified data matches, failure cases fail safely.
Stop: unrecoverable changes, unsafe automatic restart/rollback, missing backup.
Resume artifact: recovery logs, restore checksums, proven rollback commands.

## BP6 — full-world acceptance and go/no-go

- Convert the consistent full-world staging copy. Validate ALL dimensions
  (Overworld, Nether, End, Paradis), player files, builds, containers and portals.
- Compare conversion-only NBT against baseline; separately evaluate legitimate
  normal ticking changes during subsequent server tests.
- Measure terrain/entity/POI, DH and TOTAL bytes separately; measure memory,
  save/reopen latency and cold sequential chunk reads along a flight route.
  A script-driven chunk-read workload can flag stalls without a rendered client.
- Choose moderate hot-path compression; validate any idle recompression rather
  than enabling maximum compression indiscriminately.

Pass: safety gates passed, measured storage benefit worthwhile, no substantial
server read/save regression, precise deployment/restore instructions ready.
Stop: incompatibility or latency problems. Production stays Anvil.
Resume artifact: full report, measured conversion/downtime estimate and decision.

This is the deployment decision breakpoint. A separate human playtest is not
required to prove conversion integrity. Visual LOD glitches, real network
streaming/aircraft experience and client-specific issues cannot be certified
by code-only checks; report these as remaining owner gameplay acceptance.

## BP7 — production cutover (separate approval)

- Build immutable matching artifacts/manifests; keep existing world identity.
- Pause generators and stop consistently. Because production has advanced since
  BP1, create/verify a FRESH single pre-cutover snapshot and pin it. The staging
  snapshot can be superseded only once this replacement is verified.
- Convert the CURRENT production world using the tested transaction. Do not
  replace it with an older staging world and lose intervening gameplay.
- Start, check cold reads/saves/logs and health, deploy compatible controller/
  inventory together, then resume idle pregeneration.
- Publish launcher/channel changes only after referenced artifacts and healthy
  server exist; clients receive only what the tested integration requires.
- On failure stop immediately and follow the proven WORLD-plus-application
  recovery procedure. A restore loses post-snapshot writes; disclose this risk.
- After technical acceptance/owner check, remove disposable test copies, unpin
  backup policy and resume one-backup retention. Never remove the sole restore
  point before a verified replacement exists.

Pass: joinable healthy release, generators resumed, one protected restore point.
Owner gameplay follow-up: joins, aircraft travel, LOD visuals, containers and
Paradis return portal. No claim of zero risk even after tests pass.

## Check-in convention

At each breakpoint report: PASS/FAIL/RUNNING, evidence paths, current production
status, next step and revised ETA. Save state before ending a turn. Long builds
and conversions may run as isolated background jobs; no need to watch output
continuously. Never advance solely because a process exited or an ETA elapsed.
