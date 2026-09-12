# DrewCraft V1 — Remaining Execution Plan

**Status date:** 2026-09-12  
**Starting point:** Step 8B physical ground radar/weather integration implemented at code/manifest/hash scope  
**Finish condition:** one exact release candidate passes the hard V1 acceptance matrix and is tagged `1.0.0`

This document is the **canonical detailed plan for the remaining work from the post-8B state to DrewCraft V1**. It supplements:

- `docs/v_1_requirements.md` — hard product contract;
- `docs/v_1_development_tree.md` — dependency-order overview;
- `docs/V1_EXECUTION_STATUS.md` — live gate/evidence status;
- `docs/STRATEGIC_WORLD_MODEL.md` — strategic-world behavior contract;
- `docs/SOURCE_CORE_SPEC.md` — source-clear transaction semantics;
- `docs/RADAR_V1.md` — V1 radar scope amendment.

If this plan conflicts with a hard V1 requirement, the requirement wins. If it conflicts with an older implementation detail in the development tree, this document describes the current post-8B execution plan.

---

# 1. Governing execution rules

## 1.1 V1 is integration-complete, not balance-complete

Do not expand the remaining schedule with broad recipe, fuel, economy, spawn-rate, progression, or difficulty tuning. Only change an upstream default before V1 when it clearly breaks a defining DrewCraft pillar.

## 1.2 Simulate only what players can meaningfully observe

The strategic world is **not an always-running RTS simulation**.

Hard invariant:

> **Unloaded/distant strategic populations are compact persistent records. They do not keep chunks loaded, they do not run ordinary Minecraft entity AI, and they do not continuously recompute full routes.**

The intended simulation hierarchy is:

```text
FAR / UNLOADED
  persistent StrategicGroup record
  cached coarse route
  elapsed-time position advancement
  no entities
  no Minecraft pathfinding
  no siege planner

NEAR / PRE-MATERIALIZATION
  strategic record still authoritative
  local arrival/materialization planning only
  bounded work budget

LOADED / PLAYER-OBSERVABLE
  bounded real entities/waves
  normal tactical AI/pathfinding
  siege planner only if ordinary navigation cannot solve the encounter
  casualties reconcile back to the strategic record
```

A 600-strength army may therefore have zero loaded entities while distant and perhaps 40-80 active entities at once during a loaded battle. Total strategic strength remains real even when tactical materialization is capped.

## 1.3 Route computation is event-driven and cached

A strategic route is computed when needed and then reused. Recompute only when one of these occurs:

- a destination/objective changes;
- the current route becomes invalid;
- a relevant route-cost layer changes materially;
- a group is explicitly rerouted by gameplay/admin state;
- a cached route expires under an intentional policy.

Do **not** run A*/Dijkstra every tick or for every group on every strategic update.

## 1.4 Coarse simulation cadence is acceptable

Distant groups should advance using `distance = effectiveSpeed * elapsedTime`, not per-tick movement. Scheduler cadence may vary by priority/distance, e.g. nearby/high-priority groups every few seconds and very remote groups much less often. Correct elapsed-time advancement matters more than update frequency.

## 1.5 Every stage has a real gate

A stage is not complete because a class exists. It is complete only when its acceptance test passes, including restart/unload behavior when persistence is involved.

## 1.6 Parallel tracks are allowed only when dependencies permit

The strategic-world critical path should continue sequentially. Production-world, infrastructure, release tooling, server updater, and launcher work should proceed in parallel where they do not depend on unfinished strategic semantics.

---

# 2. Remaining critical path at a glance

```text
CURRENT: 8B radar implemented

11  Strategic-world kernel
    persistence + IDs + scheduler + coarse route/ETA
        ↓
12  Materialization / dematerialization transaction
    identity + bounded entities + casualty reconciliation
        ↓
13  Hostile-source lifecycle
    real generated source → persistent SourceRecord → clear transaction
        ↓
14  Factions / patrols / hordes / raids / armies
    data-driven strategic population breadth
        ↓
15  Siege planner
    path first → deliberate bounded breach only when needed
        ↓
16  Strategic animal herds
    reuse strategic kernel with ownership/domestication exclusions
        ↓
17  Local-spawn coexistence
    prove strategic simulation is additive to Minecraft ecology
        ↓
18  Cross-system gameplay scenarios
    weather + radar + aviation + transport + strategic world together
        ↓
19  Performance / scale hardening
        ↓
20  Crash / persistence / backup / recovery hardening
        ↓
21  V1 release candidate freeze
        ↓
22  Hard V1 acceptance
        ↓
TAG 1.0.0
```

Parallel tracks beginning now:

```text
A. production world / pregeneration / restore
B. production host / ARM benchmark
C. immutable release artifact contract
D. server deploy/update/backup system
E. Windows + Apple Silicon launcher/install/update experience
```

The strategic critical path and these operational tracks converge at Stage 21.

---

# 3. Stage 11 — Strategic-world kernel

## Goal

Prove that one important population can exist, move across unloaded geography, survive restart, and arrive near a predicted ETA without any loaded entity simulation.

This stage deliberately contains **no automatic camps, armies, sieges, or herd breadth**. It proves the kernel they all reuse.

## 11.1 Package/module boundary

Create a strategic package with narrow responsibilities, approximately:

```text
dev.drewcraft.strategic
  model/
  persistence/
  simulation/
  routing/
  command/
  diagnostics/
```

Keep Minecraft entity-specific materialization out of the kernel until Stage 12.

## 11.2 Persistent schema

Add versioned persistent records for at least:

```text
StrategicGroup
  groupId: UUID
  schemaVersion
  factionId
  groupType
  sourceId: optional UUID
  dimension
  strategicPosition
  destination/objective
  routeId / route snapshot
  routeCursor
  effectiveMovementSpeed
  composition
  totalStrength
  state
  lastSimulatedGameTime / elapsed-time anchor
  encounterId: optional UUID
  metadata
```

Requirements:

- stable UUID identity;
- explicit schema version from first committed format;
- deterministic serialization;
- unknown/future schema rejects visibly rather than silently resetting;
- no object identity depends on a currently loaded entity or chunk;
- save mutation paths are centralized and testable.

## 11.3 Strategic position representation

Use a coarse world representation independent of loaded chunks. The exact final cell size should be configurable/benchmarkable, but start with a sensible coarse cell such as chunks or small multi-chunk regions.

Position must support:

- dimension;
- continuous progress along a route rather than cell-to-cell teleportation;
- conversion to approximate world coordinates for diagnostics/materialization;
- deterministic persistence across restart.

## 11.4 Scheduler / simulation clock

Implement a server-side strategic scheduler with bounded work.

Rules:

- no global work every Minecraft tick;
- update due groups in batches;
- use elapsed time since `lastSimulated...`;
- cap catch-up after long downtime to an explicit maximum policy;
- expose number of groups processed, deferred, route-recomputed, and elapsed CPU time;
- prioritize nearby/active-objective groups over irrelevant remote groups if a budget is exceeded;
- scheduler failure for one malformed record must not corrupt all strategic state.

Suggested configuration knobs:

```text
strategic.enabled
strategic.schedulerIntervalTicks
strategic.maxGroupsPerCycle
strategic.maxMillisPerCycle
strategic.maxCatchupSeconds
strategic.nearPriorityRadius
```

The exact values are provisional until Stage 19 profiling.

## 11.5 Coarse terrain-cost service

Build a routing-cost abstraction that consumes only data that can be obtained without live global chunk loading.

V1 cost categories should support at least:

- normal traversable land;
- steep/difficult terrain;
- water;
- blocked/impassable cells;
- road/bridge bonuses when those layers become available safely.

Important: Terrain Diffusion is not invoked at route time. Prefer pregenerated/offline-derived or cached world metadata. If a region's cost is unknown, use an explicit conservative/default policy rather than forcing generation.

## 11.6 Route engine

Implement bounded A*/Dijkstra or equivalent over the coarse graph.

Requirements:

- deterministic enough for debugging/restart;
- bounded search radius/node count;
- route cache keyed by meaningful route inputs;
- no full-world scan;
- route failure is explicit;
- ETA derives from remaining route cost/distance and effective speed;
- route calculation timing is instrumented.

Route invalidation should be event-driven, not periodic by default.

## 11.7 Movement advancement

For a cached route:

1. compute elapsed simulation time;
2. convert to strategic movement budget;
3. advance route cursor/progress mathematically;
4. update position;
5. clamp at destination;
6. transition group state when destination is reached;
7. persist on meaningful state change according to safe save cadence.

This operation should be O(number of route segments actually crossed), not O(world size).

## 11.8 Admin/debug surface

Add commands roughly equivalent to:

```text
/drewcraft strategic create-test
/drewcraft strategic list
/drewcraft strategic inspect <groupId>
/drewcraft strategic destination <groupId> <x> <z>
/drewcraft strategic route <groupId>
/drewcraft strategic eta <groupId>
/drewcraft strategic tick <groupId|all>
/drewcraft strategic perf
```

Commands are admin/debug tools, not player-facing gameplay requirements.

## 11.9 Stage 11 tests

Unit tests:

- serialization round trip;
- schema rejection/migration skeleton;
- route progress math;
- ETA math;
- route cache hit/miss/invalidation;
- scheduler work budgeting;
- catch-up clamp;
- deterministic destination arrival.

Integration proof:

1. create one test group;
2. assign a destination thousands of blocks away;
3. verify a coarse route and ETA exist;
4. unload all relevant chunks;
5. advance real/game time;
6. restart server;
7. inspect group after restart;
8. verify it continued from persisted progress;
9. allow it to arrive;
10. compare actual strategic arrival to predicted ETA within the configured coarse-model tolerance.

## Stage 11 exit gate

**PASS only when one group travels across unloaded geography and survives restart with no entities, no forced chunk loads, no continuous path recomputation, and a credible ETA.**

---

# 4. Stage 12 — Materialization / dematerialization transaction

## Goal

Safely transform a strategic population into actual Minecraft entities near players and reconcile it back without duplication or strength reset.

This is the highest correctness-risk stage in the remaining strategic system.

## 12.1 Encounter identity

Introduce a persistent `encounterId` and explicit state machine, for example:

```text
STRATEGIC
MATERIALIZING
MATERIALIZED
DEMATERIALIZING
STRATEGIC
DESTROYED
```

Every materialized entity gets durable DrewCraft identity metadata sufficient to map it to:

- `groupId`;
- `encounterId`;
- composition role/type;
- accounting status where needed.

## 12.2 Materialization trigger

Trigger based on player-observable proximity/chunk conditions, not because a strategic scheduler decides to create mobs remotely.

Rules:

- strategic record is locked/transitioned before spawn transaction;
- two players approaching simultaneously cannot spawn the group twice;
- choose safe spawn positions near the group's actual strategic position;
- do not spawn inside protected/invalid blocks;
- if spawn transaction partially fails, recover explicitly rather than marking the entire group materialized blindly.

## 12.3 Active-entity budget / wave model

Total strategic strength and active tactical entities are distinct.

Add bounded controls such as:

```text
strategic.maxActiveEntitiesPerEncounter
strategic.maxMaterializationsPerTick
strategic.waveLowWatermark
strategic.waveSpawnBudget
```

Example semantics:

- strategic group strength = 600;
- active tactical cap = 60;
- 60 entities may exist initially;
- deaths reduce strategic remaining strength;
- additional entities may materialize from unmaterialized strength in controlled waves;
- the encounter ends only when strategic strength reaches zero or an explicit retreat/mission rule applies.

Do not create 600 pathfinding entities just because the record contains 600 strength.

## 12.4 Casualty accounting

Every legitimate tactical loss must be idempotently reflected in strategic strength.

Handle intentionally:

- normal entity death;
- despawn-like removal that should or should not count;
- command/admin removal;
- entity transfer/movement far away;
- captured/persistent entities if supported;
- duplicate callbacks;
- server stop during combat.

Never increase strategic strength because a chunk unloads.

## 12.5 Dematerialization

When no relevant player is near for a grace period:

1. freeze encounter transition;
2. enumerate surviving tagged entities;
3. reconcile health/composition if V1 retains those details;
4. remove/summarize tactical entities safely;
5. compute strategic position from encounter state;
6. clear encounter lock;
7. return group to `STRATEGIC`;
8. persist.

No tactical entity should remain permanently loaded solely to keep a strategic group alive.

## 12.6 Restart recovery

On startup, reconcile records that were saved in transitional states:

- `MATERIALIZING` interrupted before completion;
- `MATERIALIZED` with entities restored by Minecraft;
- `MATERIALIZED` but chunks/entities absent;
- `DEMATERIALIZING` interrupted midway.

Recovery must favor **no duplication and no free strength restoration**.

## 12.7 Stage 12 mandatory edge cases

Automate where feasible and otherwise document deterministic test procedures:

- two players enter materialization radius simultaneously;
- chunk unload during materialization;
- server stop during materialization;
- server stop during active combat;
- restart with a loaded encounter;
- all tactical entities die;
- partial casualties then unload;
- player logs out mid-fight;
- tagged entity is moved far away;
- entity removed outside ordinary damage path;
- repeated load/unload cycles.

Canonical proof example:

```text
strength 100
→ materialize bounded tactical set
→ 37 strategic casualties recorded
→ unload/dematerialize
→ restart
→ inspect strength = 63
→ rematerialize
→ never return to 100
→ never duplicate encounter
```

## Stage 12 exit gate

**PASS only when the materialize → fight → reconcile → unload → restart loop is duplication-safe and casualty-persistent.**

---

# 5. Stage 13 — Hostile-source lifecycle

## Goal

Connect the abstract strategic kernel to persistent hostile places in the generated world.

