# DrewCraft Current Development Breakpoint

## 2026-10-02 Linear 0.1.17-rc.1 DEPLOYED to production (Anvil→Linear cutover)

Production runs `0.1.17-rc.1` on Linear storage: stopped empty server, fresh
verified Restic snapshot `9255ec4d` (hold rotated to it), authorized migration,
activated the CI-built release, conversion-only boot completed with marker
`verified-before-world-load` (3,705 `.linear`, 0 `.mca`/`.mcc` retained),
normal boot reached RCON readiness, save-all flushes, no fallback files, no
mixin/corruption errors, pregen resumed. State `world-storage.json` is
`linear-v1`; backup stays pinned to the pre-cutover snapshot. Stale restic
lock from the 10-01 interrupted baseline (PID 266958) was found dead and
cleared before snapshotting. Launcher channel NOT yet republished: `live.json`
for 0.1.17-rc.1 exists only in the CI artifact; no stable pointer published.
Client update awaits the public-host publish decision (Pages path unresolved).

## 2026-10-02 Linear release candidate build — retry after corpus fix

First CI run of `0.1.17-rc.1` failed at the Linear step: 10/15 upstream tests
fail when the synthetic corpus was never generated (bare
`IllegalArgumentException` from `LinearTestSupport.resourcePath`). Same failure
was seen and resolved server-side by running upstream `generateCorpus` first.
Workflow runs `generateCorpus` in its own Gradle invocation (single-invocation
ordering left the corpus off the NeoForge test classpath) and verifies the
jar structurally (`infra/check_linear_jar.py`) instead of by whole-jar SHA:
class bytecode drifts across JDK updates for identical sources, which broke
two pin attempts. Provenance stays locked via commit rev-parse + tracked
patch + unit tests on the packaged classes; per-file hashes lock the release
at pack time. Exact-JDK pinning was rejected (setup-java cannot resolve the
verified build).

## 2026-10-01 Linear verification authorized — IN PROGRESS, not deployed

Latest check: the seven-stage runtime chain PASSED at 19:48:09 UTC. Final state
is `linear-verification/chain-evidence-chunky-retry2/state.json`; it reuses the
first three original passes and records the remaining four. New Terrain
Diffusion generation and native DH LOD output both passed. Measured region
compression saves 39.69%; fresh staging DH makes total-world sizes incomparable.
The apparent Chunky stall was asynchronous work still finishing, not an actual
cancelled generation job. Isolated test server stopped; production Minecraft
and idle pregeneration services are active. Do not rerun the completed chain.
Next: remaining controller runtime/pause/checkpoint, interrupted-save recovery,
Java latency and production migration/release gates listed in execution status.

See `LINEAR_EXECUTION_STATUS.md` and `LINEAR_VERIFICATION_PLAN.md` for exact
artifacts, pinned snapshot and continuation. Production/launcher remain
0.1.16 on Anvil. The sole pre-conversion snapshot is pinned; backups deliberately
fail while pinned. Isolated restore was interrupted by automatic host service
updates and is being resumed with verification. Do not overwrite staging or
run an old application against converted data. No client/account test.

Latest continuation: full stopped-world comparison PASSED (2,735 regions,
994,754 raw payloads; metadata differences explicitly inspected). Converted
runtime boot/save/reopen reached RCON readiness. `drewcraft-linear-chain` now
runs the isolated DH/Chunky/storage/log stages automatically; durable results
are `/srv/drewcraft/linear-verification/chain-evidence/state.json`. Check its
recorded failed/completed stage before resubmitting. No automatic production
conversion or release promotion is included; see execution status for gates.

## 2026-10-01 fuel-only 0.1.16 DEPLOYED and launcher promoted

Completed 06:03:27 UTC. Active server 0.1.16-dev-local, world revision 3,
RCON ready and joinable; server/pregen services active, Chunky resumed from
existing checkpoint. Shared `drewcraft-dev-pack/live.json` promoted after
health; installed launcher 0.1.10 auto-fetches matching client files, so no
new OS launcher binaries or website button changes needed.

Live all five MTS fuel categories confirmed lava-only 0.5. Vehicle-definition
capacity x2 hook included; existing absolute/default fuel not multiplied.
Gameplay range/handling acceptance remains owner-led. 114 Java tests pass
including real pinned-MTS schema test; 62 focused Python tests pass. Linear
upstream 15 tests plus actual-library five-region/5,120-chunk cold-reopen
roundtrip pass (16 tests total, 2 GB test heap). No dev Minecraft server/client.

