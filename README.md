# DrewCraft

DrewCraft is a deliberately integrated Minecraft survival server built around **geographic scale, infrastructure, weather, transportation, and a living strategic world**.

The GitHub repository is still named `ServerMc` until a manual repository rename is performed; **DrewCraft** is the player-facing product/server name.

This is not a kitchen-sink modpack. Every major subsystem has one authoritative owner, and new mods are rejected when they merely duplicate an existing system.

## Current status

**Baseline certified — V1 integration development is now active.**

On 2026-09-12, the exact `stage2_base_performance` profile passed both reproducible full-profile verification and a real NeoForge dedicated-server smoke test. The successful server run:

- rebuilt the exact pinned Terrain Diffusion Plus source artifact;
- reconstructed the verified **31-dependency** server tree;
- installed pinned NeoForge 21.1.250;
- created and reached readiness on a brand-new Terrain Diffusion Plus world;
- stopped cleanly;
- restarted the same persisted world and reached readiness again;
- stopped cleanly again;
- passed the fatal-error scan.

The fresh-world boot required roughly **26 minutes** in GitHub CI; the same-world restart required roughly **2 minutes**. That confirms the expensive part is Terrain Diffusion Plus first-world initialization rather than ordinary restart behavior.

The V1 base-mod selection is now **frozen**. From this point forward the default work is compatibility adapters, cross-mod interactions, DrewCraft custom systems, profiling, and optimization—not adding more gameplay/content mods. A mandatory transitive dependency may still be added if an already-selected upstream requires it.

See [`docs/V1_EXECUTION_STATUS.md`](docs/V1_EXECUTION_STATUS.md) for the live gate status, certification evidence, CI policy, and exact next implementation sequence.

### Immediate next milestone

> Scaffold the `mods/drewcraft/` NeoForge integration mod, define upstream-independent service contracts, audit Terrain Diffusion Plus / Project Atmosphere / Create / MTS integration surfaces, and prove a thin environment-sampling vertical slice before building radar, armies, or broader gameplay systems.

We intentionally will **not** keep rerunning the expensive full Terrain Diffusion Plus server smoke test during ordinary integration work. Cheap compile/unit/manifest checks should carry development until the next meaningful full-stack V1 acceptance cycle, preferably run locally or on dedicated hardware.

## Target platform

- Minecraft **1.21.1**
- **NeoForge 21.1.250**
- **Java 21**
- Windows x86-64 clients
- Apple Silicon macOS as a hard V1 client target
- Ubuntu/Linux x86-64 as a hard V1 client target
- Linux server; Oracle Ampere A1 remains the first low-cost benchmark target, not a V1 requirement

## V1 scope

DrewCraft V1 is **feature-complete and integration-complete, not balance-complete**.

V1 requires the intended systems and bridges to exist and work together reliably. Broad recipe, fuel-price, progression, spawn-frequency, radar-tier, and difficulty tuning belongs to V1.1+ unless an upstream default clearly destroys a core design pillar.

## System ownership

| System | Owner |
| --- | --- |
| Overworld generation, terrain/climate fields, tall-world caves | Terrain Diffusion Plus |
| Offline world pregeneration | Chunky |
| Distant terrain LOD | Distant Horizons |
| Industry, logistics and rail | Create |
| Road vehicles and aircraft | Immersive Vehicles / MTS + minimal curated content |
| Atmospheric/weather simulation | Project Atmosphere |
| Cloud/localized-weather rendering substrate | Simple Clouds under Atmosphere integration |
| Season calendar/gameplay hooks | Serene Seasons where required/stable |
| Radar, aviation bridges, strategic populations, armies, herds and sieges | DrewCraft custom NeoForge integration mod |
| Ordinary local spawning/farms | Minecraft/upstream local rules; strategic simulation is additive |
| Technical performance | Measured optimization suite; no gameplay-state ownership |

Consequences:

- no second terrain/cave overhaul by default;
- no second weather simulator;
- no redundant giant technology tree merely to power radar;
- no competing macro horde/army simulator;
- no routine teleportation that destroys geographic scale;
- no optimizer may silently change strategic-world semantics.

## Core architecture

### Geography and transportation

Terrain Diffusion Plus at **World Scale 2** is the overworld foundation. The production world will be bounded and pregenerated offline with Chunky so the live server does not depend on neural terrain generation during normal play. Distant Horizons communicates that scale visually.

Create owns trains and industrial infrastructure. MTS supplies road vehicles and aircraft. Travel should remain geographically meaningful rather than being replaced by routine teleportation.

### Weather, aviation and radar

**Project Atmosphere is the atmospheric source of truth.** DrewCraft consumes that state through an adapter rather than inventing another weather simulation.

The planned first cross-mod vertical slice is:

`Terrain Diffusion Plus -> Project Atmosphere -> DrewCraft -> MTS`

That pipeline will drive wind, turbulence, visibility, terrain/elevation context, and later aircraft weather instruments.

Physical radar uses the same environmental state. Ground radar requires a real dish/controller, Create kinetic power, data connectivity, antenna-height/terrain-horizon logic, and a physical display. Aircraft weather radar reuses the same cached sensing pipeline.

### Persistent strategic world

Distant populations are compact server-side records rather than permanently loaded mobs. DrewCraft owns persistent hostile sources, strategic groups, unloaded movement/ETA, materialization, casualty reconciliation, multiple hostile compositions, sieges, and wild herds.

