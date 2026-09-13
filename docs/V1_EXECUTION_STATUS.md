# DrewCraft V1 Execution Status

**Last updated:** 2026-09-12  
**Current phase:** **BP1-BP8 complete -> BP9 cross-system scale/failure/recovery hardening next**  
**Current breakpoint handoff:** `docs/CURRENT_BREAKPOINT.md`  
**Breakpoint protocol:** `docs/DEVELOPMENT_BREAKPOINTS.md`

This is the live execution overlay for DrewCraft V1. `docs/CURRENT_BREAKPOINT.md` is the exact stop/resume handoff; `docs/V1_REMAINING_EXECUTION_PLAN.md` remains the detailed path to `1.0.0`.

## Certified platform

- Minecraft **1.21.1**
- NeoForge **21.1.250**
- Java **21**
- external candidate stack: **34 dependencies = 33 exact provider artifacts + one exact Terrain Diffusion Plus source build**
- provider hashes: **34724313143**
- manifest graph: **34724313201**
- dedicated-server baseline: **34704011609**

Environment/aviation/radar integration is implemented at development scope; final representative world/client acceptance belongs to BP9/BP10.

## Completed strategic/gameplay breakpoints

- **BP1 — PASS:** persistent groups + bounded coarse simulation.
- **BP2 — PASS:** coarse cached routing/ETA + 10,000-block unloaded restart proof. Evidence **34726835776**, **34726857058**.
- **BP3 — PASS:** transactional materialization, bounded waves, idempotent casualties, restart/concurrency proof. Evidence **34727614866**, **34727505486**.
- **BP4 — PASS:** persistent hostile sources, Source Core mining/explosion clearing, launch/clear race safety. Evidence **34728862438**, polish **34729284337**.
- **BP5 — PASS:** JSON-driven factions/roles/missions, exact source debits, non-omniscient targeting, bounded 256-unit army proof. Evidence **34729884759**, **34729684064**, **34729641645**.
- **BP6 — PASS:** path-first bounded siege, protected/decorative safety, no distant siege planning. Evidence **34730303373**, runtime compile **34730277755**.
- **BP7 — PASS:** explicit strategic herds, unloaded migration, bounded materialization, independent herd kill switch, no global spawn/spawner interception. Evidence **34730837899**.

Central invariant remains:

> **Keep the world abstract while nobody is looking; materialize only what players can interact with; cache expensive decisions; persist every important consequence.**

## BP8 — production/deployment/release/launcher convergence — PASS at implementation/CI scope

Detailed contract: `docs/BP8_RELEASE_OPERATIONS.md`.

### Release truth

- one immutable `release-manifest.json` drives both client and server;
- `live.json` is only the stable-channel pointer;
- common/client/server trees derive from one verified layout;
- exact path/side/size/SHA/acquisition identity for managed files;
- repository-built DrewCraft mod is explicitly injected/hash-recorded into both sides;
- provider artifacts are matched by locked SHA and use official CurseForge/Modrinth acquisition URLs where available;
- DrewCraft publish payload omits provider files instead of blindly rehosting them.

### Server operations

- exact SHA-verified NeoForge installer produces a complete immutable server runtime (`run.sh`, libraries, verified mods/config);
- application releases exclude persistent `world`/`logs`;
- server updater stages/verifies, checks world compatibility, backs up, atomically activates, health-checks, and restores application identity on rollout failure;
- application rollback never blindly rolls an authoritative world backward;
- clean separate-root backup/restore proof is automated.

### Production-world machinery

- world identity/revision + `generationPackVersion = drewcraft-worldgen-1` are explicit;
- final seed/radius are deliberately **not yet frozen**;
- fail-closed candidate lock requires measured generation/disk/archive/backup/restore/restart evidence, verified clean restore, archive SHA, terrain review, source distribution, herd-corridor review, and matching generation identity;
- offline structure indexing produces exact source/core records; generic core rule is horizontal center -> nearest accessible interior floor;
- production runtime imports exact source/herd records without global scans or forced chunk loading;
- world bundle tooling stamps, hashes, archives, validates, and clean-restores identity.

### Host/deployment contract