One stopped-world pre-update max-compressed backup retained, verified repository
and exactly one snapshot: `39a7f78a5007922ce4218f707273d350d13a713a52074ef653d74270fa973ae5`;
receipt `/srv/drewcraft/backups/20261001T055949341224Z.restic.json`.
Prior application 0.1.13 retained for application rollback. 0.1.15 explicitly
withdrawn/unpromoted; final 0.1.16 jar preserves every baseline embedded data
resource byte-for-byte. All other immutable 0.1.13 assets reused.

Linear NOT installed, experimental DH hook NOT registered in shipping jar,
and draft Linear-aware controller/inventory NOT deployed. Existing Anvil world
unchanged except normal gameplay/generation. Remaining storage gates: actual
DH/Chunky/adapter runtime verification, interrupted conversion/recovery and
consistent full-world staging/restore proof. Cannot promise zero corruption
risk; code tests are not a substitute for these gates.

## 2026-10-01 corrected fuel-only rollout 0.1.16 — in progress

114 DrewCraft Java tests pass, including real pinned-MTS definition/hook-schema
verification; no development Minecraft server/client launched. Actual Linear
library write/cold-reopen test preserves all 5,120 copied real chunk payloads
byte-for-byte. Initial copied-region test exhausted default 512 MB test heap;
rerun at 2 GB passed. This does not prove DH/Chunky/runtime recovery.

Fuel-only release reuses immutable 0.1.13 assets except integration jar, fuel
config and fuel-policy JSON. ALL baseline embedded `data/` resources are
preserved byte-for-byte, keeping recipes, loot and worldgen. Experimental
Linear hook excluded by default; requires `-PenableLinearAdapter` to register.
Linear itself is NOT installed. Source and safe operational changes pushed.

0.1.15 staging was cancelled before activation when packaging review found
the raw compile lacked injected recipe resources. Previous application 0.1.13
was explicitly restored/resumed; launcher channel stayed 0.1.13. Do not promote
0.1.15. Corrected immutable target is 0.1.16-dev-local; manifest SHA256
`a91a93e33659e5d51ee3dac337d84bf8b0cae24d5748813669dafdc475c3e421`.
Deployment via `infra/deploy_fuel_patch.py` verifies resources against active
jar, takes stopped-world Restic backup, health-checks startup, resumes existing
pregeneration checkpoint. Promote shared launcher `live.json` ONLY after
successful deployment and confirmation of exact active version/fuel config.
No world reset/format conversion; gameplay acceptance remains owner-led.

## 2026-10-01 code-only fuel/Linear progress — NO LIVE DEPLOYMENT

Owner explicitly prohibited launching a development Minecraft/client/gameplay
test; respect this restriction. Waited five minutes for each requested build
check and continued code-only work. No Minecraft process was launched.

- Linear legacy jar compiled. Initial upstream test run failed 10/15 solely
  due to absent corpus resources. Ran upstream `generateCorpus`; subsequent
  `test jar` passed all 15 tests. Generated synthetic fixtures do not establish
  live-world integrity or full-stack compatibility.
- MTS `MtsFuelCapacityPolicy` + `MtsFuelCapacityMixin` doubles the shared JSON
  vehicle capacity once, after legacy normalization/before item construction.
  Scopes to JSONVehicle only; saved/default fuel untouched, Create/part storage
  unchanged. Four Java policy tests pass. Fuel config is 0.5, not shipped yet.
- `DhLinearRegionReaderMixin` routes DH's cold `read` through the SAME Minecraft
  RegionFileStorage when Linear is loaded, avoiding hardcoded Anvil fallback
  and separate stale region instances. Adapter compiles but actual mixin
  application/concurrency/player-flight behavior is not verified.
- `infra/region_inventory.py` validates Linear v1 headers/checksums/footer,
  bounded libzstd decompression and occupied slots. Controller recognizes
  `.linear` fingerprints; size inventory counts actual Linear slots. Duplicate
  Anvil/Linear coordinates fail closed instead of double-counting. Dependency
  must be installed alongside BOTH controller and world-size command.
- Draft DrewCraft `test build` successful; focused Python regressions pass.

