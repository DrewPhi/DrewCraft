# DrewCraft V1 Strategic Sources — BP4 Contract

> **Post-V1 design archive (2026-09-16):** this completed design is not part of the focused V1 shipping profile. See `FURTHER_IDEAS.md`.

**Status:** BP4 implementation contract.  
**Superseded by:** nothing; this document narrows `SOURCE_CORE_SPEC.md` into the implemented V1 architecture.

## 1. Purpose

Hostile camps, forts, ruins, cities, and strongholds are persistent strategic producers. They are not represented by permanently loaded mobs and they are not controlled by ordinary Minecraft spawners.

The persistent `SourceRecord` is authoritative. A physical `drewcraft:source_core` is only the player-facing objective bound to that record.

## 2. Stable source identity

A qualifying generated structure is described by a `SourceDescriptor` containing:

- dimension;
- structure ID;
- deterministic generated anchor X/Y/Z;
- source class;
- faction ID;
- bound Source Core position.

The stable source UUID is deterministically derived from:

```text
drewcraft-source-v1 | dimension | structureId | anchorX | anchorY | anchorZ
```

The Source Core block position is deliberately **not** part of source authority. Replacing, copying, or manually placing a physical Source Core cannot manufacture a new strategic source or reactivate a cleared one.

Rediscovering the same generated source is idempotent. If the same stable source UUID is rediscovered with conflicting immutable metadata, DrewCraft fails closed instead of silently mutating strategic identity.

## 3. Persistence

World persistence schema **4** stores `SourceRecord`s alongside strategic groups and encounters.

Each record persists:

- stable source UUID;
- generated structure identity and anchor;
- Source Core position;
- source class and faction;
- `INTACT | DAMAGED | CLEARED` state;
- remaining production budget;
- launch strength and cooldown;
- next action time;
- launch serial;
- generation counter used for transaction safety;
- clear time/cause/actor metadata.

Schema-3 worlds migrate with an empty source registry. Future source/world schemas fail closed.

## 4. Generated-world integration seam

Production structure integration must call:

```text
DrewCraftSavedData.discoverSource(SourceDescriptor, gameTime)
```

from a deterministic structure/template/post-generation integration point. That call is safe to repeat and does not reactivate a cleared source.

DrewCraft does **not** perform a recurring global structure/chunk scan. The final production-world/pregeneration track owns the concrete list of DrewCraft/third-party structure templates and their deterministic Source Core anchors. Those integrations populate this already-complete registry seam while the relevant structure is generated/indexed.

For development, `/drewcraft source create-test` proves the same lifecycle by registering a deterministic test source and placing its bound Source Core.

## 5. Physical Source Core

`drewcraft:source_core` is a real registered block.

V1 safety properties:

- no BlockItem is registered, so it is not a portable strategic-authority item;
- piston reaction is `BLOCK`, so ordinary piston motion cannot move it;
- successful player destruction calls the source-clear transaction;
- actual explosion destruction calls the same transaction;
- an unbound/copied Source Core block is strategically inert;
- the persistent `SourceRecord` remains authoritative after the physical block is gone.

A placeholder vanilla texture is used at this development stage; visual theming can vary by source/faction without changing authority semantics.

## 6. Permanent clearing

Clearing is synchronized and idempotent:

1. resolve physical core position to a persistent source UUID;
2. if already `CLEARED`, do nothing;
3. set state to `CLEARED`;
4. increment the source generation counter;
5. record clear time/cause/actor;
6. disable future production permanently for V1;
7. mark world state dirty;
8. immediately flush `DimensionDataStorage` because this is a rare irreversible progression event.

The admin clear command uses the same persistence rule.

Rediscovering the structure after clearing returns the same `CLEARED` record. V1 has no automatic regeneration/reoccupation transition.

## 7. Production scheduler

`SourceProductionScheduler` works only over already-persisted source records. It never scans distant chunks and never keeps source chunks loaded.

Default bounds:

- source cycle: every **200 ticks**;
- source records inspected per cycle: **16**;
- successful group launches per cycle: **4**;
- failed-route retry delay: **1200 ticks**.

The inspection window rotates through the sorted registry so a large source registry cannot permanently starve later UUIDs.

A source launches only when:

- it is not `CLEARED`;
- it has enough remaining production budget;
- its cooldown has elapsed.

Route planning uses the BP2 bounded coarse routing service. A failed route consumes no population and only moves the source's next retry time.

## 8. Clear-versus-launch race

A route may be expensive relative to a tiny state mutation, so route planning does not hold the source lock.

Instead:

1. scheduler captures `source.generation`;
2. bounded route is planned;
3. launch attempts an atomic `commitSourceLaunch(sourceId, expectedGeneration, group, gameTime)`;
4. commit succeeds only if the generation is unchanged and source is still eligible.

Clearing increments the generation. Therefore:

- a group committed before the clear transaction remains a real strategic population;
- a plan that started before clearing but tries to commit after clearing is rejected;
- a source can never create a new strategic group after `CLEARED` becomes authoritative.

This rule is tested directly by clearing the source from inside the planner between generation capture and commit.

## 9. Already-deployed groups survive

Source clearing never deletes strategic groups whose `sourceId` points to the source. Their:

- UUID;
- route/cursor;
- composition and casualties;
- materialization state;
- objective

remain independent persistent state.

A save/reload acceptance test proves that a pre-clear group remains present while its parent source remains permanently `CLEARED` and refuses a subsequent launch.

## 10. BP4 baseline versus BP5 content

BP4 intentionally proves **source lifecycle and production semantics**, not final faction breadth.

The minimal BP4 launch planner currently creates routed zombie `PATROL` groups with class-dependent bounded budgets/cooldowns/ranges. This is an integration proof, not final balance.

**BP5 owns:**

- data-driven factions;
- varied entity compositions;
- patrol/horde/raid/army/reinforcement launch profiles;
- richer target/objective selection;
- multiple hostile families;
- army-size semantics.

BP5 must reuse the BP4 source transaction rather than bypass it.

## 11. Admin/debug surface

```text
/drewcraft source create-test
/drewcraft source list
/drewcraft source inspect <sourceId>
/drewcraft source clear <sourceId>
/drewcraft source perf
```

Inspection reports persistent identity, state, budget, cooldown, generation, launch count, clear metadata, core position, and the number of existing strategic groups from that source.

`source perf` reports bounded scheduler work, launches, route failures, rejected race commits, rotation cursor, and CPU time.

## 12. BP4 acceptance boundary

Automated BP4 acceptance proves:

- deterministic/idempotent source identity;
- persistence and schema migration;
- duplicate/conflicting source bindings fail closed;
- permanent clearing across save/reload;
- source clear is idempotent;
- scheduler bounds and fair rotation;
- global launch cap;
- route failure does not consume population;
- source-clear/launch race cannot commit after clear;
- a pre-clear launched group survives clear and restart;
- cleared source cannot launch after restart;
- Source Core block and production scheduler compile against the pinned NeoForge/Minecraft runtime.

The production-world track must still bind the selected real generated structures/templates to `SourceDescriptor`s and visually verify their core placement in the final pregenerated world. This is deliberately an offline/world-integration task, not a reason to introduce recurring live chunk scans.
