# DrewCraft Performance and Optimization Stack

Research snapshot: **2026-09-12**

This document defines the intended optimization architecture for DrewCraft on Minecraft **1.21.1 / NeoForge / Java 21**. It is part of the Stage 1/Stage 2 dependency work: candidates are recorded now, exact artifacts are hashed and locked only after reproducible-pack resolution and compatibility testing.

The goal is not to install every performance mod available. The rule is:

> **Optimize each bottleneck deliberately, avoid overlapping patches where practical, and benchmark the complete DrewCraft stack rather than assuming synthetic gains transfer.**

DrewCraft has two unusual workloads:

1. a very large pregenerated Terrain Diffusion world containing occasional large hostile-source structures; and
2. clients rendering long-distance terrain/weather plus large structures while the server may simultaneously materialize strategic encounters.

The production server should normally load pregenerated chunks rather than run expensive Terrain Diffusion + giant-structure generation during ordinary play. Aggressive asynchronous world-generation mods are therefore optional compatibility spikes, not foundational requirements.

---

## 1. Baseline performance suite

These mods should enter the **Stage 2 compatibility stack** unless a concrete incompatibility is found.

### Common / server-and-client optimization

- **ModernFix** — broad performance, memory, startup and bug-fix layer.
- **FerriteCore** — memory-use reduction, especially valuable with large modded blockstate registries.
- **Lithium** — core game-logic/ticking optimizations; must be tested with Create, strategic entities and all custom DrewCraft behavior.
- **ScalableLux** — faster lighting updates; particularly relevant to large structures and chunk loading.
- **AllTheLeaks** — leak fixes for Minecraft/NeoForge/mod interactions; intended to improve long-running client/server stability.
- **FastSuite** — recipe-system optimization.
- **FastWorkbench** — crafting-table recipe/cache optimization.
- **FastFurnace** — furnace recipe/cache optimization.
- **Clumps** — combines XP orbs to reduce entity overhead after large fights/farms.

### Server-focused optimization / reliability

- **ServerCore** — server optimization framework. Start with conservative defaults and keep gameplay-changing features such as entity activation/dynamic simulation-distance behavior disabled until separately proven.
- **Chunk Sending** — prioritizes/staggers/caches chunk packet delivery, useful when players rapidly approach large pregenerated structures or travel by vehicle/aircraft.
- **Connectivity** — packet/login/payload reliability fixes. Treat as reliability infrastructure, not a substitute for fixing DrewCraft protocol bugs.
- **spark** — mandatory profiler/diagnostic tooling for development and production investigations. It is not itself an optimization.

### Client rendering optimization

- **Embeddium** — primary NeoForge client renderer optimization.
- **ImmediatelyFast** — immediate-mode/entity/UI/particle rendering optimization.
- **Entity Culling** — client-side occlusion culling for hidden entities and block entities.
- **MoreCulling** — additional block/face/item culling. This complements Entity Culling rather than owning the same exact visibility mechanism, but the pair must still be visually tested with Create, MTS, Simple Clouds and Distant Horizons. Its required Cloth Config API dependency is explicitly pinned in the production profile.

### Required libraries introduced by this suite

At minimum, current candidates add:

- **Placebo** — required by FastSuite / FastWorkbench / FastFurnace current lines.
- **Cupboard** — required by current Chunk Sending and Connectivity lines.

All transitive dependencies must be resolved by the Stage 1 resolver rather than installed manually.

---

## 2. Candidate versions at the research snapshot

These are **candidate versions, not production locks**. `pack/manifest/performance_candidates.yaml` is the machine-readable companion.

| Mod | Candidate | Side / role |
| --- | --- | --- |
| ModernFix | `5.27.24+mc1.21.1` | common |
| FerriteCore | `7.0.3` | common |
| Lithium | `0.15.4+mc1.21.1` | common/server logic |
| ServerCore | `1.5.19+1.21.1` | server |
| ScalableLux | `0.1.0.1` | common lighting |
| Chunk Sending | `3.9` | server/common networking |
| AllTheLeaks | `1.1.12+1.21.1` | common |
| FastSuite | `6.0.7` | common/server recipe system |
| FastWorkbench | `9.1.3` | common |
| FastFurnace | `9.0.1` | common |
| Clumps | `19.0.0.1` | common |
| Connectivity | `7.6` | common/server reliability |
| spark | `1.10.124` | server/admin |
| Embeddium | `1.0.15` | client |
| ImmediatelyFast | `1.6.13` | client |
| Entity Culling | `1.10.5` | client |
| MoreCulling | `1.0.10` | client |
| Placebo | `9.9.2` | library |
| Cupboard | `4.1` | library |

Exact provider file IDs and SHA-256 hashes remain Stage 1 resolver work unless already recorded in the candidate manifest.

---

## 3. Aggressive / experimental optimization branch

### C2ME NeoForge

**Do not make C2ME part of the first baseline lock.**

C2ME improves chunk generation, I/O and loading through concurrency. This could substantially accelerate the **offline world-build/pregeneration workflow**, but it deliberately changes threading assumptions and its own documentation warns that custom world generators may expose compatibility issues.

DrewCraft uses Terrain Diffusion Plus, custom large structure selection, Chunky pregeneration and later source indexing, so the test must be treated as a separate branch.

Current 1.21.1 NeoForge compatibility-spike candidate:

- `c2me-neoforge-mc1.21.1-0.3.0+alpha.0.93.jar`
- alpha/dev build

Required spike:

1. generate the same bounded disposable test region without C2ME;
2. regenerate from the same seed/config with C2ME;
3. verify Terrain Diffusion output, structures, registries and source indexing;
4. compare pregeneration chunks/second, CPU utilization, heap/native memory and wall time;
5. restart/reload the generated region repeatedly;
6. inspect for thread/random/worldgen warnings or nondeterministic corruption;
7. promote only if output correctness is acceptable and the speedup is substantial.