## 13.1 Source discovery/indexing

Implement/finish a structure-source adapter that turns qualifying generated structures into stable `SourceRecord`s without keeping their chunks loaded.

Use the production/pregenerated world where possible.

Source record follows `docs/STRATEGIC_WORLD_MODEL.md` / `docs/SOURCE_CORE_SPEC.md` and includes:

- stable source UUID;
- dimension and anchor/bounds;
- structure/type identity;
- faction/source class;
- `INTACT | DAMAGED | CLEARED` state;
- source-core location;
- population/reinforcement budget;
- launch cooldown / next action time;
- schema version.

Registration must be idempotent: rescanning/restart cannot duplicate a source.

## 13.2 Source Core

Implement the V1 player-understandable clearing objective.

Requirements:

- physical core representation tied to exactly one source;
- replacing/copying/moving the block does not create source authority;
- legitimate destruction atomically persists `CLEARED` before any later launch can commit;
- clear state survives unload/restart/restore;
- replacing a core cannot reactivate a cleared source.

## 13.3 Production budget / launch policy

Start with simple deterministic V1 rules:

- source has finite/current strategic budget;
- source schedules patrol/raid/etc. according to class/faction;
- launch creates a real `StrategicGroup` at the source position;
- committed groups remain real if the source is later cleared;
- no new group can commit after `CLEARED` is authoritative.

## 13.4 Targeting knowledge

Do not make every source omniscient.

V1 may begin with a simple explainable target-knowledge rule using one or more of:

- local/source-region player discovery;
- recent hostile interaction;
- known settlement/objective registry;
- explicit retaliation after source attack.

Roaming/patrol groups may have non-player objectives.

## 13.5 Stage 13 acceptance

Prove:

1. two qualifying structures register as two stable sources;
2. restart does not duplicate them;
3. one intact source launches a strategic group;
4. group travels according to Stage 11 mechanics;
5. source core is destroyed legitimately;
6. `CLEARED` persists after unload/restart;
7. already-deployed group remains;
8. cleared source cannot launch another group;
9. ordinary Minecraft spawners inside/outside the site remain independent.

## Stage 13 exit gate

**PASS when a real place in the world persistently produces strategic threats and permanent conquest of that exact place stops future production without deleting forces already deployed.**

---

# 6. Stage 14 — Factions, patrols, hordes, raids, and armies

## Goal

Add gameplay breadth on top of the proven kernel without multiplying simulation architectures.

## 14.1 Data-driven definitions

Use data/config definitions for at least:

```text
FactionDefinition
GroupTemplate
SourceProductionRule
TacticalRoleDefinition
```

Support multiple hostile categories, not a zombie-only hard-code.

V1 content target should include at least two meaningfully different compositions where stable, e.g. undead/horde and raider/pillager-derived forces.

## 14.2 Group roles

Implement the strategic roles already defined in `STRATEGIC_WORLD_MODEL.md`:

- patrol;
- roaming horde/warband;
- raid;
- army;
- reinforcement.

Each role uses the same persistence/routing/materialization engine with different objective/state policies.

## 14.3 Army scale semantics

Large strategic size is a number/composition model, not an entity count mandate.

Requirements:

- strategic strength can reach hundreds or more;
- active entities remain bounded by Stage 12 budgets;
- waves preserve total remaining strength;
- casualties persist between waves/unloads;
- no distant army keeps chunks loaded;
- no distant army runs tactical pathfinding.

## 14.4 Merge/split policy

For V1, only implement merge/split if required by the encounter/source design. If added:

- identities and accounting must be transactional;
- total strength before/after must balance exactly;
- restart during transition must be safe.

Otherwise defer richer army logistics to V1.1+.

## Stage 14 acceptance

- spawn/launch multiple group roles;
- run several simultaneous distant groups with no loaded mobs;
- materialize one large army under active-entity cap;
- kill multiple waves;
- unload/restart;
- verify exact remaining strategic strength;
- prove another distant faction/group remains cheap and unaffected.

## Stage 14 exit gate

**PASS when DrewCraft can represent convincing persistent large hostile forces without representing all of them as permanently loaded entities.**

---

# 7. Stage 15 — Siege planner

## Goal

Make defensive architecture matter while preventing indiscriminate block griefing.

## 15.1 Trigger condition

Siege planning exists only for a **loaded encounter** with a valid objective.

Order:

1. use ordinary navigation/pathing first;
2. if a reasonable route exists, use it;
3. only if no viable route exists or route cost exceeds an explicit threshold, consider breaching;
4. only siege-capable roles may execute structural damage.

There is no distant strategic siege pathfinding across unloaded chunks.

