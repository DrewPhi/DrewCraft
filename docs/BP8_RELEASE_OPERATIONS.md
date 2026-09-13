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
- exact managed runtime lock for Windows x86-64, Apple Silicon macOS, and Ubuntu/Linux x86-64;
- server address/health metadata when configured;
- required `worldId`, `worldRevision`, and `generationPackVersion`.

Client and server layouts are derived from the same verified inputs. Files identical on both sides collapse to `common`; divergent files stay `client` or `server`.

DrewCraft's own compiled integration jar is injected explicitly into both verified layouts and hash-recorded before release assembly. The external dependency count does not silently stand in for the custom mod.

### Acquisition / redistribution policy

Exact provider artifacts are matched to the release by their already-locked SHA-256. Where an official provider acquisition identity exists, `tools/apply_release_acquisition.py` rewrites that file's manifest URL to the official provider instead of assuming DrewCraft should rehost it:

- CurseForge uses the exact project/file ID download endpoint;
- Modrinth resolves the exact locked version ID and filename to its official CDN URL;
- DrewCraft-built, source-built, config, and server-runtime files continue to use the immutable DrewCraft release base.

`tools/package_release_payload.py` then excludes provider-backed files from the DrewCraft-hosted payload. Friends still get one-click installation because launcher/server updater verifies the same exact SHA-256 regardless of acquisition origin.

## Production world contract

`world/production-world.plan.json` is intentionally **not** allowed to claim a final production seed/radius before a real candidate has been generated and reviewed.

The current world-generation compatibility identity is `drewcraft-worldgen-1`. A candidate report must carry that identity; a world generated under a different compatibility set cannot be silently promoted.

The process is:

1. generate representative Terrain Diffusion Plus / World Scale 2 candidates on suitable generation hardware;
2. pregenerate one of the approved experimental radii;
3. measure generation time, expanded size, archive size, backup time, restore time, and restart time;
4. create and verify a checksummed world archive;
5. destroy the working copy and restore into a clean location;
6. inspect terrain/geography visually;
7. inspect hostile-source distribution and proposed herd corridors;
8. submit the measured candidate report to `tools/evaluate_world_candidates.py`;
9. only a fully passing report may freeze `seed` and `pregenRadiusBlocks` into a locked production plan.

The candidate lock fails closed if clean restore is unverified, an archive hash is missing, the generation-pack identity differs, a radius is outside the experiment set, or any required human/geographic review has not passed.

### Strategic source and herd indexing

The production live server never scans distant chunks for strategic sources or herds.

During world-build/indexing:

- generated hostile structure locations are exported/indexed offline;
- `world/source-mappings.json` decides which structure IDs become which source class/faction;
- generic Source Core placement is deterministic: **horizontal structure center -> nearest accessible interior floor candidate**;
- the resulting exact source/core records plus explicit herd corridors are written to `drewcraft-strategic-seeds.json`.

At runtime `ProductionStrategicSeedRuntime` validates the seed file against `drewcraft-world.json`, registers source/herd authority without searching chunks, places Source Cores only in already-loaded/naturally loaded chunks (including spawn chunks that loaded before `ServerStartedEvent`), and never force-loads a source chunk.

## World archive identity

A production archive contains at minimum Minecraft world state including `level.dat`, `drewcraft-world.json`, `drewcraft-strategic-seeds.json`, and DrewCraft/NeoForge/mod SavedData contained in the world tree.

`tools/world_bundle.py` stamps, validates, archives, hashes, and clean-restores this identity. An archive is not accepted merely because it was created; checksum and clean restore must pass.

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

If A1 misses BP9 performance or native-dependency gates, record `MIGRATE` and move the same release/persistent layout to a deliberately chosen fixed-size replacement host rather than silently scaling cloud resources.

## Complete immutable server application

`tools/assemble_server_application.py` combines the exact hash-verified NeoForge 21.1.250 server installer output (`run.sh`, libraries, launcher metadata), the verified server mod/config tree, the compiled DrewCraft integration jar, JVM policy, and EULA acceptance. It explicitly excludes `world` and `logs`, which are reserved persistent paths.

