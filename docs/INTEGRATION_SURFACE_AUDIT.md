# DrewCraft Upstream Integration Surface Audit

**Audit date:** 2026-09-12  
**Target:** Minecraft 1.21.1 / NeoForge 21.1.250 / Java 21  
**Purpose:** identify the least-invasive integration surface for the frozen V1 authorities before DrewCraft bridge code depends on upstream implementation details.

This audit covers only the four authorities the DrewCraft integration layer must bridge directly:

1. Terrain Diffusion Plus;
2. Project Atmosphere;
3. Create;
4. Immersive Vehicles / Minecraft Transport Simulator (MTS).

The integration preference remains:

**public API/event -> isolated DrewCraft adapter -> narrow accessor/mixin -> maintained fork only as a last resort and only when licensing permits.**

No audit finding here reopens V1 mod selection.

## Source identity and artifact-binding rule

| Upstream | Selected runtime | Source inspected | Artifact/source confidence |
| --- | --- | --- | --- |
| Terrain Diffusion Plus | DrewCraft source build | `derekvawdrey/terrain-diffusion-plus@05fdcf5681cc53a9685325d714750b4427661a21` | **Exact**: this is the source commit DrewCraft builds |
| Project Atmosphere | `0.9.1.2` | `xGabou/Project-Atmosphere`, branch `NeoForge-1.21.1` | **Not exact**: no matching `0.9.1.2` Git tag was found; branch source is architectural evidence only |
| Create | `6.0.10` | tag `mc1.21.1-6.0.10` -> commit `ac0c444d9828da3453ae8cc65338e8de063286fb` | **Exact**: release tag matches selected version |
| MTS / Immersive Vehicles | `24.0.0` | `DonBruce64/MinecraftTransportSimulator`, `master` inspected at `b92e272bb59628310c8bb231e63c165208a2aaf3` | **Not exact**: no matching `24.0.0` Git tag was found; master is architectural evidence only |

**Implementation rule:** where an exact source/release binding is unavailable, DrewCraft must compile the adapter against the exact verified provider JAR acquired by the pack resolver. A moving upstream branch is never silently treated as the runtime release. Source inspection can tell us what integration patterns exist, but the exact JAR is the final compile/runtime authority.

## Executive capability matrix

| Authority | Needed by DrewCraft | Best current surface | Authority/side | Risk | Decision |
| --- | --- | --- | --- | --- | --- |
| Terrain Diffusion Plus | elevation, terrain/climate context | `LocalTerrainProvider` plus normal generated-world data | server/worldgen; expensive inference can occur | synchronous generation calls can block for seconds | isolated cached terrain adapter; never infer per tick |
| Project Atmosphere | wind, temperature, precipitation, clouds, storm state; later pressure/humidity | public read-only `AtmoApi` | server `ServerLevel` query | pressure/humidity are not in public `WeatherSnapshot` | use `AtmoApi`; seek/implement upstream read-only extension before using internals |
| Create | kinetic power availability/consumption | public stress registry + normal kinetic block-entity extension surface | server-authoritative kinetic network | some addon extension types live outside `api` package | normal Create addon adapter; no generic electricity layer, no mixin |
| MTS | vehicle/aircraft enumeration, position, velocity, orientation; later weather force/instruments | public MTS wrapper/entity classes for observation | MTS wrapper exists separately client/server | no clean external force-injection API identified | read-only adapter is straightforward; force injection needs a narrowly designed hook, not arbitrary field mutation |

## 1. Terrain Diffusion Plus

### Exact audited source

`derekvawdrey/terrain-diffusion-plus@05fdcf5681cc53a9685325d714750b4427661a21`

This is the same exact source commit used by DrewCraft's verified source build.

### Useful source surface

`common/src/main/java/com/github/xandergos/terraindiffusionmc/pipeline/LocalTerrainProvider.java` is a public class and exposes, among other methods:

- `init(long seed)`;
- `getInstance()`;
- `getSeed()`;
- `clearCache()`;
- `getPipelineData(...)`;
- `getPipelineCoarse(...)`;
- `getRiverTerrainData(...)`;
- `getExplorerDetailData(...)`;
- instance `fetchHeightmap(...)`.

The pipeline can expose elevation/climate arrays, biome indices, river-water masks/surfaces, and generated height information. The source also defines `TerrainClimateSample` with semantic fields including elevation, temperature, precipitation, moisture/aridity, slope, growing-season information, and terrain flags. This audit did not identify a stable top-level public query that simply returns that record for an arbitrary block position, so DrewCraft should not assume that record itself is the supported API boundary.

### Threading and cadence constraint

This is the most important Terrain Diffusion finding.

`LocalTerrainProvider` explicitly warns that a heightmap request can block for **10-30+ seconds** if the required neural tile is unavailable. Several convenience methods route inference through an internal executor but then wait on the returned future. Therefore a method being backed by an executor does **not** make a synchronous DrewCraft call non-blocking.