Remaining: inspect/verify cold-reader and capacity hook injection against pinned
artifacts without launching a game, test actual saved-region corpus through
upstream APIs, validate conversion failure handling and retention pin through
cutover, prepare hash-recorded client/server release. Runtime save/reopen,
DH/Chunky/full-copy/flight acceptance gates are still unfulfilled and cannot
be claimed from code-only tests. No source commit/push, pack publication,
server restart, live format conversion or full-world copy was performed.

## 2026-10-01 fuel/Linear implementation started — NOT DEPLOYED

Owner authorized implementation and background builds, with later status check.
Lava config/policy/tests now target 0.5, but doubled-capacity integration is
not implemented yet: do not publish the partial fuel update. Pinned MTS 24.0.0
code inspection finds capacity used both in fuel-tank constructor and the
automatic-feed threshold; tank-only constructor scaling would miss that path.
Vehicle mass includes fuel mass, so handling must be tested too.

Linear Java-21 legacy source build/tests started in disposable checkout
`/tmp/drewcraft-linear-review`, commit aa693e448723a817504957eec2a9c923f7af7ef5:
`./gradlew test jar -PbuildTarget=legacy --no-daemon`.
Initial dependency setup/compilation running at handoff, exec session 10020.
This is upstream baseline validation, NOT the adapted DrewCraft stack and
NOT a converted-world test. Review Gradle test reports/build output before
claiming compatibility. DH adapter/controller support still need implementation.
Live world and server were not modified or restarted in this step.

## 2026-09-30 storage review / one-backup migration

Backup operations policy installed: one verified restore point, maximum
Restic compression. The one-off `drewcraft-backup-max.service` completed
successfully October 1 00:04:11 UTC (September 30 local), verified all 1,136
packs and removed the old repository and seven stale restore points. See
`docs/STORAGE_OPTIMIZATION_REVIEW.md` for measurements and exact resume checks.
Copied-region compaction saves 2.85%; actual Btrfs-Zstd saves 14.76% data
extents. Neither was applied to the live world. Linear-format compression
looks strong but installed DH's uncached reader explicitly opens `.mca`,
and our controller/inventory also require Anvil. Linear is not deployable
as-is. Minecraft and pregeneration remained active; no client rollout.

## 2026-09-30 world target raised to 150 GB

Live service and checkpoint now target 150,000,000,000 total world bytes,
including DH and all dimensions. Emergency cap is 155 GB; the 25 GB free-space
reserve is retained. Continuous mode does not use the old expansion-count
limit. Added a mid-job total-size check that pauses Chunky and DH at the
target, retains the interrupted phase/frontier, and remains joinable.
Increasing the target later resumes without treating the interrupted batch
as complete. Polling gives a small possible overshoot; no exact byte ceiling
is claimed. Player pause and ten-minute idle grace remain unchanged.
139 Python tests pass. Minecraft was not restarted. Backup:
`/srv/drewcraft/state/pregen-150gb-qju32rj6`.

IMPORTANT capacity blocker: filesystem has about 206.9 GB usable capacity,
70.6 GB used and 136.3 GB available while the world is about 20 GB. Keeping
the reserve can pause growth around 130 GB before the 150 GB target. Free
roughly 20 GB elsewhere or expand storage before promising 150 GB completion.
No backups or unrelated files were deleted, and no paid storage was ordered.

## 2026-09-30 canonical world-size command installed

Run `sudo drewcraft-world-size` after SSH login, or add `--json` for automation.
The read-only script `infra/world_size.py` is installed at
`/usr/local/bin/drewcraft-world-size`. It measures live files, includes DH and
all dimensions, and separately labels confirmed Chunky circle, unfinished
target, playable border, and irregular saved-region extents. It ignores old
inflated radius counters and empty region placeholders. Agent instructions
now require this command for world-size questions. 137 Python tests pass.
Verified live at 23:08 UTC: 19.43 GB total (6.81 GB DH included), confirmed
radius 6,144, in-progress 7,168, playable radius 5,824. No service restart.

## 2026-09-30 completed-terrain exploration boundary enabled

Owner requested players stay within pregenerated terrain. Controller now
enables the existing server mod's circular Overworld-only boundary using
continuousCompletedRadius minus a 320-block chunk-loading buffer; never the
in-progress selection radius. It expands only after fresh Chunky completion
evidence and survives controller restarts. Nether, End and Paradis are not
affected. Existing enforcement polls the boundary JSON and clamps players
back inside; it dismounts them on crossing, so it is not a physical aircraft
wall or an absolute global prohibition on every possible generation cause.
The buffer covers normal player chunk loading at current view-distance 10.
Installed server jar contains the boundary runtime classes. No Minecraft
restart or client update. 132 Python tests pass. Operational backup:
`/srv/drewcraft/state/pregen-boundary-6e8x1ibj`. At activation, Chunky had
completed radius 5,120 and the playable radius was 4,800 blocks.