Initial 12 GB host policy uses `-Xms4G` / `-Xmx8G`; BP9 measurements may tune it.

## Server deployment/update transaction

`infra/serverctl.py` provides the application transaction:

1. validate release manifest;
2. verify world ID/revision/generation compatibility before activation;
3. stage common+server files outside the live tree;
4. verify size + SHA-256 for every managed file;
5. create a checksummed pre-update backup;
6. stop Minecraft cleanly when an operator/service command is supplied;
7. atomically switch `current` to the staged immutable application release;
8. start and health-check;
9. publish `ready` only after success;
10. on failure, restore the previous application pointer and matching health/active-release metadata;
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

Prism remains the Microsoft-authentication/Minecraft-launch engine; the DrewCraft bootstrapper owns exact installation, update, validation, and repair.

`launcher/runtime-lock.json` pins exact Java 21 and Prism archives per supported architecture. Native client targets are Windows x86-64, Apple Silicon macOS, and Linux x86-64 (packaged for Ubuntu/Debian).

Every converge/update:

1. reads `live.json` and verifies its immutable manifest SHA;
2. rejects an unsupported minimum launcher version;
3. stages exact common+client content, downloading/reusing only verified files;
4. acquires/verifies pinned Java + Prism if absent;
5. creates a real Prism instance with `instance.cfg` and `mmc-pack.json` declaring exact Minecraft + NeoForge versions;
6. atomically promotes the versioned instance;
7. preserves explicitly user-owned screenshots/resource packs/shader packs/saves/options and Terrain Diffusion's downloaded model cache where not pack-managed;
8. verifies both the immutable local release cache and the actual Prism instance;
9. checks safe server health/version information;
10. launches the exact Prism instance and server address.

Microsoft account state lives in the persistent managed Prism root rather than versioned pack instances. Running DrewCraft again is also the repair path for corrupted/missing managed content.

CI builds `DrewCraft-Windows.exe`, `DrewCraft-macOS.dmg`, and `DrewCraft-Linux.deb`. macOS CI proves a native arm64 app and ad-hoc/development signature structure; final Apple Developer signing/notarization is deliberately an RC distribution gate.

## Reproducible release-candidate builder

`.github/workflows/release-candidate-build.yml` removes the remaining developer-local ZIP step. A manual candidate build:

1. compiles/tests the repository DrewCraft mod;
2. checks out and builds the exact Terrain Diffusion source ref;
3. rebuilds the exact verified external client/server dependency trees;
4. injects/hash-records DrewCraft itself;
5. downloads and SHA-verifies the exact NeoForge installer;
6. installs the full NeoForge server runtime;
7. assembles the complete immutable server application;
8. derives one common/client/server release layout;
9. generates the immutable release manifest;
10. applies official provider acquisition URLs by exact artifact hash;
11. independently reconstructs/verifies both client and server views;
12. creates a publishable payload containing only DrewCraft-owned files plus manifest/evidence/checksums.

`live.json` produced by this workflow is a **candidate pointer** until later promotion; public publication is not automatic merely because a build succeeded.

## BP8 automated evidence contract

`.github/workflows/bp8-convergence.yml` exercises five independent jobs:

1. **release-contract** — discovers every `test_bp8_*.py`, including update/repair/rollback/world/provider/payload invariants, and parses both BP8 workflow files;
2. **server-application-layout** — SHA-verifies the exact NeoForge installer, performs a real `--installServer`, then proves a complete immutable application layout;
3. **server-arm64** — native ARM64 Java + full DrewCraft `test build` + production jar existence;
4. **launcher-windows** — verifies real locked Java/Prism and builds the Windows EXE;
5. **launcher-macos-arm64** — verifies real locked Java/Prism and builds/verifies the native arm64 app/DMG.
6. **launcher-linux-x86_64** — verifies real locked Java/Prism and builds an Ubuntu/Debian x86-64 package.

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
- observe real Windows + Apple Silicon + Ubuntu/Linux friend-machine install/login/update/join behavior;
- finish Apple production signing/notarization and public stable publication before final RC distribution.

No BP9 gameplay feature should fork the release/world ownership model established here.