- initial fixed benchmark target: Ubuntu ARM64, OCI A1, 2 OCPU / 12 GB, no autoscaling;
- non-root service, systemd Minecraft + read-only health endpoint, application/persistent separation;
- native ARM64 CI compiles/tests DrewCraft and proves a production jar exists;
- real representative A1 gameplay benchmark remains BP9 and must conclude `PASS` or explicit `MIGRATE`.

### Friend launcher

- exact Java 21 + Prism archives pinned by URL/size/SHA for Windows x86-64 and Apple Silicon;
- real Prism instance metadata declares exact MC 1.21.1 + NeoForge 21.1.250;
- staged/hash-verified updates and repair;
- preserves explicitly user-owned screenshots/resourcepacks/shaderpacks/saves/options;
- server pack/protocol/health check before launch;
- native CI produces **`DrewCraft-Windows.exe`** and **`DrewCraft-macOS.dmg`**;
- Apple production signing/notarization remains a final RC distribution gate.

### Reproducible release candidate

`.github/workflows/release-candidate-build.yml` can rebuild Terrain Diffusion from the exact pinned source ref, rebuild the exact external profile, compile/inject DrewCraft, install exact NeoForge, assemble the complete server app, generate a provider-aware immutable release manifest, independently verify client/server views, and create the publishable DrewCraft-owned payload without a developer-local zip step.

### BP8 CI

`bp8-convergence.yml` has five gates:

1. every `test_bp8_*.py` + workflow/JSON parsing;
2. real NeoForge `--installServer` + complete server application assembly;
3. native ARM64 DrewCraft build/test + production JAR;
4. real locked Java/Prism + Windows EXE;
5. real locked Java/Prism + Apple Silicon app/DMG.

The exact final run/head is recorded in `docs/CURRENT_BREAKPOINT.md` after the BP8 branch gate finishes.

## Honest BP8 boundary / BP9 evidence

BP8 does **not** claim the following real-world facts yet:

- a final Terrain Diffusion seed/radius or final world archive;
- final visual world/source/herd geography approval;
- a representative A1 server workload benchmark;
- an actual independent/off-host production backup copy/recovery drill;
- real nontechnical friend-machine Windows/macOS install/login/update/join observation;
- Apple Developer notarization;
- public stable release binaries/live pointer.

Those are BP9/BP10 acceptance gates. The machinery to make them reproducible/fail-closed is now in place.

## Remaining critical path

```text
DONE BP1 persistence + coarse scheduler
DONE BP2 routing + ETA + unloaded travel
DONE BP3 materialization + casualties
DONE BP4 hostile sources + permanent clearing
DONE BP5 factions / patrols / hordes / raids / armies / reinforcements
DONE BP6 path-first bounded siege
DONE BP7 strategic herds + local-spawn coexistence
DONE BP8 production/deployment/release/launcher convergence
→ NEXT BP9 cross-system scale / failure / recovery / performance hardening
→ BP10 exact RC + hard acceptance
→ 1.0.0
```

## Gate status

| Gate | State | Evidence / remaining condition |
| --- | --- | --- |
| External manifest/resolver | **PASS** | 34724313201 |
| Provider artifact hashes | **PASS** | 34724313143 |
| Dedicated-server baseline | **PASS** | 34704011609 |
| BP1-BP7 strategic gameplay/ecology | **PASS** | breakpoint evidence above |
| BP8 release/deploy/launcher machinery | **PASS at implementation/CI scope** | final BP8 matrix in current handoff |
| Final production world | **BP9 HARD EVIDENCE** | candidate generation/visual lock/archive/restore |
| Production host performance | **BP9 HARD EVIDENCE** | A1 PASS or documented MIGRATE |
| Independent off-host recovery | **BP9 HARD EVIDENCE** | real storage/recovery drill |
| Real friend-machine client acceptance | **BP9/BP10** | Windows + Apple Silicon |
| Public signed stable release | **BP10** | notarization/promotion/RC freeze |

## Immediate next sequence — BP9

On the next **"go"**, use the BP8 operational contract to generate/freeze the real world candidate, deploy an exact release to the fixed-size host, run defining DrewCraft systems together under representative multiplayer load, measure performance, and deliberately exercise crash/restart/backup/recovery paths.

Do **not** begin BP10 hard RC acceptance or tag `1.0.0` until BP9 is reached, reported, and the user says **"go"** again.