## 2026-09-30 continuous Chunky expansion enabled

Owner requested ongoing idle terrain generation as well as DH catch-up.
Deployed the continuous mode at 22:59 UTC without restarting Minecraft.
`continuousChunky=true`, `dhOnly=false`; both services active, zero players,
and Chunky acknowledged a 1,024-block circle centered at (-1536,-1536).
Revalidate circles from the center, skipping saved completed chunks, rather
than seeding the completed frontier from inflated historical radii. After
each proven Chunky completion, run all pending saved-region DH jobs before
expanding the radius by another 1,024 blocks. Missing tasks trigger resume,
not advancement; fresh 100% task-finished evidence is required. Player pause
and 600-second empty grace remain. Checkpoints survive controller restarts.

The 50 GB world target stops further expansion, while DH maintenance keeps
running. Existing 55 GB emergency cap, 25 GB free-space reserve and maximum
radius remain hard safety limits. No terrain deletion, client update, or
Minecraft restart. Old controller/state backup:
`/srv/drewcraft/state/continuous-pregen-vdyxr99b`.
130 Python tests pass including four continuous-cycle behavior tests.
Next check: confirm real completion advances continuousCompletedRadius and
that the controller alternates terrain batches with DH delta jobs. Do not
report legacy activeRadius/chunkyRadius as completed generation evidence.

## 2026-09-30 DH frontier and flight delivery verification

At 22:49 UTC the live idle controller had completed 12 native jobs and all
895 nonempty saved Overworld region files matched its maintenance baseline.
New Chunky-saved regions are queued beyond the original catch-up radius;
there is no fixed-radius cutoff for incremental maintenance. Two additional
regression tests cover all-direction frontier growth and empty placeholders;
126 Python tests pass. No runtime change/restart was needed for this request.
Independent per-column LOD coverage remains unverified.

Correction: an ad-hoc inventory counted empty/short region placeholders as
chunks. The corrected stored-chunk extents are X -12,464..8,415 and
Z -11,216..7,647, not the larger placeholder bounds or legacy 130,048 radius.

Live MTS 24.0.0 aircraft/car speed factors are 0.35. Its physical displacement
is `motion * speedFactor` each tick; at 20 TPS actual horizontal blocks/second
are `20 * speedFactor * hypot(motion.x, motion.z)`. Aircraft top speed is not
a single pack constant: engine/propeller choices, mass, drag, altitude and
flight attitude affect it. No live flight-speed benchmark was performed.
With view-distance 10, a conservative square-window estimate for fresh full
chunk delivery is `21 * (abs(vx) + abs(vz)) / 16` chunks/second per pilot.
At actual speeds 20/40/60 blocks/sec this is about 26–37/53–74/79–111 chunks/sec
depending on heading, before startup bursts and safety headroom. Live Chunk
Sending caps are 15 chunks/player/tick and 80 globally, with client desired
rate multiplied by 0.8. Those are ceilings, not measured throughput. DH LODs
do not substitute for collision chunks. Flight profiling remains needed
before blaming or increasing the caps; no chunk-send settings were changed.

## 2026-09-30 incremental DH maintenance deployed

The idle controller is deployed on Oracle; Minecraft was left running. It now
starts one native catch-up pass from (-1536,-1536) over real saved-region bounds
(11,328-block radius, including the new western terrain), then queues only new
or changed region groups. Quiet terrain causes no repeated whole-world pass.
Region snapshots and pending/active jobs persist across player pauses/restarts;
changes during a pass remain pending for a later check. Player polling is 10
seconds, idle grace remains 600 seconds, and idle region-change checks are 60
seconds. CHUNKS_ONLY/PRE_EXISTING_ONLY and DH's native live chunk hashing remain.
124 Python tests pass, including six maintenance behavior tests. At 17:31 UTC,
the live first scan was running at 83.9%, with zero players and both services
active. New outer terrain is slower than cached sections (latest native ETA
about 15 minutes; early estimates were much shorter). Health remains joinable.
Completion is not yet verified. Old script/state backup:
`/srv/drewcraft/state/dh-incremental-ZSfzin`.