## 15.2 Bounded breach planner

Planner should evaluate a local bounded region around objective/attack front.

Candidate scoring may include:

- whether removing the block creates/shortens a navigable corridor;
- block hardness/breach time;
- door/gate preference;
- protected/unbreakable tags;
- vertical accessibility;
- required number of blocks in corridor;
- distance from attacking force;
- explicit decorative/protected exclusions where configured.

Avoid global per-tick flood fills across a base.

## 15.3 Cached siege plan

A computed breach plan becomes encounter state.

Recompute only when:

- corridor succeeds/fails;
- relevant blocks change;
- objective moves;
- plan times out/stalls;
- a materially better normal route opens.

Do not let every attacking mob independently run a breach planner.

## 15.4 Structural damage execution

- only assigned siege roles attack planned blocks;
- rate-limit block damage;
- honor protected tags;
- produce visible/understandable progress;
- once a route opens, return to ordinary navigation.

## 15.5 Stage 15 acceptance scenarios

1. **Open gate:** attackers path through it; no breach.
2. **Door/weak entrance:** prefer it over arbitrary wall if it creates a useful route.
3. **Sealed wall:** planner chooses a deliberate bounded corridor.
4. **Decorative statue off-route:** remains untouched.
5. **Protected blocks:** never selected.
6. **Bridge/chokepoint:** route behavior remains sensible.
7. **Breach succeeds:** normal pathing takes over.
8. **Restart during siege:** no duplicate/undefined strategic strength and encounter can recover.

## Stage 15 exit gate

**PASS when a castle's layout changes combat outcomes, attackers use valid entrances first, and breaching is rare, deliberate, useful, and bounded.**

---

# 8. Stage 16 — Strategic wild animal herds

## Goal

Reuse the strategic kernel for a living large world without creating a second persistence engine.

## 16.1 Herd record

Add a `StrategicHerd` or generalized population record containing:

- herd ID;
- species/type;
- count/composition;
- strategic position;
- home/range region;
- movement state/route;
- last simulation time;
- materialization encounter state;
- schema version.

## 16.2 Ownership safety

Never silently absorb:

- named animals;
- tamed animals;
- leashed animals;
- penned/player-owned animals under an explicit ownership heuristic;
- animals with persistent custom state that would be lost.

Strategic herds are a wild-population system.

## 16.3 Herd movement

Start with simple bounded movement:

- home-range wandering;
- migration between coarse destinations if useful;
- terrain/water constraints;
- no full ecology simulator required for V1.

## 16.4 Materialization

Use Stage 12 transaction machinery and active-entity caps. Player interaction/deaths reduce or alter the herd's persistent count where appropriate.

## Stage 16 exit gate

**PASS when a wild herd moves across unloaded terrain, can be encountered at its real strategic location, survives restart, and never absorbs player-owned animals.**

---

# 9. Stage 17 — Local spawning / Minecraft ecology coexistence

## Goal

Prove that strategic systems are additive and do not replace normal Minecraft gameplay.

## Required proofs

- ordinary nighttime hostile spawning still occurs;
- cave spawning still occurs;
- ordinary mob farms function;
- vanilla/modded spawners function;
- strategic materialized entities can be distinguished/accounted separately;
- strategic caps do not globally suppress ordinary local ecology;
- killing an unrelated local zombie does not reduce a strategic army;
- clearing a strategic source does not disable ordinary hostile spawning;
- herd logic does not capture unrelated player-owned animals.

If mob-cap interactions become problematic, solve them narrowly with strategic materialization budgets/configuration rather than replacing the entire spawn system.

## Stage 17 exit gate

**PASS when a player can simultaneously have ordinary Minecraft spawning/farms and DrewCraft strategic populations with no accounting cross-talk.**

---

# 10. Parallel Track A — Production world / pregeneration / restore

This work may proceed while Stages 11-17 are implemented, but final source registration and terrain acceptance use the chosen representative/production world.

## A1 World-size experiment

Generate smaller representative radii first and measure:

- chunk count;
- generation duration;
- compressed archive size;
- expanded disk footprint;
- backup duration;
- restore duration;
- server save behavior;
- visual/geographic quality.

Inspect mountains, rivers, valleys, climate transitions, caves, coastlines, meaningful empty geography, structure density, and long-distance transportation value.

## A2 Lock production generation inputs

Freeze:

- seed/world identity;
- Terrain Diffusion source/build/model provenance;
- World Scale 2;
- worldgen-affecting dependency versions;
- generation radius/border policy;
- Chunky generation procedure.

## A3 Pregenerate production candidate