DrewCraft must never perform uncached Terrain Diffusion inference:

- every tick;
- in an aircraft physics hot path;
- in a radar scan inner loop;
- from arbitrary entity AI;
- while holding strategic-state locks.

### DrewCraft integration decision

Use an isolated terrain adapter with two tiers:

1. **Generated-world fast path.** For already generated/pregenerated chunks, prefer ordinary server-world data such as surface height/biome where it represents the fact DrewCraft needs. This avoids invoking neural generation merely to answer a gameplay query.
2. **Terrain Diffusion enrichment path.** Where DrewCraft genuinely needs TD+-specific climate/river fields, use the provider behind a bounded cache/background-prefetch boundary and never from a per-tick hot path.

The adapter should make cache miss/unknown explicit rather than stalling gameplay for an unbounded inference.

### Need for mixin/fork

- Public/source-visible access: **sufficient for first adapter spike**.
- Mixin/accessor: **not currently justified**.
- Fork: **not justified**.

## 2. Project Atmosphere

### Source inspected

`xGabou/Project-Atmosphere`, `NeoForge-1.21.1` branch.

The selected provider artifact is `0.9.1.2`. No matching Git tag was found, so the exact provider JAR remains the authority when the adapter is compiled.

### Strong public API

Project Atmosphere already contains an explicit package:

`net.Gabou.projectatmosphere.api`

`AtmoApi` describes itself as the public-facing, read-only API and exposes server-position queries including:

- `getCurrentWeather(ServerLevel, BlockPos)`;
- `getWeatherSnapshot(ServerLevel, BlockPos, long gameTime)`;
- forecast-region access;
- read-only weather convenience checks;
- `registerWorldEffect(AtmosphereWorldEffect)`.

`WeatherSnapshot` contains:

- cloud cover;
- rain intensity;
- temperature in Celsius;
- wind speed in m/s;
- wind angle in radians;
- storming flag;
- snowing flag.

This is exactly the sort of upstream-owned query surface DrewCraft should consume rather than reproducing Atmosphere internals.

### Pressure/humidity gap

Live `RegionAtmosphereState` contains public getters for temperature, humidity/humidity percent, pressure, wind, cloud cover, cloud water, and related state. However, pressure and humidity are not currently carried by the public `WeatherSnapshot`.

Those values are desirable for aviation instruments and richer radar/weather products, but importing internal registry/state packages directly would turn an otherwise clean API integration into a brittle implementation dependency.

### DrewCraft integration decision

For the first environment slice:

- use `AtmoApi` directly for its supported fields;
- sample on the logical server;
- cache a composed DrewCraft weather sample for consumers that need repeated reads in one tick/scan;
- treat pressure/humidity as temporarily unavailable rather than reaching immediately into Atmosphere internals.

Preferred pressure/humidity solution: a tiny upstream-compatible read-only API extension (for example, adding them to a richer snapshot/query) or another documented public accessor. If that is not possible, isolate any internal read behind the Atmosphere adapter only; no core DrewCraft type may expose Atmosphere classes.

One small source-quality note: the inspected `getWeatherForecast(ServerLevel, BlockPos, ForecastType)` implementation accepts a `ForecastType` parameter but currently delegates without using that parameter. DrewCraft should not build behavior that assumes the parameter selects a distinct forecast until verified against the exact 0.9.1.2 JAR.

### Need for mixin/fork

- Public API for initial weather: **yes**.
- Pressure/humidity: **API gap**.
- Mixin/accessor: **avoid for now**; a public read-only extension is preferable.
- Fork: **strongly avoid**; selected source is All Rights Reserved and a fork/redistribution path must not be assumed legal.

## 3. Create

### Exact audited source

Selected runtime `6.0.10` maps to Git tag `mc1.21.1-6.0.10`, commit:

`ac0c444d9828da3453ae8cc65338e8de063286fb`

### Kinetic power surface

Create already provides a formal API package for stress values:

`com.simibubi.create.api.stress.BlockStressValues`

It exposes registries and getters for block stress impact/capacity. The ordinary kinetic implementation also provides the established addon extension surface around `KineticBlockEntity`.

Relevant public kinetic state includes:

- `getSpeed()`;
- `isOverStressed()`;
- normal kinetic network attachment/update behavior;
- stress impact/capacity calculation based on `BlockStressValues`.

Importantly, `getSpeed()` returns zero when the network is overstressed, which is useful for a DrewCraft machine's effective-powered state.

### DrewCraft integration decision

Radar and other DrewCraft infrastructure should be native **Create kinetic consumers**, not consumers of a second abstract electrical-energy system.

The eventual Create adapter should expose only DrewCraft concepts such as:

- connected/kinetically available;
- effective RPM/direction where needed;
- required stress impact for the DrewCraft machine;
- operational/not operational.

A radar controller or power-input block can use the normal Create addon extension pattern and register its stress impact. Radar logic above that adapter must not import Create classes.

### Threading/cadence

Kinetic network state is ordinary game/server state and should be sampled on the logical server. There is no reason for global scans: each DrewCraft machine should read its local attached kinetic state and react to network updates/ticks using normal block-entity lifecycle behavior.

### Need for mixin/fork

- Public API/addon surface: **sufficient**.
- Mixin/accessor: **not justified**.
- Fork: **not justified**.

## 4. Immersive Vehicles / MTS

### Source inspected

`DonBruce64/MinecraftTransportSimulator`, `master` at:

`b92e272bb59628310c8bb231e63c165208a2aaf3`

Selected runtime is `24.0.0`. No matching Git tag was found, so exact-provider-JAR compile verification is mandatory before relying on any inspected class/member.

### Read-only vehicle observation is viable

MTS exposes a useful public internal abstraction layer.

`AEntityB_Existing` exposes public world-state fields including:

- `position`;
- `orientation`;
- `prevPosition` / `prevOrientation`;
- `motion` / `prevMotion`;
- velocity.

`EntityManager` exposes entity lookup/enumeration including typed entity collections. On NeoForge 1.21.1, `mcinterface1211.WrapperWorld.getWrapperFor(Level)` maps a Minecraft `Level` to MTS's per-world wrapper, and that wrapper inherits the entity manager.

That gives a straightforward isolated read adapter:

`ServerLevel -> MTS WrapperWorld -> EntityVehicleF_Physics collection -> DrewCraft vehicle snapshots`

No global reflection scan is required.

### Physics-injection gap

Aircraft physics is calculated in `EntityVehicleF_Physics`. The relevant force/motion method is protected, while its principal force accumulators are private. The inspected code computes aerodynamic forces from the vehicle's own motion/air density and then directly applies them to `motion`.

This means DrewCraft should **not** implement weather by casually mutating MTS public `motion` fields from a separate tick handler. Doing so would be order-dependent, difficult to reason about, and would not correctly make aerodynamic forces depend on air-relative velocity.

No dedicated external environmental-force/wind callback was identified in this audit.

### DrewCraft integration decision

Split MTS work into two capability levels:

1. **Observation/instruments:** build first. Read position, motion, orientation and vehicle identity through the public wrapper/entity surface and translate into DrewCraft-owned snapshots.
2. **Flight-force integration:** design separately. Preferred solution is a small upstream extension hook/callback that lets an addon supply environmental air velocity/force at the correct physics stage. If the exact 24.0.0 JAR offers no such hook and upstream extension is not practical, use one narrowly targeted DrewCraft mixin at the force-calculation boundary with a dedicated compatibility test.

Do not modify MTS source or maintain a redistributed fork merely to inject wind unless both technical necessity and license permission are established.

### Need for mixin/fork

- Read-only vehicle API: **sufficient for initial adapter**.
- Weather-force injection: **gap; likely upstream hook or one narrow mixin**.
- Fork: **last resort / licensing concern** because MTS is All Rights Reserved.

## Thread/authority policy for all adapters

DrewCraft adapters should default to these rules unless exact upstream documentation proves a stronger guarantee:

- mutable game state is read/written on the logical server thread;
- adapters return immutable DrewCraft snapshots, not live upstream objects;
- expensive terrain/weather products are cached at an appropriate spatial/time granularity;
- no adapter performs global per-tick scans;
- no asynchronous task mutates Minecraft/upstream world state directly;
- client code consumes synchronized DrewCraft products only when a feature actually requires client rendering/instruments;
- third-party types stop at the adapter boundary.

## Immediate implementation consequences

The audit clears the following next implementation work without any additional mod selection:

1. define upstream-independent `TerrainService`, `WeatherService`, `PowerService`, and `VehicleService` contracts;
2. compile adapter modules against exact verified runtime artifacts, not moving source branches;
3. implement Terrain Diffusion Plus + Project Atmosphere first;
4. prove `/drewcraft env sample` on the server with bounded/cached terrain behavior;
5. implement Create kinetic power through normal addon APIs;
6. implement MTS read-only vehicle snapshots before touching flight forces;
7. design the MTS wind-force hook as its own compatibility decision and test.

## Current blocker summary

There is no blocker requiring a new gameplay mod or a fork.

The only notable API gaps found are:

- Project Atmosphere public snapshot does not expose pressure/humidity even though its live region state contains them;
- MTS does not expose an obvious external wind/environment force hook at the audited physics boundary;
- Terrain Diffusion Plus source access is usable, but expensive synchronous inference must be kept out of live hot paths.

Those are adapter/API-engineering problems, exactly the class of work the DrewCraft integration mod is intended to contain.