Correction to earlier coverage interpretation: native DH generation can save
LODs without the ChunkHash record used by live chunk updates. Missing hash rows
alone do not prove LOD holes; independent per-column coverage remains unverified.
The fuel changes below remain local and unshipped.

## 2026-09-30 lava-only fuel and flight chunk follow-up

The source pack now configures every MTS fuel category (gasoline, avgas,
diesel, furnace, and brewing stand) to accept only lava at potency 0.1. This
change is local and unshipped; live 0.1.13 still has the prior bioethanol
mapping until a verified client/server pack release is deployed. No world
reset is needed.

Owner reported plane travel with slow/missing full chunks and DH visual glitches
after roughly 1–3k blocks. Live read-only status: server ready/joinable,
world about 19.37 GB, pregeneration controller active in `dhOnly=true` /
`phase=complete`, Chunky idle (`No tasks running`), and periodic DH passes
completing. The stored Chunky radius of 130,048 blocks is historical state,
not verified coverage. DH's saved catch-up radius is 10,304 blocks around
(-1536,-1536); `coverageVerified=false`. Region-header inventory previously
found existing terrain across X -701..525 and Z -701..477 region-chunk
coordinates, but this does not prove every chunk inside that footprint is
present or that full chunks can be delivered as fast as a plane travels.
Need the incident's exact start/end coordinates and timestamp/client log to
separate absent terrain from server chunk-send/terrain-generation delay and
client/DH rendering behavior. Do not report complete Chunky or DH coverage yet.

## 2026-09-28 fuel balance rollout

Pack 0.1.13-dev-local is active on the Oracle server and promoted to the
shared launcher channel. The public health endpoint reports ready and joinable
for the existing `drewcraft-production` world, revision 3. The live MTS config
sets lava potency to 0.1 and Create bioethanol to 1.0 for gasoline and avgas;
other fuel categories were unchanged. The update took a pre-update restic
snapshot (`20260928T220040881108Z.restic.json`). The first activation rolled
back because its readiness check ran before Minecraft finished starting; the
retry succeeded after allowing normal startup time. In-game fuel consumption
remains for owner acceptance.

## 2026-09-27 quality-of-life rollout

Pack 0.1.12-dev-local is published, active on the Oracle server, and promoted
to the shared launcher channel. The public health endpoint reports ready and
joinable for `drewcraft-production` revision 3. The update kept the existing
world (~18 GB), dock, player data, and DH/pregeneration checkpoint; no live
world was recreated. Jade and AppleSkin are present server-side; Sodium,
LambDynamicLights, Mouse Tweaks, and Nemo's Inventory Sorting are client-only.
The pinned full pack assembled and verified locally (223 client files, 218
server files); 117 Python tests and the Gradle test build passed. The existing
launcher 0.1.10 meets the release's minimum version and should auto-fetch the
new pack. Owner-led in-game acceptance on the actual client platforms remains
open, especially Sodium/Aeronautics/DH rendering and the dynamic-light toggle.

## 2026-09-27 map persistence rollout

Launcher 0.1.10 and pack 0.1.11-dev-local are published and deployed. The shared
client channel matches the healthy, joinable server. World Map is client-only;
map/waypoint folders now survive launcher updates and repairs. Existing world,
dock, welcome book and DH-only catch-up state were preserved. See
`MAP_PERSISTENCE.md` for exact release/backup evidence and remaining owner-led
client acceptance. No terrain expansion was resumed.

## 2026-09-26 owner-directed AOT rollout

Release 0.1.10-dev-local uses `v1_2_paradis_candidate`, extending V1.1 with
Danny's AOT and its exact compatibility dependencies. See `AOT_INTEGRATION.md`
for evidence, the administrator dock command and explicitly unverified gameplay
checks. The owner requested stopping local interactive testing and deploying
for their own real-server acceptance. Preserve world revision 3; no world reset
or automatic dock placement is authorized. Release assets are versioned; promote
the launcher's `drewcraft-dev-pack/live.json` only after server activation/health.

The older breakpoint history below is retained; it is not current release state.

**Updated:** 2026-09-19
**Last completed breakpoint:** **BP-V1A — focused profile convergence**
**Current breakpoint:** **BP-V1B — server and gameplay proof**

## Decision

V1 has been deliberately narrowed to fun, reliable multiplayer survival: Terrain Diffusion, Distant Horizons, MTS vehicles/planes, the compatible Create stack (including Create: Radars and the NTGL/Gunsmithing firearm stack), and the complete upstream WDA dungeon set. Weather and DrewCraft-specific radar/strategic/endgame systems are post-V1.

