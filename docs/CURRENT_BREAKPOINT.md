# DrewCraft Current Development Breakpoint

**Updated:** 2026-09-12  
**Protocol:** `docs/DEVELOPMENT_BREAKPOINTS.md`  
**Last completed breakpoint:** **BP7 — Strategic herds + local-spawn coexistence**  
**Next breakpoint:** **BP8 — Production world + deployment + release/launcher convergence**

## BP7 status — REACHED

BP7 is complete at implementation/compile/unit/runtime-wiring scope. Detailed contract: `docs/HERDS_ECOLOGY_V1.md`.

## Implemented

### Explicit strategic wildlife only

DrewCraft does **not** scan or absorb existing Minecraft animals into strategic herds.

`WildHerdDescriptor` explicitly defines one persistent migration population using:

- dimension;
- species entity ID;
- origin and destination;
- represented count;
- effective movement speed.

Its stable UUID is deterministic from dimension + species + migration endpoints. `WildHerdRegistration` is idempotent and cannot reset an already-moving or casualty-bearing herd if the same descriptor is presented again.

Strategic herd groups use:

- `StrategicGroupType.HERD`;
- faction `drewcraft:wildlife`;
- `MIGRATION_ROUTE` target knowledge;
- no hostile `SourceRecord` or Source Core;
- the existing BP1/BP2/BP3 route, persistence, materialization, casualty, and restart machinery.

This means naturally spawned, bred, named, leashed, tamed/player-owned, penned/farmed, spawner-created, or mod-created ordinary animals are never silently converted into DrewCraft strategic population.

### Lightweight migration

A distant herd remains a single strategic record following its cached coarse route. It does not load chunks, run Minecraft animal AI, or create entities while nobody is near it.

Near players it uses the existing bounded tactical encounter system:

- default active cap remains **64 entities per encounter**;
- remaining represented animals stay abstract;
- confirmed deaths decrement the herd exactly once;
- survivors collapse back into the same herd record;
- save/restart preserves migration target, route, casualties, and encounter authority.

### Local ecology isolation

DrewCraft does not install or replace the normal Minecraft spawn pipeline.

The BP7 architecture guard fails if strategic code begins referencing:

- global `MobSpawnEvent` handling;
- `NaturalSpawner` replacement;
- `SpawnPlacements` rewriting;
- `BaseSpawner` manipulation.

The existing `EntityJoinLevelEvent` hook remains validation-only for entities that already carry DrewCraft strategic tags. Untagged entities return before any cancellation path.

Therefore strategic caps do not quota ordinary night/cave mobs, livestock, mob farms, or vanilla/modded spawners.

### Independent herd kill switch

`features.strategicHerds` independently controls strategic wildlife.

When disabled:

- herd records remain persistent;
- herd coarse movement pauses;
- new herd materialization is disabled;
- currently materialized DrewCraft-tagged herd copies reconcile back into their strategic herd;
- ordinary animals/spawns remain untouched.

### Admin/debug surface

```text
/drewcraft herd create-test <species> <count>
/drewcraft herd list
/drewcraft herd ecology
```

`create-test` seeds an explicit 2,048-block diagnostic migration and respects the herd kill switch. Production V1 herd locations/species/counts will be supplied by BP8 production-world tooling rather than player-position discovery.

## BP7 acceptance evidence

The representative automated herd proof uses an **80-cow** strategic herd:

```text
80 strategic cows
        |
abstract migration begins
        v
player-near encounter
        v
64 active / 16 abstract
        |
10 confirmed deaths
        v
70 strategic survivors / 54 active
        |
next wave = 10 (64-active ceiling)
        |
save + restart
        v
same HERD + migration mission + 70 survivors + 54 active reservations
        |
reconcile/dematerialize
        v
70 strategic survivors, TRAVELING again
```

Additional focused evidence proves:

- deterministic stable herd identity;
- idempotent herd registration does not reroute/reset a living herd;
- `MIGRATION_ROUTE` mission persistence;
- shared BP3 bounded wave/casualty semantics;
- normal spawn-system classes/events are not intercepted by DrewCraft;
- untagged entity joins cannot be cancelled by strategic stale-entity validation;
- herd kill switch gates only HERD strategic movement/materialization and never scans ordinary animals.

### CI

- final BP7 code/test head: **`dfa507d0ac9c330c16897afe19f88467c06784a6`**
- DrewCraft mod CI: **run `34730837899` — SUCCESS**
- job `build-and-test` — **SUCCESS**
- command: `gradle -p mods/drewcraft test build --stacktrace --no-daemon`

The earlier BP7 test run `34730632483` correctly exposed an acceptance-test mistake: after 10 deaths, 54 active survivors leave only 10 slots under the 64-active cap, not 16. The assertion was corrected and the final suite passed.

## Important deferred acceptance

BP8 must choose and seed the actual production-world herd species, counts, and migration corridors.

BP9/BP10 still need representative in-world multiplayer observation of:

- a large herd migrating/materializing in the final Terrain Diffusion world;
- normal night/cave hostile spawning;
- a representative mob farm;
- ordinary vanilla/modded spawners.

Those are final-pack observational acceptance items; the BP7 implementation deliberately does not modify those systems.

Optional richer ownership behavior for an animal that began as a materialized strategic herd member (for example permanently converting it to local livestock when captured/named) is not required for V1 and remains deferred.

## Next: BP8

On the next **"go"**, begin **BP8 — production world + deployment + release/launcher convergence**.

BP8 must converge the production Terrain Diffusion world/pregeneration and real hostile-source/herd seeding, production host decision, immutable client/server release manifest, staged server update/backup/rollback flow, off-host restore proof, and one-click Windows + Apple Silicon macOS install/update/repair paths.

Stop and report again when BP8 passes. Do not begin BP9 scale/failure/recovery hardening until the user says **"go"** after that report.
