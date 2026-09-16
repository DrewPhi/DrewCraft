# DrewCraft Hostile Source Core Contract

> **Post-V1 design archive (2026-09-16):** preserved for a later release; not part of the focused V1 shipping profile. See `FURTHER_IDEAS.md`.

This file is the focused implementation contract for clearing hostile strategic sources. It supplements `STRATEGIC_WORLD_MODEL.md`, `SYSTEMS.md`, `v_1_requirements.md`, and `v_1_development_tree.md`.

The core rule is:

> **The physical Source Core block is the player-facing destruction objective; the persistent `SourceRecord` is the authoritative truth.**

A camp, fort, town, city, ruin, stronghold, or other hostile source can only produce new strategic forces while its persistent source state is active.

## 1. Source identity

Every qualifying hostile structure receives exactly one stable strategic source identity.

Conceptually:

```text
SourceRecord
  sourceId
  dimension
  structureId
  structureBounds / region
  sourceClass
  faction
  state: INTACT | DAMAGED | CLEARED
  sourceCorePosition
  sourceCoreType
  populationBudget
  reinforcementRule
  launchCooldown
  nextActionTime
  clearedAt
  clearedBy / clearCause   # optional metadata
  schemaVersion
```

The record survives chunk unload, server restart, application update, backup, and restore.

An ordinary vanilla/modded spawner is never the authoritative strategic source.

## 2. Physical Source Core

Every hostile source has one obvious physical objective bound to its `sourceId`.

The visual block may be faction/source themed, for example:

- camp war banner / command standard
- fort command table or war room core
- undead necromantic altar
- corrupted heart
- fortress beacon
- city/kingdom command core

Different blocks may share the same underlying source-core implementation contract.

The core should be located deterministically and intentionally inside the structure. It must not be an arbitrary decorative block whose accidental destruction silently clears a source.

## 3. Clearing transaction

When the bound active Source Core is destroyed by a legitimate world event, DrewCraft performs one idempotent source-clear transaction.

Supported clear causes should include at minimum:

- player mining/breaking;
- player-caused or gameplay-valid explosion that actually destroys the block;
- other explicitly approved block-destruction events.

The transaction is:

1. resolve the core block/entity to its `sourceId`;
2. verify the source exists and is not already `CLEARED`;
3. atomically set the persistent `SourceRecord.state = CLEARED`;
4. record clear time and optional cause/player metadata;
5. cancel or invalidate all future launch/reinforcement production owned by that source;
6. prevent the source scheduler from creating a new strategic group after the clear commit;
7. remove/disable the physical core representation as appropriate;
8. give players/admins explicit feedback that the source is neutralized;
9. persist the state immediately enough that a crash/restart cannot resurrect the source.

Repeated break callbacks, explosion callbacks, or reloads must be idempotent.

## 4. What clearing means

After `CLEARED`:

- the source cannot launch new patrols;
- the source cannot launch new roaming hordes/warbands;
- the source cannot launch new raids;
- the source cannot launch new armies;
- the source cannot launch new reinforcements;
- its population/reinforcement scheduler is disabled under the V1 rule;
- its cleared state survives unload/restart/backup restore.

V1 has no automatic regeneration, respawn, reoccupation, or recapture of a cleared source.

Those could become later features only through an explicit strategic state transition.

## 5. Already-deployed forces survive

Clearing a source does **not** erase troops that already left it.

If a source already launched:

```text
Patrol #14
Warband #22
Army #31 -> player settlement
```

then destroying the core only stops future production. Those groups remain valid strategic populations at their current geographic positions.

For V1, they continue their existing strategic behavior unless destroyed normally.

Future versions may optionally allow orphaned groups to retreat, merge, defect, seek another allied source, or establish field camps, but no such richer behavior is required for V1.

## 6. Replacing or moving a core never reactivates a source

The block is not the source state.

Therefore:

- placing another Source Core at the same coordinates does not reactivate a cleared `SourceRecord`;
- obtaining a core block/item does not create a source by itself;
- pistons/contraptions must not be able to move a bound core in a way that severs identity or creates duplicates;
- Silk Touch must not provide a functional portable source core;
- a dropped trophy item may exist, but it must not retain source authority;
- duplicating the block item must not duplicate a strategic source.

The safest V1 implementation is for bound source cores to be non-movable and either drop nothing functional or drop a decorative/trophy form only.

## 7. Structure integration

For DrewCraft-owned structures, include the Source Core directly in the template.

For third-party structures, preferred strategies are:

1. supported datapack/template integration that inserts/replaces a known marker;
2. deterministic post-generation placement at a validated relative anchor;
3. source-registration code binds the placed core to the generated structure's stable `sourceId`.

Do not depend on scanning whether some percentage of the original building has been destroyed. Players must be free to loot, renovate, demolish, or repurpose structures without confusing strategic state.

## 8. Defenders and accessibility

The core should be protected by the actual structure layout and defenders, not by hidden completion conditions.

V1 does not require `kill every defender before the core may break` unless testing demonstrates a strong reason. The intended objective should remain understandable:

> reach and destroy the core.

Large source classes may simply place the core deeper inside stronger defenses and start with larger strategic populations.

## 9. Persistence and scheduling safety

Clearing must be race-safe against the source production scheduler.

The implementation must prevent this failure:

```text
T = 1000: source scheduler begins launch
T = 1001: player destroys core
T = 1002: launch commits anyway as a newly created post-clear army
```

Valid implementations may use a per-source lock/version/generation counter or another atomic transaction pattern, but the observable rule is:

- a strategic group committed before clearing is valid and survives;
- a new group may not be committed after the clear state becomes authoritative.

## 10. Required admin/debug surface

At minimum, admins should be able to inspect:

```text
/drewcraft source inspect <sourceId>
```

with:

- source class/faction;
- structure ID/location;
- state;
- bound core position/type;
- active production cooldown/budget while intact;
- clear time/cause if cleared;
- currently existing groups whose `sourceId` points to this source.

This makes invisible strategic bugs diagnosable.

## 11. Required V1 tests

A Source Core implementation is incomplete until all of these pass:

- qualifying generated structure creates exactly one `SourceRecord`;
- exactly one active core is bound to that source;
- mining the core clears the source;
- a supported explosion destroying the core clears the source;
- explosion damage that does not destroy the core does not clear the source;
- duplicate destruction callbacks do not duplicate state transitions/rewards;
- cleared state survives chunk unload;
- cleared state survives server restart;
- cleared state survives full backup/restore;
- replacing the physical core does not reactivate the source;
- moving/duplicating the core cannot duplicate or relocate strategic authority;
- ordinary spawners inside/near the structure remain independent;
- cleared source produces no new strategic groups;
- groups launched before clearing remain in the world and keep their casualties/routes/objectives;
- scheduler/core-destruction race cannot create a post-clear force;
- admin inspection reports the correct source/core state.

## 12. Player-facing result

The intended experience is simple and legible:

```text
HOSTILE FORT
   |
   | Source Core intact
   v
can send patrols / hordes / raids / armies
   |
player attacks fort
   |
DESTROYS SOURCE CORE
   v
SourceRecord = CLEARED permanently
   |
   +-- no future groups from this fort
   +-- existing distant armies still exist
   +-- ordinary local Minecraft mobs/spawners still work
```

This is the V1 source-clearing contract.
