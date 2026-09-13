# DrewCraft Current Development Breakpoint

**Updated:** 2026-09-12  
**Protocol:** `docs/DEVELOPMENT_BREAKPOINTS.md`  
**Last completed breakpoint:** **BP8 — Production world + deployment + release/launcher convergence**  
**Next breakpoint:** **BP9 — Cross-system scale, failure, recovery, and performance hardening**

## BP8 status — REACHED

BP8 is complete at implementation/reproducibility/native-build/CI convergence scope. Detailed contract: `docs/BP8_RELEASE_OPERATIONS.md`.

BP8 deliberately does **not** invent production evidence that requires a final visually selected Terrain Diffusion world, a real production host workload, or final signed public binaries. The machinery for collecting and enforcing that evidence is complete; BP9/BP10 own the expensive real-world gates.

## Implemented

### One immutable release truth

- `release-manifest.json` is the one client/server application contract.
- `live.json` is only the stable-channel pointer to an immutable manifest.
- Client/server layouts derive from one verified source; identical files collapse to `common`.
- Every managed file has side/path/size/SHA-256/acquisition URL.
- DrewCraft's own compiled NeoForge mod is explicitly injected and hash-recorded into both verified sides.
- Exact provider artifacts are matched by locked SHA and use official CurseForge/Modrinth acquisition URLs when available; DrewCraft does not need to rehost them.
- Public payload packaging omits provider-backed artifacts and includes only DrewCraft/source-built/runtime-owned content, manifest/evidence, and checksums.

### Complete server application + safe updater

- The exact SHA-verified NeoForge 21.1.250 installer constructs a full immutable server application (`run.sh`, libraries, verified mods/config).
- Persistent `world` and `logs` are excluded from application releases.
- Initial 12 GB host policy is `-Xms4G/-Xmx8G`.
- `infra/serverctl.py` stages/verifies, checks world compatibility before activation, creates a checksummed pre-update backup, atomically switches `current`, health-checks, and rolls back application identity on failure.
- Failed application rollout never blindly restores an older world.
- Failed first deployment leaves no fake active application; failed upgrades restore matching pointer/health/active-release metadata.
- Backup restore verifies checksum and refuses non-empty targets; acceptance restores to a clean separate root.

### Production world pipeline

- `world/production-world.plan.json` owns world identity/revision and `generationPackVersion = drewcraft-worldgen-1`.
- Final production seed/radius remain intentionally unset until measured and visually reviewed.
- Approved experiment radii: 4096 / 8192 / 12288 blocks.
- `tools/evaluate_world_candidates.py` requires generation/disk/archive/backup/restore/restart measurements, clean restore, archive SHA, terrain review, source distribution, herd-corridor review, and matching generation identity before locking a candidate.
- `tools/world_seed_index.py` converts offline generated-structure evidence into exact strategic source/core/herd seeds.
- Generic Source Core placement is deterministic: **horizontal center -> nearest accessible interior floor**.
- Runtime seed import validates world identity, never scans distant structures/animals, handles already-loaded spawn chunks, and never force-loads source chunks.
- `tools/world_bundle.py` stamps, hashes, archives, validates, and clean-restores world identity.

### Production-host contract

- First benchmark target is Ubuntu ARM64 / OCI `VM.Standard.A1.Flex` / 2 OCPU / 12 GB, fixed size, no autoscaling.
- Host bootstrap creates a non-root DrewCraft service, separated app/persistent trees, systemd Minecraft service, and read-only health service.
- Native ARM64 CI compiles/tests the DrewCraft mod and production jar.
- If representative BP9 workload misses the target, required outcome is explicit `MIGRATE`, not silent cloud scaling.

### One-click Windows + Apple Silicon launcher

- Exact Java 21 and Prism runtime archives are pinned by URL/size/SHA per platform.
- Bootstrapper stages/verifies updates atomically and reuses already-valid unchanged files.
- Real Prism instance metadata (`instance.cfg` + `mmc-pack.json`) declares exact Minecraft 1.21.1 + NeoForge 21.1.250.
- Microsoft account state stays in persistent Prism data, outside versioned pack instances.
- User screenshots/resource packs/shader packs/saves/options are preserved where not pack-managed.
- Repair validates both the immutable local release cache and actual Prism instance.
- Server health/protocol/pack compatibility is checked before launch.
- Native CI builds `DrewCraft-Windows.exe` and Apple Silicon `DrewCraft-macOS.dmg`.
- macOS CI proves arm64 + ad-hoc/development signature structure; production Apple signing/notarization remains an RC gate.

### Reproducible release-candidate workflow

`.github/workflows/release-candidate-build.yml` can rebuild the exact external profile plus Terrain Diffusion source build, compile/inject DrewCraft, install exact NeoForge, assemble the complete server application, create one provider-aware release manifest, independently verify client/server trees, and emit a publishable candidate payload without a developer manually zipping a local Minecraft folder.

## BP8 acceptance evidence

Final BP8 code gate:

- code/test head: **`af2cae4764196c7280ffaf4bb07946386ea18ee1`**
- BP8 convergence CI: **run `34733309413` — SUCCESS**
- all five jobs: **SUCCESS**
  - `release-contract`
  - `server-application-layout`
  - `server-arm64`
  - `launcher-windows`
  - `launcher-macos-arm64`

The gate covers every `test_bp8_*.py`, parses both BP8 workflows, performs a real SHA-verified NeoForge `--installServer`, compiles/tests DrewCraft on native ARM64 and proves its production JAR, verifies real pinned Java/Prism archives, and builds the Windows EXE plus Apple Silicon DMG.

Earlier dedicated-server/full-pack baseline **34704011609**, provider hashes **34724313143**, and manifest graph **34724313201** remain valid because BP8 did not change the locked external dependency set.

## Intentionally deferred real-world evidence

These are **not** claimed complete by BP8:

- final Terrain Diffusion seed/radius and real production world archive;
- visual approval of final terrain/source/herd geography;
- representative OCI A1 Minecraft workload benchmark (`PASS` or `MIGRATE`);
- actual independent/off-host production backup drill;
- real friend-machine Windows/macOS install/login/update/join observation;
- Apple Developer signing/notarization;
- public stable binaries and `https://drewphi.github.io/DrewCraft/live.json` promotion.

Those are BP9/BP10 acceptance work. The public Pages repository does not yet contain a live DrewCraft release, so BP8 does not publish a broken pointer merely to claim distribution is live.

## Next: BP9

On the next **"go"**, begin BP9 cross-system scale/failure/recovery hardening using the BP8 operational contract.

BP9 must generate/select/freeze the real production-world candidate, restore/deploy it with an exact release, benchmark the fixed-size host, exercise the defining systems together under representative multiplayer load, stress crash/restart/backup/recovery behavior, and gather the real client/host performance evidence required before RC freeze.

Stop and report again when BP9 passes. Do not begin BP10 hard acceptance or tag `1.0.0` until the user says **"go"** after BP9.