Hostile source structures have persistent `SourceRecord` state and a player-facing **Source Core** objective. Legitimately clearing the source permanently prevents future forces from that source, while already-deployed forces continue to exist.

Sieges are path-first: mobs use viable entrances/routes and breach only when necessary, with constrained breach corridors rather than indiscriminate block griefing.

Wild animals may exist as persistent `HerdRecord`s while unloaded, but named/domesticated/penned/player-owned animals remain ordinary persistent entities.

Normal Minecraft spawning, caves, farms, spawners, building, redstone, and Create contraptions remain intact; strategic simulation is additive.

## Integration-mod architecture

DrewCraft should use one NeoForge integration mod with explicit internal adapters rather than many tightly coupled custom mods.

Initial upstream-independent contracts are expected to include:

- `TerrainService` — elevation/terrain/climate data;
- `WeatherService` — wind, temperature, pressure, humidity, precipitation, visibility, severity;
- `PowerService` — Create kinetic availability/consumption semantics;
- `VehicleService` — MTS vehicle/aircraft pose, velocity, orientation and instrument hooks.

Third-party implementation types should remain inside their adapters. Integration preference is:

**public API/event -> external adapter -> narrow accessor/mixin -> maintained fork only as a last resort when licensing permits.**

## Performance strategy

The first optimization is architectural:

1. pregenerate expensive bounded terrain offline;
2. keep strategic populations unloaded as compact records;
3. materialize only nearby tactical entities;
4. cache expensive products such as radar scans and terrain masks;
5. profile before changing semantics.

The frozen baseline includes the selected conservative optimization suite and `spark` for profiling. Aggressive experiments such as C2ME remain isolated unless separately proven correct and useful.

## One-click friend experience

Friends should not manually manage Java, NeoForge, Prism, mods, or configs.

The intended experience is:

1. visit the DrewCraft page;
2. click **Windows**, **Mac**, or **Linux**;
3. run the DrewCraft bootstrapper;
4. authenticate through Prism/Microsoft once;
5. thereafter launch/update through DrewCraft.

Client and server releases come from the same exact manifest. Updates must be staged, hash-verified, repairable, and rollback-safe.

## Repository direction

```text
ServerMc/ (eventually DrewCraft/ if renamed)
├── README.md
├── AGENTS.md
├── docs/
├── pack/
│   ├── manifest/
│   ├── common/
│   ├── client/
│   ├── server/
│   └── overrides/
├── mods/
│   └── drewcraft/
├── launcher/
├── server/
├── infra/
├── world/
├── tools/
├── tests/
└── .github/workflows/
```

Third-party binaries, generated worlds, Java runtimes, model assets, backups, credentials, and caches are not committed to Git by default. Releases are generated from manifests and verified artifacts.

## Canonical documentation order

1. [`docs/v_1_requirements.md`](docs/v_1_requirements.md) — hard V1 product/release contract
2. [`docs/v_1_development_tree.md`](docs/v_1_development_tree.md) — canonical dependency-ordered execution checklist
3. [`docs/V1_EXECUTION_STATUS.md`](docs/V1_EXECUTION_STATUS.md) — **live gate status, certification evidence, and immediate next work**
4. [`docs/STRATEGIC_WORLD_MODEL.md`](docs/STRATEGIC_WORLD_MODEL.md) — strategic-world behavior contract
5. [`docs/SOURCE_CORE_SPEC.md`](docs/SOURCE_CORE_SPEC.md) — hostile-source clearing contract
6. [`docs/PERFORMANCE_STACK.md`](docs/PERFORMANCE_STACK.md) — optimization architecture
7. [`docs/MOD_STACK.md`](docs/MOD_STACK.md) — subsystem ownership and anti-redundancy policy
8. [`docs/UPSTREAM_DEPENDENCIES.md`](docs/UPSTREAM_DEPENDENCIES.md) — source/fork/licensing policy
9. [`pack/manifest/README.md`](pack/manifest/README.md) — resolver/profile/promotion architecture
10. [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md) and [`docs/SYSTEMS.md`](docs/SYSTEMS.md) — product/custom-system design
11. [`docs/REPO_ARCHITECTURE.md`](docs/REPO_ARCHITECTURE.md) — repository/artifact boundaries
12. [`docs/LAUNCHER_HOSTING.md`](docs/LAUNCHER_HOSTING.md) — launcher/server/deployment architecture
13. [`docs/ROADMAP.md`](docs/ROADMAP.md) — high-level roadmap; the requirements/development tree/status documents above are more authoritative

## Definition of V1 success

A V1 release candidate must demonstrate the complete system together:

- one-click Windows, Apple Silicon, and Ubuntu/Linux installation/update;
- reliable large pregenerated Terrain Diffusion Plus world;
- representative multiplayer performance and restart safety;
- Distant Horizons;
- functional road vehicles, Create trains, and aircraft;
- real weather affecting flight;
- physical ground radar and aircraft weather radar;
- persistent hostile sources and unloaded strategic travel;
- multiple hostile compositions and large armies;
- casualty-preserving materialization/dematerialization;
- permanent source clearing without deleting already-deployed forces;
- path-first constrained sieges;
- persistent wild animal herds;
- normal local spawning/farms/building intact;
- reliable release updates, backups, restores, and rollback.

That is DrewCraft V1. Fine-grained balance comes after the complete integrated game exists.