Even if C2ME is useful for the world-build machine, it does not automatically need to run on the production server after the world is pregenerated.

### SuperChunk / GPU chunk-generation bundles

Do **not** baseline these for V1. They combine multiple aggressive optimizations and hardware-specific behavior, and Terrain Diffusion already has its own unusual inference/worldgen path. They may be revisited only for offline build experimentation after the conservative stack is stable.

### Noisium

Do not add to the baseline. The project is archived and its worldgen role overlaps the area where DrewCraft already has the highest compatibility risk.

---

## 4. Large-structure performance strategy

Large source structures such as selected When Dungeons Arise forts/palaces stress several independent stages:

```text
disk read
  -> chunk loading / deserialization
  -> lighting
  -> server ticking / block entities / entities
  -> chunk packet construction and network delivery
  -> client chunk mesh construction
  -> client render / entity and block-entity render
```

DrewCraft addresses these deliberately:

- pregenerate structures offline with Chunky;
- ModernFix + FerriteCore + AllTheLeaks reduce memory/startup/leak pressure;
- Lithium + conservative ServerCore improve simulation work;
- ScalableLux targets lighting;
- Chunk Sending controls packet spikes;
- Embeddium handles terrain/chunk rendering;
- ImmediatelyFast handles immediate-mode rendering workloads;
- Entity Culling + MoreCulling avoid drawing unnecessary hidden geometry/entities;
- Distant Horizons renders distant terrain as LOD rather than full-resolution chunks;
- spark identifies the actual remaining server hot path.

**Structure Essentials** is a useful world-build/server-tool candidate, not a raw FPS mod. Its faster locating, spacing/separation controls, overlap prevention and structure debugging may help the source-structure build/index workflow. Test it after the base worldgen stack is stable; do not require it if pack-owned structure configuration already solves the problem cleanly.

---

## 5. Mob optimization policy

Do not solve strategic-population scale by spawning thousands of entities and then freezing their AI.

DrewCraft's primary optimization is architectural:

- unloaded armies/hordes/herds are compact strategic records;
- only nearby groups materialize as entities;
- materialized large armies have bounded active-entity caps/waves while preserving total strategic strength;
- distant groups never require vanilla entity ticking or full-resolution entity pathfinding.

Therefore generic entity-freezing / AI-throttling mods such as `DoesPotatoTick?` or broad AI optimization mods are **not baseline dependencies**. They may accidentally freeze strategic entities at encounter boundaries or change behavior that the tactical horde/herd layer depends on.

ServerCore entity-activation/dynamic-distance features should start disabled for the same reason. If later enabled for ordinary entities, strategic-tagged materialized entities need explicit exclusion/proof.

---

## 6. Server configuration policy

Optimization mods must begin with semantics-preserving settings.

Do not enable a setting simply because it benchmarks faster if it changes gameplay or simulation expectations. In particular:

- no dynamic simulation-distance behavior until tested with strategic materialization radii;
- no mobcap changes until local-spawn coexistence is tested;
- no entity activation/freeze rule that can pause a strategic encounter incorrectly;
- no async save/worldgen feature without restart/corruption tests;
- no packet limit that causes MTS/Create/DrewCraft synchronization failure;
- no renderer option that breaks Simple Clouds, Distant Horizons, Create contraptions, MTS vehicles or radar displays.

Pack-owned configuration should be committed under the appropriate `pack/common`, `pack/client`, or `pack/server` configuration tree once those directories are created.

---

## 7. Stage 2 performance compatibility matrix

The full baseline stack is not accepted until it passes all normal Stage 2 tests plus:

### Dedicated server

- clean boot with every baseline optimizer loaded;
- 30+ minute idle soak and active-player soak;
- repeated restart/rejoin;
- representative Create machine/train activity;
- representative MTS road/aircraft movement;
- representative Project Atmosphere weather;
- representative large structure loaded and traversed;
- representative strategic materialization test when that subsystem exists;
- no unexplained mixin overwrite/conflict warnings;
- no recipe/cache correctness regressions;
- no lighting corruption;
- no chunk resend/login timeout regression.

### Client

Test both Windows x86-64 and Apple Silicon macOS:

- Embeddium + Distant Horizons;
- Embeddium + Simple Clouds + Project Atmosphere;
- ImmediatelyFast;
- Entity Culling + MoreCulling;
- large structure approach on foot and at vehicle/aircraft speed;
- Create trains/contraptions;
- MTS vehicles/aircraft;
- radar/display rendering once available;
- memory stability over a long traversal session.

### Metrics

Record at least:

- server MSPT p50 / p95 / p99;
- GC pause behavior;
- heap after warmup and after long traversal;
- native/process RSS;
- chunk-send rate / join time where practical;
- client average and low-percentile FPS in representative scenes;
- large-structure approach hitching;
- pregeneration chunks/second for world-build tests.

Use spark and external process metrics as appropriate. Optimization changes require before/after evidence.

---

## 8. Promotion rule

A performance dependency becomes part of the production lock only when:

1. the exact 1.21.1 NeoForge artifact is acquired from an allowed provider;
2. SHA-256 is recorded;
3. transitive dependencies are recorded;
4. source/license/redistribution path is audited;
5. client/server side classification is correct;
6. the relevant Stage 2 matrix passes;
7. it does not create a second gameplay/system authority;
8. removing it produces a measurable regression or it provides a concrete reliability benefit worth its maintenance cost.

This last requirement prevents the optimization stack from becoming a cargo-cult collection of jars.
