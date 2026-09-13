# DrewCraft Current Development Breakpoint

**Updated:** 2026-09-12  
**Protocol:** `docs/DEVELOPMENT_BREAKPOINTS.md`  
**Last completed breakpoint:** **BP3 — Transactional materialization + casualty reconciliation**  
**Next breakpoint:** **BP4 — Hostile sources + permanent clearing**

## BP3 status — REACHED

BP3 is complete at implementation/compile/unit/runtime-wiring scope. DrewCraft now has a durable, bounded strategic ↔ tactical population transaction layered on the BP1/BP2 strategic kernel.

The detailed transaction contract is `docs/STRATEGIC_MATERIALIZATION.md`.

## Implementation

### Durable encounter authority

- `StrategicEncounter` has a stable encounter UUID;
- lifecycle states are `PREPARING`, `MATERIALIZED`, `RECONCILING`, `COMPLETE`;
- each encounter stores:
  - owning strategic-group UUID;
  - pre-encounter strategic state to resume;
  - start and last-nearby-player times;
  - active tactical entity UUID → entity-type reservations;
  - already-accounted casualty UUIDs;
- `DrewCraftSavedData` is now schema **3** and persists active encounters;
- schema 2 worlds migrate with an empty encounter registry;
- future encounter/world schemas fail closed.

### Duplication-safe materialization

`beginStrategicEncounter()` is the atomic ownership boundary:

1. check whether the group already has an active encounter;
2. if yes, return the existing encounter;
3. otherwise freeze the group in `MATERIALIZED` state **before** entity creation;
4. create exactly one durable `PREPARING` encounter.

The method is synchronized and has a real two-thread barrier test proving simultaneous callers receive the same encounter UUID and exactly one reports creation.

### Real entity materialization

`StrategicMaterializationRuntime` is registered on the NeoForge server/event bus and:

- checks player proximity on a coarse configurable cadence;
- materializes only in the group's existing dimension;
- requires the group-position chunk to already be loaded;
- never calls a chunk-loading API merely to materialize;
- samples surface height only after `hasChunkAt` succeeds;
- creates real configured `EntityType` entities;
- writes durable group/encounter/type tags to entity persistent NBT;
- commits the entity UUID into encounter authority **before** `addFreshEntity()` can fire the join event;
- rejects stale tagged entities whose encounter/reservation no longer exists.

### Bounded tactical population

Default bounds:

- materialization cadence: 20 ticks;
- materialization radius: 160 blocks;
- dematerialization radius: 224 blocks;
- dematerialization grace: 200 ticks;
- maximum active entities per encounter: **64**;
- maximum successful new strategic entities across all encounters in one cycle: **128**;
- maximum encounter records processed per cycle: **32**.

The effective dematerialization radius is never allowed below the materialization radius, preserving hysteresis even under a bad config combination.

Large strategic strength therefore remains abstract reserve rather than forcing all represented units to exist as entities.

### Casualty reconciliation

Strategic strength remains authoritative during materialization. Spawning an entity does **not** subtract population.

A tagged `LivingDeathEvent`:

- resolves the durable encounter;
- accepts the death only if that entity UUID is still active;
- moves the UUID to the casualty set;
- decrements matching strategic composition exactly once;
- decrements total strategic strength exactly once;
- ignores duplicate death callbacks.

Example proven by test:

```text
strategic strength = 100
active tactical cap = 64
37 active entities die
strategic strength = 63
active survivors = 27
eligible backfill = 36
```

The wave planner therefore can refill to at most 63 active survivors, never recreate the 37 casualties.

### Dematerialization

After all players leave the larger dematerialization radius for the grace period:

- loaded tactical survivors are discarded without counting as deaths;
- the strategic group resumes its pre-encounter state;
- already-recorded casualties remain authoritative;
- the encounter is completed and removed;
- unloaded stale entity copies are harmless because their later join is canceled.

### Restart/crash behavior

`PREPARING` or `RECONCILING` surviving a restart is treated as an interrupted transaction:

- loaded partial entities are discarded;
- the transaction rolls back to strategic state;
- unloaded stale copies are rejected if they later load.

A fully `MATERIALIZED` encounter survives restart with its active UUID reservations. Repeated attempts to materialize the same group reuse that encounter instead of duplicating it.

If a reserved entity UUID never actually made it to disk during a crash, observing the encounter releases that missing reservation back to abstract reserve and permits bounded backfill. A later stale copy is rejected.

### Persistence invariants

Schema-3 load fails closed if:

- an encounter references a missing group;
- multiple active encounters reference one group;
- an encounter references a group not in `MATERIALIZED` state;
- active tactical count exceeds surviving strategic strength/composition;
- a `MATERIALIZED` group has no durable encounter.

## BP3 acceptance evidence

Focused automated tests cover:

- encounter lifecycle and NBT round trip;
- encounter future-schema rejection;
- schema-2 → schema-3 world migration;
- idempotent casualty accounting;
- bounded per-encounter wave planning;
- global per-cycle spawn-budget exhaustion;
- **canonical `100 → kill 37 → unload → restart → 63` proof**;
- duplicate death callbacks leave the result at 63;
- post-casualty backfill is exactly the surviving reserve;
- materialized restart retains one encounter and active UUID authority;
- interrupted `PREPARING` restart rolls safely back;
- **two simultaneous callers cannot create two encounters**.

### CI

- final code/test head: `974e2d25cdede7a5679340445bfc3d5471e36cd8`
- DrewCraft mod CI: **run `34727614866` — SUCCESS**
- CI job: `build-and-test` — **SUCCESS**
- command: `gradle -p mods/drewcraft test build --stacktrace --no-daemon`
- simultaneous-reservation proof run `34727505486` also passed.

## Important acceptance boundary

BP3 proves the transaction, persistence, runtime event wiring, NeoForge API compatibility, bounded spawn policy, and restart/casualty invariants automatically.

A later representative-world/full-stack acceptance still needs to observe actual hostile mobs materializing/dematerializing in the final pack under multiplayer load. That is deliberately retained for the cross-system/RC acceptance stage rather than forcing an expensive full Terrain Diffusion world boot for every strategic-kernel commit.

## Next: BP4

On the next **"go"**, continue until BP4 is reached.

BP4 makes hostile generated structures real strategic producers:

1. stable persistent `SourceRecord` registry tied to generated geography;
2. idempotent source discovery/indexing;
3. Source Core binding with authoritative clear semantics;
4. deterministic source launch budget/cooldown;
5. sources launch real BP1/BP2 strategic groups;
6. clearing permanently survives unload/restart;
7. clearing prevents all future launches from that source;
8. groups already committed before clearing remain real populations.

Stop and report again when BP4 passes. Do not begin BP5 faction/horde/army breadth until the user says **"go"** after that report.
