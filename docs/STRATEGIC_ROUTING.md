# DrewCraft Strategic Routing Contract

**Scope:** BP2 / V1 strategic-world kernel  
**Status:** implementation contract for coarse unloaded movement

## Core rule

Strategic routing is not Minecraft pathfinding.

A distant group routes over a coarse 2D cost graph, persists the solved waypoint route, and then advances along that route using elapsed-time arithmetic. The scheduler never calls the route planner.

```text
route event
  destination changes / route invalidated
        ↓
coarse cost map + bounded A*
        ↓
persist solved StrategicRoute
        ↓
coarse scheduler advances cursor/progress only
        ↓
no route search until another meaningful route event
```

## Resolution

Default routing cells are **64×64 blocks**, configurable within bounded limits. This is intentionally much coarser than block navigation and independent of Minecraft chunk load state.

## Terrain-cost policy

The current V1 coarse categories are:

| Class | Cost multiplier | Traversable | Purpose |
| --- | ---: | --- | --- |
| `ROAD` | 0.65 | yes | preferred infrastructure |
| `BRIDGE` | 0.80 | yes | preferred crossing |
| `NORMAL` | 1.00 | yes | ordinary land |
| `UNKNOWN` | 1.25 | yes | conservative default when no indexed data exists |
| `DIFFICULT` | 1.75 | yes | steep/rough geography |
| `WATER` | 2.50 | yes | expensive crossing for generic land groups until faction rules specialize it |
| `BLOCKED` | ∞ | no | impassable strategic cell |

These are routing semantics, not final difficulty/balance values. Stage 19 profiling and V1.1 gameplay tuning may adjust multipliers.

## Terrain data source

The routing engine **never queries Terrain Diffusion or Minecraft chunks**.

`StrategicTerrainCostMap` is populated separately. Producers may include:

1. offline metadata derived from the final pregenerated world — preferred production path;
2. opportunistic sampling of already-loaded realized terrain;
3. explicit admin/test classification;
4. later road/bridge indexing.

`StrategicTerrainCapture` is deliberately separate from route search. It uses DrewCraft's existing realized-world terrain adapter; unloaded samples return unavailable and are not force-loaded.

Unknown cells remain explicit `UNKNOWN` rather than causing generation or a world scan.

## Route search bounds

The BP2 planner uses 8-neighbor A* with:

- a hard configurable expanded-node cap;
- a finite start/destination bounding box plus configurable detour padding;
- no diagonal corner-cutting through blocked cardinal cells;
- deterministic tie-breaking;
- explicit failure status when bounds are exhausted or endpoints are blocked;
- search timing and expanded-node diagnostics.

A route failure is data, not permission to run an unbounded search.

## Cache and invalidation

Solved routes use an LRU template cache keyed by:

- exact start position;
- exact destination;
- dimension;
- terrain-cost-map version.

Editing the terrain cost map increments its version. Old route templates therefore stop matching immediately without scanning every active group or periodically recomputing routes.

Already-deployed groups persist their own solved `StrategicRoute`; a server restart does **not** require A* to recreate the route they were already following.

Later gameplay events may intentionally mark selected groups for rerouting when a bridge/road/source/objective changes. That remains event-driven.

## Weighted movement and ETA

Terrain cost affects both path selection and traversal time.

Each persisted route segment has a positive cost multiplier. The group's base movement speed consumes weighted route-cost units per second:

```text
segment cost = physical segment length × terrain multiplier
ETA = remaining weighted route cost / group effective speed
```

Thus difficult/water terrain slows strategic physical progress even after the route has been solved. The scheduler still performs only simple route-segment arithmetic.

## Runtime/admin diagnostics

BP2 provides:

- `/drewcraft strategic destination <groupId> <x> <z>`
- `/drewcraft strategic route <groupId>`
- `/drewcraft strategic eta <groupId>`
- `/drewcraft strategic routing-perf`
- `/drewcraft strategic terrain capture-here`
- `/drewcraft strategic terrain set-here <class>`

`create-test` now creates a routed long-distance test group rather than an unsolved straight-line placeholder.

## Proof boundary

BP2 proves long-distance **strategic** movement and restart persistence without world/entity simulation. It does not materialize mobs. Materialization, casualty reconciliation, duplicate prevention, and encounter recovery are BP3.
