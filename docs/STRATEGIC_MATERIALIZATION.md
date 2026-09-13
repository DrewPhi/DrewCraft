# DrewCraft Strategic Materialization Contract

**Status:** V1 BP3 implementation contract  
**Minecraft:** 1.21.1  
**Authority:** `DrewCraftSavedData` schema 3

This document defines how a DrewCraft strategic population becomes ordinary loaded Minecraft entities near players and safely returns to abstract strategic state.

## Core invariant

> A strategic unit is never removed from strategic strength merely because it materializes. Materialization reserves an entity identity for an already-existing strategic unit. Only a confirmed, idempotently-recorded tactical death reduces strategic population.

This is what makes unload/reload, crashes, multiple players, and bounded waves safe.

For a strategic group with strength `100` and a tactical cap of `64`:

- the group remains strength `100` while 64 entities are loaded;
- the remaining 36 units are abstract reserve;
- if 37 loaded entities die, strategic strength becomes `63` and 27 entities remain active;
- at most 36 survivors may be backfilled, bringing active entities to at most 63;
- dematerializing does not change strength;
- after save/restart the group is still exactly 63.

## Durable records

### StrategicGroup

The group remains population authority and stores:

- stable group UUID;
- faction/type/source identity;
- strategic position and cached route;
- composition counts;
- total surviving strength;
- strategic state.

While a tactical encounter is active, the group state is `MATERIALIZED`. The coarse strategic scheduler therefore does not move it.

### StrategicEncounter

A non-complete encounter stores:

- stable encounter UUID;
- owning group UUID;
- pre-encounter strategic state to resume after reconciliation;
- lifecycle state: `PREPARING`, `MATERIALIZED`, `RECONCILING`, or `COMPLETE`;
- start and last-nearby-player game times;
- authoritative active entity UUID → entity-type reservations;
- already-accounted casualty UUIDs.

Only one active encounter may exist for a group.

## Materialization transaction

1. A player comes within the configured materialization radius.
2. The group dimension and group-position chunk must already be loaded. DrewCraft never loads a chunk for this step.
3. `beginStrategicEncounter()` atomically checks for an existing encounter.
4. If one exists, it is reused; a second encounter is never created.
5. Otherwise the group is frozen in `MATERIALIZED` state before any entity creation.
6. A durable `PREPARING` encounter is created.
7. The bounded wave planner chooses only strategic units not already represented by active entity reservations.
8. Each entity is created and tagged with group UUID, encounter UUID, and strategic entity type.
9. Its UUID is persisted into encounter authority **before** `addFreshEntity()` can fire `EntityJoinLevelEvent`.
10. Successful entities count against the per-cycle global spawn budget.
11. Once at least one entity exists, the encounter becomes `MATERIALIZED`.
12. If no valid entity can be created, the transaction rolls back to strategic state.

## Bounds

Default V1 limits are deliberately conservative and configurable:

- materialization checks: every 20 ticks;
- materialization radius: 160 blocks;
- dematerialization radius: 224 blocks, with runtime enforcement that it cannot effectively be below the materialization radius;
- dematerialization grace: 200 ticks;
- max active entities per encounter: 64;
- max successful new strategic entities across all encounters in one materialization cycle: 128;
- max encounter records processed per cycle: 32.

Large strategic strength therefore does not imply the same number of loaded mobs.

## Casualties

A `LivingDeathEvent` for a tagged entity is resolved through encounter authority.

The entity UUID must still be in the active reservation map. The first accepted death:

1. removes that UUID from active reservations;
2. stores it in the encounter casualty set;
3. decrements the matching strategic composition count;
4. decrements total strategic strength.

A repeated death callback for the same UUID is a no-op. Strategic counts cannot underflow through duplicate callbacks.

## Waves

`StrategicEncounterPlanner` computes reserve by entity type as:

```text
surviving strategic composition - currently active reservations
```

It then fills only free tactical slots up to the configured active-entity cap.

This allows a strategic army of hundreds to appear as bounded waves while retaining exact strategic casualties.

## Dematerialization

When no player remains inside the larger dematerialization radius for the grace period:

1. loaded encounter entities are discarded without counting as deaths;
2. unloaded encounter entities remain harmless stale disk objects;
3. the group resumes its pre-encounter strategic state with already-recorded casualties preserved;
4. the encounter is completed and removed.

If a stale entity later attempts to load, its durable tags no longer point to an active encounter reservation, so `EntityJoinLevelEvent` is canceled.

## Restart/crash recovery

### PREPARING / RECONCILING survives restart

These states mean a transition was interrupted. On the next materialization cycle DrewCraft discards any loaded partial entities and rolls the transaction back to the strategic group. Any unloaded stale copies are rejected when they later try to join the world.

### MATERIALIZED survives restart

The encounter and active UUID reservations remain authoritative. Loading a tagged entity is accepted only when:

- encounter UUID still exists;
- group UUID matches;
- entity UUID is still reserved by that encounter.

If a reserved UUID never reappears after a crash while a player is actively observing the encounter, the reservation returns to abstract reserve and can be backfilled. A stale copy that appears later is rejected, preserving population without duplication.

## Persistence consistency

Loading SavedData fails closed if:

- an encounter references a missing group;
- multiple active encounters reference the same group;
- an active encounter references a group that is not `MATERIALIZED`;
- active encounter population exceeds surviving strategic strength/composition;
- a `MATERIALIZED` group has no durable encounter.

DrewCraft does not silently repair ambiguous population ownership.

## Canonical BP3 proof

Automated tests prove:

```text
strategic strength 100
→ reserve one encounter
→ materialize 64 entity identities
→ record 37 deaths
→ duplicate death callbacks are ignored
→ strategic strength 63
→ only 36 units remain eligible for backfill
→ dematerialize
→ save / restart
→ strategic strength remains 63
```

A separate two-thread barrier test calls encounter reservation simultaneously and proves exactly one encounter is created.

## V1 boundary

BP3 establishes generic strategic ↔ tactical population correctness. It does not yet define faction templates, hostile source structures, raid objectives, siege behavior, or herd-specific rules. Those are layered on top in BP4–BP7.