- pregenerate Overworld target;
- validate Nether/End behavior;
- index candidate hostile source structures;
- produce world metadata/checksums;
- archive;
- destroy local working copy;
- restore from archive into clean server;
- verify identity and boot.

## Track A exit gate

A production candidate world is reproducible/restorable, geographically appropriate, and large enough to make cars/trains/aircraft/radar/strategic travel meaningful.

---

# 11. Parallel Track B — Production host / ARM / benchmark

## B1 Reproducible host setup

Under `infra/`:

- ARM64 Java 21;
- non-root service account;
- firewall/SSH baseline;
- application release directories separate from persistent world data;
- systemd service;
- logs/health endpoint or equivalent diagnostics.

## B2 Oracle Ampere A1 first benchmark

Deploy restored representative world and current exact pack.

Prove:

- required native libraries load on ARM64;
- Terrain Diffusion pregenerated world loads;
- Create/Atmosphere/MTS/radar/server state boots;
- restart/save is clean.

Record idle and representative workload metrics.

Oracle is a benchmark target, not a sacred requirement. If it fails compatibility/performance, intentionally choose another fixed-cost host. Never hide deficiencies behind surprise autoscaling.

## Track B exit gate

Explicit `PASS` on production target or documented `MIGRATE` decision with replacement host benchmarked.

---

# 12. Parallel Track C — Immutable release artifact contract

## Goal

Make launcher and server updater consume the same release truth.

Finalize versioned `release-manifest.json` containing at minimum:

- DrewCraft pack version;
- protocol version;
- Minecraft/NeoForge/Java requirements;
- minimum launcher version;
- file list, side, size, SHA-256;
- original-provider/release URLs where redistribution policy requires fetch-at-install;
- DrewCraft artifact URLs where redistribution is legal;
- server/client artifact identity;
- compatibility metadata.

Add stable channel pointer such as `live.json` only after release checks pass.

Build deterministic client/server layouts from the one manifest. Never maintain independent launcher/server mod lists.

## Track C exit gate

A synthetic release can be generated, hashed, independently verified, and consumed without developer-local files.

---

# 13. Parallel Track D — Server deployment / updater / backup

## Goal

Make server updates boring, atomic, and recoverable.

## D1 Release layout

Separate:

```text
releases/<version>/   immutable-ish application/mod/config tree
current -> releases/<version>
persistent/world/
persistent/strategic-data/
backups/
logs/
```

Exact implementation may vary, but application release identity must not be conflated with world identity.

## D2 Update transaction

1. fetch target manifest;
2. stage release outside active tree;
3. verify all hashes;
4. validate compatibility/migration preconditions;
5. enter maintenance state;
6. create verified backup;
7. cleanly stop server;
8. switch application release;
9. start;
10. run health check;
11. if application startup fails before irreversible world migration, roll application release back;
12. never blindly replace a migrated world with an old copy.

## D3 Backup contract

Backups include:

- production world;
- DrewCraft strategic persistence;
- player data;
- mod-owned persistent state required for recovery;
- release/manifest identity;
- checksums.

Maintain retention and at least one off-host copy for production.

## D4 Restore drill

Restore into a clean host directory and prove server starts with matching world/strategic/release identity.

## Track D exit gate

A release upgrade, failed application rollout, backup, and clean restore have all been exercised deliberately.

---

# 14. Parallel Track E — One-click Windows/macOS launcher

## Goal

A nontechnical friend should not manage Java, NeoForge, Prism instances, mods, configs, or updates.

Use Prism as launch/auth engine; DrewCraft bootstrapper manages installation/update around it.

## E1 Bootstrap/install

- native Windows installer/bootstrap executable;
- Apple Silicon macOS installer/app/dmg path;
- detect OS/architecture;
- create managed DrewCraft application-data location;
- discover or acquire pinned Java 21 and verify hash;
- discover/manage Prism;
- create/import DrewCraft instance programmatically;
- install exact manifest-resolved pack;
- preserve user-owned screenshots/resource packs/settings where intentionally allowed.

## E2 Launch/update flow

Every launch:

1. read local state;
2. query stable release pointer;
3. compare pack/protocol/launcher versions;
4. stage changed files only;
5. verify hashes;
6. atomically promote verified update;
7. retain prior known-good app version;
8. check server health/version;
9. start Prism/game.

## E3 Failure UX

Clear states for:

- offline/no network;
- server offline;
- server updating;
- stale client;
- incompatible/newer server;
- corrupt local file;
- failed update;
- repair required.

Provide repair and log-export functions.

Never place server SSH/cloud credentials in the client.

## E4 Platform acceptance

On clean machines/accounts:

- Windows installation;
- Apple Silicon installation;
- Java handled automatically;
- Microsoft login through Prism;
- launch;
- join server;
- publish one pack update;
- relaunch and converge automatically;
- corrupt/delete one managed file and repair;
- verify rollback/recovery behavior.

## Track E exit gate

A nontechnical friend can install from one platform-specific download, log in, click Play, update automatically, and repair without opening a mods folder.

---

# 15. Stage 18 — Cross-system gameplay integration

## Goal

Prove the defining DrewCraft systems work together rather than merely passing isolated tests.

Run documented scenarios against the representative/production candidate world.

## Scenario A — Long-distance infrastructure

Use at least two of road vehicle / Create rail / aircraft across meaningful geography. Confirm scale makes infrastructure useful rather than cosmetic.

## Scenario B — Weather aviation + radar

- observe a real Project Atmosphere storm remotely on Create: Radars weather overlay;
- compare with Atmosphere handheld radar;
- fly supported MTS aircraft toward/across/around system;
- verify same atmospheric authority affects aviation;
- verify terrain/site selection changes ground-radar coverage;
- cut/restore radar operation and confirm clean recovery.

## Scenario C — Persistent invasion

- intact source launches force;
- force receives route/ETA;
- players leave area;
- force advances unloaded;
- restart server;
- force remains at correct strategic position;
- players encounter/materialize it near actual position;
- casualties persist after unload/restart.

## Scenario D — Conquest

- players attack source;
- clear Source Core;
- source remains cleared after restart;
- existing deployed group remains;
- no new launch occurs;
- ordinary hostile spawning remains normal.

## Scenario E — Siege

- army reaches defended settlement;
- open route/gate is used first;
- sealed route triggers bounded planned breach;
- decorative off-route structure survives;
- casualties/state survive restart.

## Scenario F — Herd

- wild herd advances unloaded;
- materializes when encountered;
- interaction changes persistent herd state;
- player-owned animals remain excluded.

## Stage 18 exit gate

**PASS when these scenarios work in the same build/world without manual state repair or contradictory ownership between mods.**

---

# 16. Stage 19 — Performance and scale hardening

## Goal

Prove V1 remains playable under a deliberately stressful but plausible multiplayer workload.

## 19.1 Representative worst-normal-case workload

Include simultaneously where practical:

- multiple players;
- Project Atmosphere + Simple Clouds;
- Distant Horizons clients;
- active Create machinery/train;
- MTS road vehicle + aircraft;
- multiple strategic groups moving unloaded;
- multiple wild herds;
- one large materialized army under cap/waves;
- active siege;
- multiple Create radar installations/monitors;
- ordinary local mobs/spawners.

## 19.2 Measure

Server:

- MSPT p50/p95/p99;
- long-tick count;
- CPU saturation;
- heap/native memory;
- GC pause/frequency;
- disk I/O;
- network throughput;
- save duration;
- backup impact;
- loaded entity count;
- strategic scheduler CPU/time/deferred work;
- route computation count/time/cache hit rate;
- materialization counts;
- siege planner invocation/time/cache behavior;
- radar update/sample cost.

Client:

- representative FPS/frame-time behavior on Windows and Apple Silicon;
- Distant Horizons/weather/radar rendering interactions;
- memory use.

Use `spark` and DrewCraft-owned diagnostics.

## 19.3 Optimization order

Before cutting gameplay features:

1. reduce scheduler cadence;
2. increase caching;
3. improve route invalidation discipline;
4. lower/budget active tactical entity counts;
5. spread materialization over ticks;
6. bound siege planner region/frequency;
7. share radar products across displays;
8. tune ordinary server/view/simulation distances as justified;
9. only then reconsider optional features.

Do not solve performance by silently degrading strategic correctness.

## Stage 19 exit gate

Set explicit measured production thresholds from actual host/client benchmarks and pass them with headroom appropriate to the intended friend group.

---

# 17. Stage 20 — Crash, persistence, migration, backup, and recovery hardening

## Goal

Prove the world does not depend on a perfectly clean shutdown.

Test interruption/recovery during:

- strategic route advancement;
- materialization;
- active combat;
- dematerialization;
- source clearing;
- group launch;
- siege;
- herd materialization;
- application update;
- backup creation.

Persistence requirements:

- every custom persistent format has schema version;
- supported migration is explicit/tested;
- unsupported future schema fails visibly;
- feature/subsystem kill switch preserves persistent state instead of deleting it;
- duplicate/replayed transitions are idempotent where required.

Perform full backup/restore drill with exact release identity.

## Stage 20 exit gate

**PASS when intentional crash/restart tests cannot duplicate groups, resurrect cleared sources, restore casualties, corrupt herd ownership, or silently discard strategic state.**

