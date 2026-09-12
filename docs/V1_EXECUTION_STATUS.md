# DrewCraft V1 Execution Status

**Last updated:** 2026-09-12  
**Current phase:** certified base stack -> integration platform / environment slice  
**Canonical contracts:** `docs/v_1_requirements.md` and `docs/v_1_development_tree.md`

This file is the live execution-state overlay for DrewCraft V1. The requirements document defines the V1 contract; the development tree defines dependency order; this file records which gates have actually passed and what work is next.

## Certified V1 base

The Minecraft 1.21.1 / NeoForge 21.1.250 / Java 21 `stage2_base_performance` profile is the frozen V1 integration baseline.

- **31 dependencies total:** 30 provider artifacts + one exact Terrain Diffusion Plus source build.
- Terrain/world authority: **Terrain Diffusion Plus**.
- Weather authority: **Project Atmosphere**.
- Industry/power language: **Create**.
- Vehicle/aircraft platform: **Immersive Vehicles / MTS**.
- Distant terrain: **Distant Horizons**.
- Pregeneration tool: **Chunky**.
- Additional gameplay/content mods are frozen unless an already-selected dependency exposes a genuinely mandatory transitive requirement.

### Baseline certification evidence

Full verified-profile reconstruction: GitHub Actions run **34702233400**, success.

Dedicated-server baseline certification: run **34704011609**, job **103580655867**, commit `4259d0ccf0e10f34298f744c42b253a1c08603d0`, success.

That smoke test proved:

1. exact Terrain Diffusion Plus source checkout and NeoForge CPU build;
2. exact verified server mod-tree reconstruction;
3. pinned NeoForge installation;
4. fresh Terrain Diffusion Plus world creation and Minecraft readiness;
5. clean shutdown;
6. same-world restart and readiness;
7. second clean shutdown;
8. fatal-log-pattern scan.

Smoke evidence artifact: **10303917312**; digest `sha256:52ecf4981cadcf5b9d4443665f30e03fbe8d8a27a7b363be0d7e23781f4b5a07`.

Observed timing on that runner was roughly **26 minutes** for the fresh TD+ world boot and roughly **2 minutes** for the persisted-world restart. The workflow deliberately did not Chunky-pregenerate a production-scale map.

The earlier runtime blocker where Gabou's Libs required Architectury API `>=13.0.8` is resolved by the pinned NeoForge Architectury API **13.0.11** artifact.

## DrewCraft integration-platform progress

### Steps 1-2: scaffold and upstream audit — DONE

`mods/drewcraft/` is a NeoForge 1.21.1 / Java 21 integration mod with configuration, feature flags, diagnostics, protocol/version boundaries, versioned SavedData, tests, and cheap compile/unit CI.

`docs/INTEGRATION_SURFACE_AUDIT.md` records the integration surfaces for Terrain Diffusion Plus, Project Atmosphere, Create, and MTS. Integration preference remains:

**public API/event -> isolated DrewCraft adapter -> narrow accessor/mixin -> maintained fork only as a last resort and only when licensing permits.**

### Step 3: DrewCraft-owned service contracts — DONE

Core gameplay systems now depend on DrewCraft contracts rather than upstream implementation classes:

- `TerrainService` / `TerrainSample`;
- `WeatherService` / `WeatherSample`;
- `PowerService` / `PowerSample`;
- `VehicleService` / `VehicleSnapshot` / `VehicleQueryResult`.

The weather contract explicitly has optional slots for pressure, humidity, visibility, and normalized severity. Missing upstream values remain unavailable; DrewCraft does not fabricate them.

### Step 4: first terrain/weather adapters — DONE for the initial slice

**Terrain Diffusion Plus:** `TerrainDiffusionTerrainService` samples already-realized server-world terrain only. It reports surface elevation, biome, surface block, and sea level. It does **not** force-load unloaded chunks and does **not** call neural inference. This is a hard boundary for future flight/radar/strategic hot paths.

**Project Atmosphere:** `ProjectAtmosphereWeatherService` consumes the upstream read-only `AtmoApi` surface and converts `WeatherSnapshot` into DrewCraft-owned immutable data. The public snapshot currently supplies cloud cover, rain intensity, temperature C, wind speed m/s, wind angle radians, storming, and snowing. Pressure, humidity, visibility, and severity remain explicit `n/a`/unavailable values until there is a supported source for them.

