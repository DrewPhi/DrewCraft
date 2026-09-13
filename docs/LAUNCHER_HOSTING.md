# ServerMc Launcher, Updates, and Hosting

The operational goal is simple:

> A non-technical friend downloads ServerMc once, signs into Minecraft, and thereafter presses Play. Pack versions, Java, loader, mods, configs, and server compatibility are managed automatically.

This document describes how to make that true without placing cloud credentials on friends' computers.

## 1. Friend-facing experience

### First install

1. Visit the ServerMc download page / GitHub Release page.
2. Click **Windows**, **macOS**, or **Linux**.
3. Run the ServerMc bootstrapper.
4. Bootstrapper installs/locates the managed runtime pieces.
5. It creates the managed ServerMc Prism instance.
6. Prism prompts for normal Microsoft/Minecraft authentication if no account is configured.
7. Bootstrapper verifies the server and launches the instance.

### Normal launch

1. Open ServerMc.
2. It checks its own minimum supported version.
3. It reads the current release manifest.
4. It compares local hashes/version.
5. It downloads only missing/changed content.
6. It verifies the local pack.
7. It checks server pack compatibility/readiness.
8. It launches Minecraft through the managed Prism instance.

No manual mod copying.

## 2. Why Prism remains underneath

Prism Launcher already solves difficult Minecraft-launcher problems well:

- Microsoft authentication
- Minecraft libraries/assets
- instance isolation
- Java selection
- mod-loader instance metadata
- launch arguments
- logs and troubleshooting
- cross-platform support

ServerMc should not reimplement Microsoft's authentication flow or the entire Minecraft launcher stack.

The ServerMc app is the friendly orchestration/update layer. Prism is the underlying launch engine.

## 3. Platform packaging

A literally identical executable cannot be the correct native installer for Windows, macOS, and Linux. The seamless design is one download page with platform-specific artifacts.

Target outputs:

- Windows x86-64 installer/bootstrapper
- macOS universal app if tooling permits (Apple Silicon + Intel), otherwise architecture-specific artifacts hidden behind platform detection
- Ubuntu/Linux x86-64 `.deb` installer/bootstrapper

The friend-facing branding and workflow should be the same on both platforms.

### macOS requirements

For a genuinely non-technical experience, plan for:

- proper `.app` packaging
- code signing
- notarization
- Apple Silicon testing
- avoiding instructions that require disabling Gatekeeper

An unsigned development build is acceptable during private testing, but it is not the final UX target.

## 4. Java

Minecraft 1.21.1 / NeoForge requires Java 21.

The bootstrapper should not assume a friend's system Java is correct.

Preferred behavior:

1. detect a compatible managed Java 21 runtime already installed for ServerMc
2. otherwise download a pinned trusted distribution for the platform/architecture
3. verify checksum/signature as available
4. configure only the ServerMc Prism instance to use that Java

Do not modify system-global `JAVA_HOME` just to play the server.

## 5. Prism installation

Two acceptable implementation paths:

### A. Managed Prism installation

ServerMc downloads/maintains its own Prism installation or uses a supported portable/application install location.

Advantages:

- predictable version
- no user setup
- independent of an existing personal Prism configuration

### B. Existing Prism discovery

If a compatible installed Prism is found, ServerMc may offer/use it while still creating a dedicated managed instance.

For the first implementation, predictability is more important than clever reuse.

Respect Prism's distribution/update licensing and platform packaging rules.

## 6. Pack update protocol

### Release manifest

Launcher checks a small immutable/versioned `release-manifest.json` plus a stable pointer such as `live.json`.

`live.json` should contain only enough data to locate/validate the active release, for example:

```json
{
  "channel": "stable",
  "packVersion": "0.3.1",
  "manifestUrl": "https://.../release-manifest.json",
  "manifestSha256": "..."
}
```

### Per-file hashing

The release manifest should ultimately list files and SHA-256 hashes so the launcher can repair drift and download changed files rather than reinstall everything.

### Atomic updates

Never update the live instance in a way that leaves half-old / half-new files after interruption.

Safer flow:

