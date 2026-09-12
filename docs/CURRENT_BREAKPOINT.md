# DrewCraft Current Development Breakpoint

**Updated:** 2026-09-12  
**Protocol:** `docs/DEVELOPMENT_BREAKPOINTS.md`  
**Last completed breakpoint:** **BP1 — Strategic persistence + coarse simulation substrate**  
**Next breakpoint:** **BP2 — Coarse terrain routing + ETA + unloaded travel proof**

## BP1 status — REACHED

BP1 is complete at compile/unit/runtime-wiring scope.

Implementation includes:

- versioned `StrategicGroup` records with stable UUID identity;
- dimension-aware continuous `StrategicPosition`;
- faction, type, optional source identity, composition, total strength, movement speed, state, and simulation-time anchor;
- cached `StrategicRoute` waypoint list + cursor;
- arithmetic elapsed-time movement across cached route segments;
- deterministic group NBT serialization with explicit group schema and future-schema rejection;
- `DrewCraftSavedData` schema **2**, including migration from schema 0/1 to an empty strategic registry and persistent strategic-group storage;
- deterministic group save ordering and duplicate-ID rejection on load;
- bounded `StrategicScheduler` registered on NeoForge `ServerTickEvent.Post`;
- default coarse cadence of 100 ticks (5 seconds), configurable;
- hard groups-per-cycle cap;
- soft milliseconds-per-cycle budget;
- explicit catch-up-seconds cap;
- completed/arrived groups stop consuming scheduler update/save work;
- scheduler performs no chunk loads, entity creation, Minecraft navigation, terrain sampling, A*, Dijkstra, or other route search;
- server-side strategic feature flag enabled because no groups exist automatically unless created/admin systems later add them;
- admin diagnostics:
  - `/drewcraft strategic create-test`
  - `/drewcraft strategic list`
  - `/drewcraft strategic inspect <groupId>`
  - `/drewcraft strategic step <seconds>`
  - `/drewcraft strategic perf`
- `/drewcraft status` reports strategic-group count.

Focused tests cover:

- multi-segment cached-route movement;
- remaining-distance math;
- bounded catch-up and excess-time discard;
- deterministic destination arrival;
- group NBT round trip;
- future group-schema rejection;
- world SavedData schema-1 migration;
- world SavedData strategic-group round trip;
- future world-schema rejection;
- scheduler group-count budget/deferred work.

## Evidence

- implementation head before this status-only commit: `216bdd4ad30de71059bf164e7c3b276173585d0c`
- DrewCraft mod CI: **run `34725983660` — SUCCESS**
- CI job: `build-and-test` — **SUCCESS**
- Java: 21
- command executed by CI: `gradle -p mods/drewcraft test build --stacktrace --no-daemon`

## Important boundary

BP1 deliberately does **not** generate routes. The only route used so far is an already-cached/supplied waypoint route. This is intentional: it proves that distant populations can persist and advance essentially for free before route-search complexity is introduced.

No ordinary Minecraft mobs are created by BP1. No chunks are kept loaded for strategic movement.

## Next: BP2

On the next **"go"**, continue until BP2 is reached. BP2 adds:

1. a coarse terrain-cost representation/cache that never triggers Terrain Diffusion generation at route time;
2. bounded coarse A*/Dijkstra-equivalent routing;
3. route caching and event-driven invalidation;
4. ETA from remaining route cost/distance;
5. route/performance diagnostics;
6. destination/route/ETA admin commands;
7. the first long-distance unloaded movement + persistence/restart proof.

Stop and report again when BP2 passes its acceptance evidence. Do not begin BP3 materialization until the user says **"go"** after that report.
