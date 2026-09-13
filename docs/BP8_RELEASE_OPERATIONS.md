# DrewCraft BP8 — Production World, Deployment, Release, and Launcher Convergence

BP8 turns the already-implemented DrewCraft gameplay stack into one reproducible operational system. It does **not** fabricate production evidence that requires a final visual world choice or a real multiplayer host workload; those measurements feed BP9/BP10.

## Central release rule

> **One immutable release manifest is the client/server application truth. Persistent world identity is separate and is never silently rolled back with application files.**

The release contract is `release-manifest.json`; `live.json` is only a stable-channel pointer to one validated immutable manifest.

The manifest contains:

- DrewCraft pack version and release channel;
- protocol version;
- Minecraft, NeoForge, and Java requirements;
- minimum DrewCraft launcher version;
- exact managed file paths, sides, sizes, SHA-256 values, and acquisition URLs;
- exact managed runtime lock for Windows x86-64 and Apple Silicon macOS;
- server address/health metadata when configured;
- required `worldId`, `worldRevision`, and `generationPackVersion`.

Client and server layouts are derived from the same verified inputs. Files identical on both sides collapse to `common`; divergent files stay `client` or `server`.

DrewCraft's own compiled integration jar is injected explicitly into both verified layouts and hash-recorded before release assembly. The external dependency count does not silently stand in for the custom mod.

## Production world contract

`world/production-world.plan.json` is intentionally **not** allowed to claim a final production seed/radius before a real candidate has been generated and reviewed.

The current process is:

1. generate representative Terrain Diffusion Plus / World Scale 2 candidates on suitable generation hardware;
2. pregenerate one of the approved experimental radii;
3. measure generation time, expanded size, archive size, backup time, restore time, and restart time;
4. create and verify a checksummed world archive;
5. destroy the working copy and restore into a clean location;
6. inspect terrain/geography visually;
7. inspect hostile-source distribution and proposed herd corridors;
8. submit the measured candidate report to `tools/evaluate_world_candidates.py`;
9. only a fully passing report may freeze `seed` and `pregenRadiusBlocks` into a locked production plan.

The candidate lock fails closed if clean restore is unverified, an archive hash is missing, a radius is outside the experiment set, or any required human/geographic review has not passed.

### Strategic source and herd indexing

The production live server never scans distant chunks for strategic sources or herds.

During world-build/indexing:

- generated hostile structure locations are exported/indexed offline;
- `world/source-mappings.json` decides which structure IDs become which source class/faction;
- generic Source Core placement is deterministic: **horizontal structure center -> nearest accessible interior floor candidate**;
- the resulting exact source/core records plus explicit herd corridors are written to `drewcraft-strategic-seeds.json`.

At runtime `ProductionStrategicSeedRuntime`:

- validates the strategic-seed file against `drewcraft-world.json` world ID/revision;
- registers source authority without searching chunks;
- registers persistent herd records;
- places a Source Core only if its exact chunk is already loaded or naturally loads later;
- handles spawn-area chunks that were already loaded before the server-start event;
- never force-loads a source chunk.

## World archive identity

A production archive contains at minimum:

- Minecraft world state including `level.dat`;
- `drewcraft-world.json`;
- `drewcraft-strategic-seeds.json`;
- DrewCraft/NeoForge/mod SavedData contained in the world tree.

`tools/world_bundle.py` stamps, validates, archives, hashes, and clean-restores this world identity. An archive is not accepted merely because it was created; its checksum and clean restore must pass.

## Production host contract

Initial benchmark target:

- Ubuntu ARM64;
- OCI `VM.Standard.A1.Flex`;
- 2 OCPUs / 12 GB RAM;
- one VM;
- no instance pool;
- no autoscaling or automatic resize;
- Java 21 ARM64 pinned by exact URL/size/SHA;
- non-root `drewcraft` service account;
- systemd-managed Minecraft and read-only health services;
- application releases separated from persistent world data.

Native ARM64 CI compiles/tests the DrewCraft NeoForge mod. That proves architecture/toolchain compatibility of the custom mod; it is **not** substituted for BP9's representative Minecraft workload benchmark.

The application architecture is host-portable. If A1 misses BP9 performance or native-dependency gates, record `MIGRATE` and move the same release/persistent layout to a deliberately chosen fixed-size replacement host rather than silently scaling cloud resources.

## Complete immutable server application

A verified mod tree alone is not a deployable Minecraft server.

`tools/assemble_server_application.py` combines:

- the exact hash-verified NeoForge 21.1.250 server installer output (`run.sh`, libraries, launcher metadata);
- the verified DrewCraft server mod/config tree;
- the compiled DrewCraft integration jar;
- server JVM policy and EULA acceptance.

It explicitly excludes `world` and `logs`, which are reserved persistent paths wired by the production host.

