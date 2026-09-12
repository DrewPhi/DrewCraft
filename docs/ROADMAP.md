# DrewCraft Implementation Roadmap

This is the high-level roadmap. The **hard V1 contract** is `docs/v_1_requirements.md`; the **canonical dependency-ordered checklist** is `docs/v_1_development_tree.md`; the **live state/evidence overlay** is `docs/V1_EXECUTION_STATUS.md`. If this roadmap is less specific, those documents win.

DrewCraft V1 is **feature-complete and integration-complete, not balance-complete**. Broad recipe/economy/difficulty tuning belongs after V1 unless an upstream default clearly breaks a core design pillar.

## Current position — 2026-09-12

The reproducible base profile is **certified and frozen for V1 integration development**.

Completed evidence-backed gates:

- exact Minecraft 1.21.1 / NeoForge 21.1.250 / Java 21 platform lock;
- deterministic profile resolution and provider-artifact hash verification;
- exact Terrain Diffusion Plus source/build/model provenance;
- exact `stage2_base_performance` reconstruction;
- real dedicated-server fresh-world creation and readiness;
- clean shutdown;
- successful restart of the same persisted world;
- fatal-error scan.

Full profile verification: run `34702233400` — **PASS**.  
Dedicated-server certification: run `34704011609` / job `103580655867` — **PASS**.

The fresh Terrain Diffusion Plus world required roughly 26 minutes to initialize in GitHub CI; the same-world restart required roughly 2 minutes. The first-world cost is therefore treated as a provisioning/world-build concern.

**Base mod selection is closed unless a blocking defect or mandatory transitive requires a change.** Ordinary work now moves into DrewCraft integration, interactions, persistence, release infrastructure, and optimization.

## 0. Reproducible pack foundation — PASS

The repository can reconstruct the selected development profile without a developer's hand-managed `mods/` directory.

Implemented/validated:

- canonical manifests and profiles;
- Minecraft/loader/Java lock;
- upstream source/provider registry;
- client/server classification;
- provider artifact acquisition and SHA-256 verification;
- exact Terrain Diffusion Plus source-build provenance;
- verified-pack builder and evidence output;
- CI pack/profile verification.

Future dependency changes must be intentional because they invalidate part of the certified baseline evidence.

## 1. Base dedicated-server compatibility — PASS

The selected baseline has booted a real new Terrain Diffusion Plus world and restarted the same persisted world successfully.

This does **not** close the later client/platform/full-game interaction gates. Windows, Apple Silicon, representative Create/MTS/weather/DH gameplay, long soak, and full V1 cross-system tests remain acceptance work.

## 2. DrewCraft integration-mod platform — NEXT ACTIVE MILESTONE

Goal: create stable DrewCraft-owned boundaries before feature-specific bridges.

Build `mods/drewcraft/` as one NeoForge 1.21.1 / Java 21 integration mod with:

- mod/version identity;
- configuration and server-side feature flags;
- network/protocol boundary;
- versioned SavedData persistence foundation;
- admin/debug observability;
- test infrastructure and cheap CI.

Define upstream-independent services:

- `TerrainService`;
- `WeatherService`;
- `PowerService`;
- `VehicleService`.

Upstream implementation types stay inside adapter modules.

Exit gate: the custom mod compiles/tests independently, loads cleanly when later exercised, and has stable contracts that feature code can target.

## 3. Upstream capability/API audit — NEXT ACTIVE MILESTONE

Audit in this order:

1. Terrain Diffusion Plus;
2. Project Atmosphere;
3. Create;
4. MTS / Immersive Vehicles.

For each upstream identify public APIs/events, required state, client/server authority, cadence, threading assumptions, persistence/network implications, and the minimum necessary access strategy.

Preferred strategy:

**public API/event -> external adapter -> narrow accessor/mixin -> fork only as a last resort and only when licensing permits.**

Exit gate: a checked-in adapter capability matrix says exactly how DrewCraft can read/write the state required for V1.

## 4. Environment vertical slice

Implement Terrain Diffusion Plus + Project Atmosphere adapters first.

First proof: a server-side command such as `/drewcraft env sample` reports the environmental truth DrewCraft needs at a position: terrain/elevation/climate context plus available wind, temperature, pressure, humidity, precipitation, visibility, and severity.

Exit gate: the command samples both authorities through DrewCraft interfaces without feature code importing their implementation types.

## 5. Create power + MTS adapters

Create adapter:

- use **kinetic** power semantics, not a generic electrical abstraction;
- expose only the power availability/consumption semantics DrewCraft machines need.

MTS adapter:

- expose supported vehicle/aircraft pose, velocity, orientation, and instrument/control hooks;
- establish server/client authority for weather effects;
- avoid an MTS fork if an external adapter/accessor is sufficient.

Exit gate: DrewCraft can consume Create power and MTS vehicle state through stable internal contracts.

## 6. Aviation weather vertical slice

Prove:

`Terrain Diffusion Plus -> Project Atmosphere -> DrewCraft -> MTS`

Initial effects:

- headwind/tailwind/crosswind;
- bounded turbulence;
- storm/severity influence;
- visibility;
- terrain/elevation contribution;
- conservative synchronization/fallback behavior.

Exit gate: one supported aircraft experiences stable server-authoritative environmental effects without a parallel weather model.