---

# 18. Stage 21 — V1 release-candidate freeze

## Goal

Stop inventing and produce one exact candidate that can actually ship.

At RC freeze:

- freeze dependency versions/hashes;
- freeze worldgen-affecting configuration;
- freeze production world candidate;
- freeze persistence schema except required bug fixes/migrations;
- stop adding major systems;
- only fix acceptance blockers/regressions;
- broad recipe/economy/difficulty tuning remains post-V1.

## RC checklist

- exact manifest artifacts built;
- production world restored onto chosen host;
- server updater tested;
- Windows clean install tested;
- Apple Silicon clean install tested;
- client update/repair tested;
- radar visual acceptance from `RADAR_V1.md` completed;
- aviation weather observed in real multiplayer;
- strategic scenarios completed;
- performance thresholds passed;
- restart/crash/backup/restore passed;
- logs reviewed for unexplained fatal/high-severity registry/mixin/network/serialization errors;
- feature kill switches documented.

Run a multiplayer soak/playtest on the exact RC.

## Stage 21 exit gate

One immutable candidate has no known V1-blocking defect and all hard acceptance evidence refers to that exact build/world identity.

---

# 19. Stage 22 — Hard V1 acceptance and release

The exact RC must demonstrate, end-to-end:

- Minecraft 1.21.1 / pinned NeoForge / Java 21 reproducible pack;
- production World Scale 2 Terrain Diffusion world;
- pregen/archive/restore correctness;
- Distant Horizons on target clients;
- Create machinery/trains;
- useful MTS road vehicles and aircraft;
- Project Atmosphere weather;
- aviation weather effects;
- physical Create: Radars ground installation;
- real weather overlay + native contacts + terrain/site effects;
- Atmosphere handheld weather radar for pilots;
- persistent sources/groups across unloaded terrain;
- route-derived movement and ETA;
- duplication-safe materialization;
- casualty persistence;
- multiple hostile group/faction types;
- convincingly large armies through bounded tactical waves;
- controlled path-first siege behavior;
- permanent source conquest;
- strategic wild herds;
- ordinary Minecraft local spawning/farms/spawners coexistence;
- restart/crash recovery;
- server update/backup/restore;
- Windows one-click install/update/repair;
- Apple Silicon one-click install/update/repair;
- acceptable measured production performance.

If every hard requirement passes on the exact candidate:

1. set release version `1.0.0`;
2. produce immutable client/server artifacts and checksums;
3. publish release notes;
4. promote stable `live.json` / release pointer only after artifact validation;
5. enable/finalize public DrewCraft download buttons only when assets are actually accessible;
6. deploy exact server release;
7. preserve pre-release backup/restore point;
8. tag Git commit/release `1.0.0`.

---

# 20. What is explicitly post-V1

Unless promoted because of a blocker, keep these out of the critical path:

- MTS cockpit traffic/weather radar instrument;
- sophisticated Doppler/radial-velocity radar products;
- elaborate forecast/history radar modes;
- custom DrewCraft radar hardware/models;
- broad recipe/progression/economy/fuel rebalance;
- complex diplomacy/faction politics;
- detailed ecosystem reproduction/predation simulation;
- strategic merge/split logistics beyond what V1 needs;
- fully dynamic road/infrastructure graph rescanning every time blocks change;
- universal tactical-AI overhaul;
- large ship system unless a stable option is already proven;
- aesthetic polish that does not block V1 usability.

---

# 21. Immediate implementation queue

The next commits should follow this order unless a discovered blocker requires a documented deviation:

```text
11.1  Strategic persistence schema + stable IDs
11.2  Strategic scheduler + elapsed-time/catch-up bounds
11.3  Coarse terrain-cost interface/cache
11.4  Cached route engine + ETA
11.5  Admin diagnostics + one unloaded moving-group proof
12.1  Encounter/materialization state machine
12.2  Entity identity + bounded spawn transaction
12.3  Casualty reconciliation
12.4  Dematerialization + restart recovery
12.5  Edge-case/duplication acceptance suite
13    Source registry + Source Core + launch/clear lifecycle
14    Data-driven group types/factions + large-army wave semantics
15    Bounded path-first siege planner
16    Strategic wild herds
17    Local-spawn coexistence
18    Full cross-system scenarios
19    Performance
20    Recovery
21    RC freeze
22    V1 acceptance → 1.0.0
```

In parallel, advance Tracks A-E so they are ready to converge by Stage 21.

The core engineering rule for the rest of V1 is simple:

> **Keep the world abstract while nobody is looking; materialize only what players can interact with; cache expensive decisions; persist every important consequence.**