Initial 12 GB host policy uses `-Xms4G` / `-Xmx8G` rather than consuming all machine memory; BP9 measurements may tune this.

## Server deployment/update transaction

`infra/serverctl.py` provides the application transaction:

1. validate release manifest;
2. verify world ID/revision/generation compatibility **before activation**;
3. stage common+server files outside the live tree;
4. verify size + SHA-256 for every managed file;
5. create a checksummed pre-update backup of persistent state;
6. stop Minecraft cleanly when an operator/service command is supplied;
7. atomically switch `current` to the staged immutable application release;
8. start and health-check;
9. publish `ready` only after success;
10. if rollout fails, restore the previous application pointer and matching health/active-release metadata;
11. never automatically restore an older world merely because application startup failed.

A failed first deployment leaves no fake active release. A failed upgrade restores application identity while preserving the authoritative current world.

## Backup/restore

Production layout:

```text
/srv/drewcraft/
  releases/<version>/
  current -> releases/<version>
  persistent/world/
  backups/
  logs/
  state/
  staging/
  bin/
```

Backups include the complete persistent tree and metadata binding it to pack/protocol/world identity. Archives get SHA-256 sidecars. Restore refuses a non-empty target and verifies the archive before extraction.

BP8 automated acceptance restores into a separate clean root and verifies world + strategic state. Production BP9/BP10 still require an actual independent/off-host storage copy and recovery drill on representative world data.

## Friend launcher contract

The friend-facing bootstrapper owns DrewCraft convergence; Prism owns Microsoft authentication and Minecraft launching.

### Exact managed runtime

`launcher/runtime-lock.json` pins exact:

- Java 21 runtime;
- Prism Launcher;
- platform/architecture URL;
- archive type;
- size;
- SHA-256;
- expected executable.

V1 native bootstrap targets:

- Windows x86-64;
- Apple Silicon macOS.

CI downloads and verifies the real pinned runtime archives on each native OS. Windows produces a PyInstaller one-click `.exe`; macOS produces an arm64 `.app` and DMG with development/ad-hoc code signing. Final Apple Developer signing/notarization is an RC distribution gate, not falsely claimed by BP8.

### Every launch/update

The bootstrapper:

1. reads `live.json`;
2. verifies the immutable release-manifest SHA-256;
3. rejects an unsupported/newer launcher minimum version;
4. stages the exact client/common managed tree;
5. reuses already-valid unchanged local files and downloads changed/missing files;
6. verifies every staged hash;
7. acquires/verifies pinned Java + Prism if absent;
8. creates a real Prism instance with `instance.cfg` and `mmc-pack.json` declaring exact Minecraft + NeoForge versions;
9. atomically promotes the per-version instance;
10. preserves explicitly user-owned screenshots/resource packs/shader packs/saves/options where they are not pack-managed;
11. verifies both the immutable local release cache and the actual Prism instance;
12. compares safe server health/version data before launch;
13. launches the exact instance and server address using Prism CLI.

Microsoft account state lives in the persistent managed Prism root, not inside versioned pack instances.

Opening DrewCraft again is also the repair path: corrupted/missing managed content is reconstructed from the release truth rather than asking friends to edit a mods folder.

## BP8 automated evidence contract

`.github/workflows/bp8-convergence.yml` exercises five independent jobs:

1. **release-contract** — every `test_bp8_*.py` release/world/update/repair/restore invariant;
2. **server-application-layout** — downloads and SHA-verifies the exact NeoForge installer, performs a real `--installServer`, then proves a complete immutable application layout;
3. **server-arm64** — native ARM64 Java + full DrewCraft `test build` + production jar existence;
4. **launcher-windows** — verifies real locked Java/Prism, builds Windows one-click EXE;
5. **launcher-macos-arm64** — verifies real locked Java/Prism, builds native arm64 app/DMG and verifies code signature structure.

The earlier dedicated-server/full-pack compatibility baseline remains valid dependency evidence unless the locked dependency/platform set changes.

## Explicit BP8 -> BP9 boundary

BP8 makes the system **reproducible, deployable, updatable, repairable, and testable** without inventing measurements.

BP9 owns the expensive real-world convergence evidence:

- generate/select/freeze the final Terrain Diffusion production seed/radius using the BP8 candidate lock;
- run the final world archive/clean restore with its real size/checksum;
- deploy that restored world and exact release to the fixed-size production candidate host;
- benchmark OCI A1 2/12 under representative DrewCraft load and choose `PASS` or `MIGRATE`;
- run multiplayer cross-system scenarios and performance/crash/recovery stress;
- prove an actual independent off-host backup/restore path;
- observe real Windows + Apple Silicon friend-machine install/login/update/join behavior;
- finish Apple production signing/notarization before public RC distribution.

No BP9 gameplay feature should fork the release/world ownership model established here.