## 7. Physical radar

Build radar on the same environment pipeline.

MVP:

- dish/antenna;
- controller;
- Create-powered adapter;
- data/connectivity path;
- cached shared scan;
- terrain/height horizon and coarse obstruction;
- physical display;
- aircraft weather-radar consumer using the same scan/product model.

Prioritize sensing correctness, cadence, caching, power, and terrain masking before decorative UI breadth.

Exit gate: differently sited/powered installations have meaningfully different coverage and display real Atmosphere-derived weather.

## 8. Strategic world kernel

Establish correctness before army content breadth.

Implement:

- stable strategic IDs;
- versioned persistence;
- coarse simulation clock;
- route/ETA engine;
- `SourceRecord`, `StrategicGroup`, and `HerdRecord` foundations;
- transactional/idempotent materialization;
- casualty reconciliation;
- safe dematerialization;
- restart/unload recovery;
- admin inspection commands.

Exit gate: an unloaded group advances consistently, materializes exactly once, records casualties, unloads without duplication, survives restart, and continues correctly.

## 9. Hostile sources and multiple forces

After the kernel is stable:

- index approved generated source structures;
- bind persistent source IDs/Source Cores;
- implement race-safe launch/clear lifecycle;
- implement patrols, warbands/hordes, raids, reinforcements, armies, and multiple compositions/factions;
- use geography, routes, source distance, and explainable target knowledge rather than omniscient player spawning;
- preserve already-deployed groups after source clearing.

Exit gate: clearing a legitimate source permanently stops future production while already-existing forces continue as real populations.

## 10. Siege planning

Implement path-first siege behavior:

1. normal path and entrance preference;
2. inaccessible-target detection;
3. useful breach-corridor selection;
4. siege-capable role assignment;
5. hardness/time-based breach;
6. protected-block rules;
7. plan caching/invalidation.

Critical behavior: open or viable entrances are used; sealed defenses may be deliberately breached; unrelated decorative builds are not arbitrary targets.

## 11. Strategic animal herds and local-spawn coexistence

Add unloaded persistent wild-herd records, coarse movement, coherent materialization, hunting/casualty reconciliation, and safe summarization.

Named/domesticated/leashed/penned/player-owned animals remain ordinary entities and must not be reabsorbed into wild-herd state.

Verify coexistence with ordinary local spawning, caves, mob farms, and normal spawners.

## 12. Production world pipeline

The successful smoke test is **not** production pregeneration.

On suitable/local hardware:

- choose/benchmark candidate world radius;
- generate with the exact locked generation profile;
- Chunky-pregenerate offline;
- record seed/settings/World Scale 2/border/generation identity;
- validate terrain/rivers/mountains/caves/structures/Nether/End;
- archive/checksum;
- restore onto a clean server;
- measure disk/compressed size, backup, restore, and traversal behavior.

Exit gate: a reproducible world artifact can be built, restored, and verified.

## 13. Host/performance gate

Oracle Ampere A1 is the first low-cost benchmark target, not a V1 identity requirement.

Measure representative pregenerated-world behavior, weather, Create, MTS, strategic materialization, MSPT percentiles, CPU, heap/native memory, GC, disk I/O, network, save/restart, and spark profiles.

If A1 is unsuitable, intentionally choose a larger/fixed host. Never hide a failed benchmark behind silent paid autoscaling.

## 14. Release, server deployment, and one-click launcher

Create one immutable release contract shared by launcher and server updater:

- versioned release manifest;
- stable-channel pointer;
- deterministic client/server artifacts;
- hashes and protocol/platform versions;
- separate world-artifact identity;
- staged server updates with backup/health/rollback;
- Windows bootstrapper;
- Apple Silicon macOS bootstrapper/app;
- managed Java 21 and Prism instance;
- Microsoft login delegated to Prism;
- atomic updates/repair/rollback;
- server readiness/version checks.

Exit gate: clean Windows and Apple Silicon machines can install/update/join without hand-managing Java/mods, and a test release update converges client/server automatically.

## 15. V1 cross-system integration and acceptance

Once all V1 systems exist, perform the expensive comprehensive test cycle locally/on the production candidate host rather than continuously burning GitHub Actions minutes.

Validate together:

- fresh install/world + persisted restart;
- Windows + Apple Silicon clients;
- long-distance travel and Distant Horizons;
- Create + MTS;
- Atmosphere -> aviation + ground radar + aircraft radar;
- source -> strategic force -> materialization -> casualties -> unload/restart;
- permanent source clearing and already-deployed-force semantics;
- siege grief safety;
- strategic herds + normal local mobs/farms;
- pregeneration/archive/restore;
- launcher/update/repair/rollback;
- long soak, spark/MSPT/memory/GC profiling;
- complete log/crash audit;
- licensing/redistribution audit.

Exit gate: the same candidate release satisfies the entire V1 contract reliably.

## Post-V1 / V1.1+

Only after playing the complete V1 system should DrewCraft broadly tune:

- recipes/acquisition costs;
- fuel/repair/maintenance economics;
- train/aircraft progression;
- road usefulness;
- exact source density and army frequency/difficulty;
- radar tier/crafting progression;
- extended portal-distance rules;
- other economy/difficulty balancing.

The purpose of V1.1+ is to balance an already complete integrated game, not to finish missing V1 architecture.