Because the selected Atmosphere `0.9.1.2` artifact has no exact matching Git tag, the adapter uses an isolated fail-closed reflection boundary rather than exposing moving branch types to DrewCraft core code. An upstream API-shape mismatch produces an unavailable sample instead of a server crash.

### Step 5: first environment vertical slice — DONE at compile/unit level

Admin command:

```text
/drewcraft env sample
```

samples the command source's current position and reports the composed terrain/weather state, including explicit `n/a` values for environmental quantities the current upstream public API does not expose.

The ordinary DrewCraft CI compiles the mod and runs focused unit tests without installing the full pack, downloading TD+ models, or generating a Minecraft world. Run **34710576298**, job **103598502645**, passed production compilation and tests after the test source set was correctly given the Minecraft/NeoForge classpath.

This milestone is **compile/unit/API-shape validated**, not a claim that a new expensive full-stack world boot was performed. Live full-pack integration observation remains part of the later local/V1 acceptance cycle unless a blocking issue specifically requires an earlier targeted runtime test.

## CI policy after baseline certification

The successful dedicated-server smoke is the baseline certification run. Until V1 is substantially complete:

- use manifest/schema/unit/compile/targeted tests on ordinary commits;
- do not automatically rerun the full TD+ fresh-world smoke for bridge development;
- do not Chunky-pregenerate production scale in GitHub Actions;
- repeat the expensive full-stack boot only if an unavoidable base/platform change invalidates certification, or at V1 acceptance;
- prefer the final comprehensive acceptance run locally/on dedicated hardware so logs, clients and `spark` profiling can be inspected without burning hosted CI minutes.

## Gate status

| Gate | State | Evidence / remaining condition |
| --- | --- | --- |
| Reproducible manifest/resolver | **PASS** | Exact profile reconstruction works in CI |
| Provider/source/platform locks | **PASS** | 30 provider artifacts + TD+ source provenance + NeoForge 21.1.250 |
| Dedicated-server fresh boot/restart | **PASS** | Run 34704011609 |
| Base mod additions | **FROZEN** | Integration/compatibility/optimization only by default |
| DrewCraft mod scaffold + persistence | **PASS** | Module and cheap CI established |
| Four upstream-independent service contracts | **PASS** | Step 3 implemented |
| TD+ realized-world adapter | **PASS: compile/unit scope** | No force-load/inference query path |
| Project Atmosphere adapter | **PASS: compile/unit scope** | Public snapshot, fail-closed boundary |
| `/drewcraft env sample` | **PASS: compile scope** | Step 5 implemented; live full-stack observation deferred |
| Create kinetic bridge | **NEXT** | Step 6 |
| MTS observation | **BLOCKED ON STEP 6 SEQUENCE ONLY** | Step 7A |
| Aviation/weather physics | **BLOCKED ON 7A** | Step 7B; proper air-relative physics hook required |
| Radar sensing engine | **BLOCKED ON 6 + environment services** | Step 8A |
| Physical radar / aircraft display | **BLOCKED ON 8A** | Step 8B |
| Strategic-world kernel | **OPEN AFTER INTEGRATION PLATFORM** | Step 9: IDs, clock, routes, materialization, sources/groups/herds |
| Production world/pregen/restore | **OPEN** | Later representative-world gate |
| ARM/production host benchmark | **OPEN** | Benchmark after representative world exists |
| Launcher/release/deployment | **OPEN** | Build against immutable release contract |
| V1 full-stack acceptance | **OPEN** | Local/host/client/soak/restart/profiling gate |

## Immediate next sequence

The next integration milestones are deliberately kept separate and reviewable:

1. **6 — Create kinetic bridge:** implement `PowerService` using Create's kinetic network/stress semantics; no generic electricity layer.
2. **7A — MTS observation:** implement `VehicleService` for vehicle identity, position, velocity, orientation, and aircraft classification.
3. **7B — aviation/weather physics:** connect DrewCraft weather to MTS using a proper air-relative force/air-velocity hook; avoid arbitrary post-physics velocity mutation.
4. **8A — radar sensing engine:** atmospheric scan field, terrain horizon/masking, antenna-height effects, scan cadence/cache, range/tier model, and Create-power gating.
5. **8B — physical radar + aircraft display interface:** dish/controller/display gameplay surface and aircraft radar presentation built on the same 8A scan product.

After those, **9** is the strategic-world kernel. Do not jump ahead to army/siege/herd breadth before the persistence/materialization kernel is correct.
