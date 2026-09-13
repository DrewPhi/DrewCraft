# DrewCraft Current Development Breakpoint

**Updated:** 2026-09-12  
**Protocol:** `docs/DEVELOPMENT_BREAKPOINTS.md`  
**Last completed breakpoint:** **BP2 — Coarse terrain routing + ETA + unloaded travel proof**  
**Next breakpoint:** **BP3 — Transactional materialization + casualty reconciliation**

## BP2 status — REACHED

BP2 is complete at compile/unit/runtime-wiring scope. Together BP1 + BP2 complete the Stage 11 strategic-world kernel proof.

Implementation includes:

- coarse dimension-aware `StrategicCell` grid;
- configurable default cell size of 64×64 blocks;
- explicit terrain classes and traversal policy:
  - `ROAD` 0.65×;
  - `BRIDGE` 0.80×;
  - `NORMAL` 1.00×;
  - `UNKNOWN` 1.25× conservative default;
  - `DIFFICULT` 1.75×;
  - `WATER` 2.50×;
  - `BLOCKED` impassable;
- versioned `StrategicTerrainCostMap` that contains no world/chunk access;
- opportunistic `StrategicTerrainCapture` for already-loaded realized terrain only;
- no route-time Terrain Diffusion inference or forced chunk loads;
- bounded 8-neighbor A* routing with:
  - hard expanded-node cap;
  - finite detour bounding box;
  - deterministic tie-breaking;
  - no diagonal corner-cutting through blocked cells;
  - explicit route-failure statuses;
  - search CPU/expanded-node diagnostics;
- weighted persisted route segments so terrain affects both route choice and actual travel time;
- ETA from remaining weighted route cost / effective group speed;
- `StrategicGroup` schema **2** with migration of schema-1 flat routes to 1.0 cost multipliers;
- exact solved route + route cursor persisted with each group, so restart does not require rerunning A*;
- deterministic LRU `StrategicRouteCache` keyed by exact endpoints, dimension, and terrain-map version;
- event-driven cache invalidation: terrain changes increment map version instead of triggering periodic global reroutes;
- the coarse scheduler remains route-search-free and only advances persisted route segments;
- configuration bounds for cell size, expanded nodes, detour padding, and route-cache entries;
- admin/debug surface:
  - `/drewcraft strategic create-test` — now creates a routed 10,000-block test group;
  - `/drewcraft strategic destination <groupId> <x> <z>`;
  - `/drewcraft strategic route <groupId>`;
  - `/drewcraft strategic eta <groupId>`;
  - `/drewcraft strategic routing-perf`;
  - `/drewcraft strategic terrain capture-here`;
  - `/drewcraft strategic terrain set-here <class>`;
- routing architecture documented in `docs/STRATEGIC_ROUTING.md`.

## BP2 acceptance evidence

Focused tests now cover:

- blocked-cell detours and no blocked-corner diagonal cuts;
- explicit blocked-destination failure;
- terrain-weighted ETA and slower physical movement on expensive terrain;
- hard A* node-expansion failure instead of unbounded search;
- conservative unknown-cell policy;
- terrain-map version changes only on effective mutations;
- route-cache hit/miss behavior;
- terrain-version cache invalidation;
- independent mutable route cursors for cached route templates;
- water/difficult/normal realized-terrain classification;
- weighted-route NBT round trip;
- migration of schema-1 flat routes;
- **10,000-block strategic journey through the actual coarse scheduler**;
- mid-journey NBT save/reload as a restart boundary;
- persisted route cursor/multipliers/progress after reload;
- post-restart arrival at the original destination;
- the long-distance proof uses no Minecraft world, chunk, or entity object.

### CI

- final implementation/test head before this status-only commit: `e474015bd16d35659023811938692478567d7819`
- DrewCraft mod CI: **run `34726857058` — SUCCESS**
- CI job: `build-and-test` — **SUCCESS**
- command: `gradle -p mods/drewcraft test build --stacktrace --no-daemon`
- earlier dedicated unloaded-travel proof run `34726835776` also passed.

A separate run (`34726754559`) failed during the GitHub Gradle setup action before compile/test and is not a code failure; subsequent runs completed compile/test successfully.

## Important production boundary

The routing algorithm is complete, but the final production terrain-cost index is intentionally not fabricated in BP2.

The preferred production path is for the final pregenerated world pipeline to populate coarse terrain metadata offline. Until a cell is indexed, it remains the explicit conservative `UNKNOWN` class. Already-loaded cells can be captured opportunistically without loading new chunks.

This means BP2 proves the routing/simulation architecture without violating the rule that live strategic routing must not trigger Terrain Diffusion generation or globally load terrain.

## Next: BP3

On the next **"go"**, continue until BP3 is reached.

BP3 adds the highest-correctness-risk transition in DrewCraft:

1. persistent encounter UUID + materialization state machine;
2. duplication-safe strategic → tactical transaction;
3. durable mob tags mapping entities to group/encounter;
4. bounded active-entity/wave budget;
5. idempotent casualty accounting;
6. safe dematerialization/reconciliation;
7. restart recovery from materializing/materialized/dematerializing states;
8. canonical `100 → fight → 63 → unload → restart → 63` proof;
9. two players approaching simultaneously cannot duplicate the encounter.

Stop and report again when BP3 passes its acceptance evidence. Do not begin BP4 hostile sources until the user says **"go"** after that report.