## BP-V1A implementation

- Added authoritative `v1_survival_exploration` and lean `v1_survival_core` profiles.
- Kept the selected compatible Create family and excluded the known-incompatible CBC Firepower Components release.
- Included WDA through the existing narrow dependency override and restored its complete upstream structure set.
- Removed Atmosphere, clouds, seasons, Covenant, armies, sources, sieges, and herds from the shipping dependency chain.
- Defaulted DrewCraft's deferred weather/radar/strategic feature flags off while retaining ordinary upstream Create: Radars behavior.
- Repointed dev release, RC, server smoke, full-profile verification, validation, and hash workflows to the shipping profile.
- Updated website messaging while retaining stable Windows/Mac/Linux launcher aliases.
- Retired the Covenant resource pack from V1 release injection; launcher 0.1.8 removes only that formerly managed pack while preserving user resource packs.
- Rebased V1 documentation and moved the larger design into `docs/FURTHER_IDEAS.md`.

## Local evidence

- Shipping profile resolves deterministically to 35 dependencies; the only unresolved provider identity is the expected pinned Terrain Diffusion source build.
- The resolved graph contains every intended Create/MTS/WDA component and none of the deferred weather/Covenant/strategic dependencies.
- `/usr/bin/python3 -m pytest -q`: **92 passed**.
- Python bytecode compilation, YAML parsing, and `git diff --check`: passed.
- Pinned Gradle 9.2.1 `test`: **BUILD SUCCESSFUL**.

## BP-V1A remote evidence

- Commit `3ac388a` is pushed to `main`.
- Pack manifests, provider hashes, DrewCraft mod CI, full V1 profile verification, source-structure smoke, BP8 convergence, and live-pack publication passed.
- The published evidence names `v1_survival_core` and `v1_survival_exploration`; the release manifest contains no Covenant or weather paths.
- Launcher **0.1.8** was published as GitHub's latest release with the exact Windows EXE, Apple Silicon DMG, and Linux DEB filenames used by the website.
- The existing website buttons therefore download 0.1.8, and existing launchers converge through the corrected `live.json`.
- The focused pack is versioned `0.1.3-dev-local`, requires launcher 0.1.8, and carries the OCI server address plus health endpoint so DrewCraft launches directly into the matching server. This revision adds a temporary Overworld-only generated-area boundary without constraining Nether or End.

## BP-V1B

**Correction:** The prior fresh-world server smoke reached `Done` but did not prove Terrain Diffusion world selection. On 2026-09-19, the live `server.properties` was found to contain `level-type=minecraft\\:normal`, and the saved Overworld uses Minecraft's normal biome source and noise settings. Thus the existing generated world is not a Terrain Diffusion world. Do not reuse the old worldgen claim as evidence.

The current deployment target is `0.1.7-dev-local` / world revision 3. It pins JEI, uses a DrewCraft-owned dedicated-server preset backed by the upstream Terrain Diffusion scale-3 dimension, seeds the upstream per-world scale SavedData before first boot, restores full inference-window overlap, and triples the previous WDA major/minor spacing. A guard checks the saved generator and scale before the pregen controller can generate chunks. The controller centers the new world at its actual saved spawn. Launcher 0.1.9 adds the server to the multiplayer list and preserves user entries; client DH radius defaults to 32 on new installs.

The first attempted release (`0.1.6-dev-local` / revision 2) exposed a packaging mistake: WDA placement JSON was copied into the pack root rather than a loadable world datapack. The server was stopped before any region files were generated. Revision 3 ships the overrides in `datapacks/drewcraft-structures` and installs them into the world before first boot. Do not treat revision 2 as a completed world-generation test.

The owner authorized deleting the old production world without a backup. It and the tiny revision-2 placeholder have been deleted; no reset backup was made. This is a one-time world reset; normal future application updates retain the existing backup policy. Release `0.1.7-dev-local` is staged and active on the Oracle VM. On the fresh revision-3 world, `worldgen_guard.py` verifies the saved Terrain Diffusion generator and World Scale 3, and `level.dat` lists `file/drewcraft-structures` among enabled datapacks. Both the server and idle-only pregeneration controller are active; first spawn generation was still running at the last check, so readiness and gameplay remain unverified. User visual verification is next; no separate preview world is required.