1. download into staging
2. verify all hashes
3. build/update staged instance tree
4. atomically switch or rename into active state
5. retain previous known-good version temporarily for rollback

### User data separation

Do not overwrite user-owned data on pack updates:

- screenshots
- local logs
- options that are intentionally user-specific unless policy says otherwise
- account data
- downloaded Terrain Diffusion model assets, which are hash-validated runtime
  cache data and must not be fetched again after each versioned-instance update

Pack-managed config should be explicitly distinguished from user-managed config.

## 7. Server version handshake

The launcher should know the server's ServerMc pack version before launching when possible.

Server should expose a small unauthenticated health/version response containing only safe public data, for example:

```json
{
  "status": "ready",
  "packVersion": "0.3.1",
  "protocolVersion": 4,
  "minecraftVersion": "1.21.1"
}
```

This can be served by a tiny sidecar endpoint, a ServerMc server query extension, or another minimal mechanism.

The launcher compares this with the local release.

Cases:

- same version: launch
- client stale: update client
- server updating: show concise updating status and retry manually/with bounded polling while app is open
- server incompatible/newer: fetch the matching/current manifest
- server offline: show useful error rather than allowing a confusing Minecraft mismatch failure

Do not give friends infrastructure credentials so their launcher can SSH into the host.

## 8. Server update agent

The server can independently poll/check the stable release metadata or receive an owner-triggered update command.

Safe update flow:

1. detect new compatible server artifact
2. download and verify into staging
3. wait for an approved maintenance condition (normally zero players, unless owner forces restart)
4. announce restart if players are present and policy allows scheduled restart
5. backup current world/custom state
6. stop Minecraft cleanly
7. atomically install the new server pack
8. start server
9. run health/version check
10. roll back application files if boot fails, without rolling back world data blindly

World-data migrations require release-specific handling.

## 9. GitHub release flow

A production release should be produced by CI rather than a developer zipping their `.minecraft` directory.

Pipeline concept:

1. validate manifest schemas
2. resolve/download pinned dependencies
3. verify hashes
4. compile/test `servermc` mod
5. build client pack
6. build server pack
7. run dedicated-server smoke test
8. build platform launchers/installers
9. generate release manifest/checksums
10. publish GitHub Release
11. only after validation, update stable `live.json`

Stable pointer update is the final promotion step.

## 10. Hosting target: Oracle Ampere A1

### Current free baseline

Oracle's current Free Tier documentation should be treated as authoritative at deployment time.

As of 2026-09-12, it states that after the trial an Always Free tenancy should stay within a total of **2 OCPUs and 12 GB RAM across Ampere A1 instances**.

Do not design around older 4 OCPU / 24 GB blog/forum numbers.

### Why ARM is plausible

The dedicated Minecraft server and most Java mods are architecture-neutral Java.

However, **native dependencies are the risk**. Terrain Diffusion uses ONNX/runtime-native components. Therefore ARM64 is a release gate, not an assumption.

### Server target

Initial benchmark target:

- Oracle Linux/Ubuntu ARM64
- Ampere A1
- 2 OCPU
- 12 GB RAM total tenancy budget available to the server if using one A1 VM
- fixed block storage
- no compute autoscaling

Memory allocation to Java must leave headroom for the OS/native libraries; do not simply give all 12 GB to `-Xmx`.

## 11. Terrain Diffusion deployment strategy

Terrain Diffusion Plus explicitly recommends pre-generation because generation is expensive.

Production strategy:

1. create/test production world using the exact locked pack
2. use capable development hardware for Terrain Diffusion generation
3. run Chunky to pre-generate the chosen bounded region
4. validate world and structure generation
5. stop cleanly
6. archive the world with a checksum
7. upload to durable storage/server volume
8. restore it on the Oracle host
9. keep world border inside the pre-generated region during ordinary production play

The live host should not be expected to comfortably perform major new diffusion generation.

### ARM native compatibility gate

Before Oracle production deployment, explicitly test:

- dedicated server boots with Terrain Diffusion Plus installed on ARM64
- required native ONNX runtime loads
- already generated chunks load normally
- no startup code insists on unavailable GPU functionality
- minimal accidental chunk generation does not crash (even if slow)

If this fails, options include changing host architecture or investigating a safe production-world setup that does not require the terrain mod at runtime. **Do not remove a world-generation mod from an existing world casually**; registry/dimension assumptions must be proven safe first.

## 12. Performance benchmark gate

A server that boots is not necessarily viable.

Benchmark with a representative scenario:

- several players in different nearby chunks
- Project Atmosphere active
- Simple Clouds/client weather sync
- Create train + representative contraptions
- several Immersive Vehicles entities
- strategic world simulation active
- one materialized large hostile group
- one siege planner
- one or more radar installations

Track:

- MSPT / tick percentiles
- heap use and GC pauses
- native memory
- CPU saturation
- network bandwidth
- save/backup time
- restart time

The free A1 target passes only if gameplay remains consistently acceptable.

## 13. Cost controls

### Free account behavior

Oracle documentation states that a credit card is not charged for Free Tier usage unless the account is upgraded to paid status. Staying within an Always Free account is the strongest simple protection if it meets the project's needs.

### Paid account caution

On PAYG, a normal OCI budget is primarily an alert mechanism. Do not describe a budget alert as a guaranteed zero-overage kill switch.

If a paid account is later required:

- provision a fixed approved instance shape
- do not grant automation permission to resize/create arbitrary compute
- use compartment/service quotas and IAM restrictions where applicable
- set low budget alerts as defense in depth
- require owner action to increase capacity
- periodically audit active resources

ServerMc launcher code must never provision cloud resources.

## 14. Idle behavior

If the server is truly within Always Free limits, leaving the VM available may be simpler and cheaper operationally than building wake/sleep machinery.

If a paid host is eventually used, idle shutdown can be considered, but wake-up must not expose cloud credentials to friends.

A future architecture could use a narrowly scoped public wake service/function that holds the cloud permission server-side. This is not required for the first release.

## 15. Network/security

Minimum rules:

- Minecraft server port exposed as required
- SSH restricted as tightly as practical
- no RCON exposed publicly
- no database port exposed
- host firewall + OCI security rules
- launcher health endpoint reveals no secrets
- automatic security updates handled carefully so they do not restart Minecraft unexpectedly without policy

Use a domain/DNS name eventually so server IP replacement does not require a client pack update.

## 16. Backups

Backups must include more than region files.

Back up atomically/consistently:

- overworld/nether/end world data
- player data
- advancements/stats as desired
- ServerMc strategic SavedData/database
- mod-specific world data
- server config required for restore
- pack version and release manifest identity

Recommended pattern:

- frequent local snapshots/archives
- periodic copy to storage independent of the VM/block volume
- retention rotation
- checksum verification
- restore drill before calling the system production-ready

A backup that has never been restored is not yet proven.

## 17. World release lifecycle

The world and pack should have separate identities.

Example:

```text
packVersion: 0.4.2
worldId: servermc-main
worldRevision: 3
worldGenerationPackVersion: 0.2.0
```

Most pack releases should not require redistributing the world.

World expansion process:

1. freeze production at a clean backup
2. copy world to generation machine
3. increase border target
4. pre-generate new ring with the correct generation-compatible pack
5. validate seams/structures
6. deploy expanded world during planned maintenance
7. update world revision/checksum metadata

## 18. Failure UX

The launcher should translate common failures into useful messages:

- no Minecraft entitlement/account signed in
- server offline
- server updating
- local disk full
- download/hash failure
- Java runtime failure
- incompatible macOS architecture/build
- Prism launch failure
- modpack validation mismatch

Provide a button/path to reveal diagnostic logs for the developer, but do not make friends parse them during normal operation.

## 19. What seamless means

The project has succeeded operationally when a friend who knows nothing about Java or Minecraft mod loaders can:

- install ServerMc from one OS-appropriate download
- log into Minecraft
- play
- close it for a month
- reopen it after multiple pack releases
- automatically update to the correct version
- join without a mod mismatch

That experience is a first-class part of the server, not cleanup work after the mods are finished.
