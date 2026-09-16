# DrewCraft Strategic World Model

> **Post-V1 design archive (2026-09-16):** preserved for a later release; not part of the focused V1 shipping profile. See `FURTHER_IDEAS.md`.

This document is the canonical behavioral contract for DrewCraft's persistent hostile populations, hostile source structures, roaming forces, materialization, and wild animal herds.

It complements `docs/SYSTEMS.md` and the implementation gates in `docs/v_1_development_tree.md`. If an implementation choice conflicts with this world model, this document describes the intended player-facing behavior while the V1 requirements/development tree remain authoritative for release order.

The central rule is:

> **Important populations are persistent geographic objects, not events spawned because a player happened to be nearby.**

A hostile army, patrol, or wild herd can exist and move while its chunks are unloaded. If a player happens to cross its current position, the player encounters the population that was already there.

---

## 1. Two simulation layers

DrewCraft uses two complementary representations.

### Strategic layer — unloaded or distant

DrewCraft owns compact persistent records describing important groups and sources. These records are cheap enough to update across the entire bounded world without loading chunks or ticking entities.

Examples:

- hostile camps, forts, towns, cities, ruins, strongholds
- patrols
- roaming hordes / warbands
- raiding parties
- armies
- reinforcements
- wild animal herds

### Tactical layer — loaded near players

When a player approaches a strategic population, DrewCraft materializes it as ordinary Minecraft/modded entities. Loaded entities may use a compatible tactical AI backbone for group behavior, pursuit, stacking, panic/herd response, etc., but the strategic record remains the authority for identity, source, composition, casualties, and unloaded movement.

Loaded tactical AI must never silently create or destroy strategic strength outside DrewCraft's accounting rules.

---

## 2. Hostile sources are real places

A hostile strategic source is attached to a real generated structure or deliberately authored DrewCraft structure in the world.

Source classes may include:

- `CAMP`
- `FORT`
- `TOWN`
- `CITY`
- `RUIN`
- `STRONGHOLD`
- other data-driven source types if later useful

The structure is not merely decoration. While its source remains active, it can generate strategic forces according to its faction/type and current population budget/cooldowns.

Sources should normally come from the pre-generated production world. After pregeneration, DrewCraft can index the qualifying structure starts/anchors and create a persistent source registry without keeping their chunks loaded.

A structure mod may supply the architecture, but **DrewCraft owns strategic source state**.

---

## 3. Stable source identity

Each source has a stable persistent identifier independent of chunk load and independent of any ordinary mob spawner.

Conceptual record:

```text
SourceRecord
  sourceId
  dimension
  structureId
  structureBoundingRegion
  anchorPosition
  sourceClass
  faction
  state: INTACT | DAMAGED | CLEARED
  sourceCorePosition
  populationBudget
  reinforcementRule
  launchCooldown
  nextActionTime
  influenceRegion
  discovery/knowledge state if used
  metadata
  schemaVersion
```

The source state is the authority. A vanilla/modded spawner inside the structure is not the source itself.

---

## 4. Source core / clearing objective

### V1 clearing rule

Every hostile strategic source should expose one explicit, understandable objective: a **DrewCraft Source Core** (final themed presentation may differ by source type).

Examples of presentation:

- command table
- war banner/controller
- corrupted heart
- fortress beacon
- city command core

Under the hood these are the same strategic concept and are bound to a `sourceId`.

### Core destruction

Destroying the active Source Core by a legitimate in-world block-destruction event — including deliberate explosives if they actually destroy the core — performs an authoritative source-clear transaction:

1. validate the core is bound to an active `sourceId`;
2. atomically mark that `SourceRecord` `CLEARED` in persistent state;
3. record clear time and optional clearer/cause metadata;
4. cancel future source-production actions;
5. remove/disable the physical core representation;
6. emit player/admin feedback that the source has been neutralized;
7. persist before the source is allowed to schedule another force.

The source remains cleared through chunk unload, server restart, backup/restore, and ordinary block replacement.

Putting another Source Core block at the same coordinates must **not** reactivate a cleared source. Reactivation/recapture, if ever added, requires an explicit strategic state transition and is post-V1 unless promoted deliberately.

### Core placement

The core must be associated with a deterministic, inspectable location inside each qualifying structure. Preferred implementation order:

1. embed/place the DrewCraft core through supported structure/datapack integration where safe;
2. otherwise place it at a deterministic valid anchor during source registration/post-generation;
3. never choose an arbitrary existing decorative block whose destruction could accidentally clear the source.

The exact source-core block appearance may vary without changing strategic semantics.

### Defenders

Defenders should make reaching the core difficult through normal gameplay. V1 does not require an invisible 'kill every defender first' condition unless testing shows it is necessary. The player should always be able to understand whether the source is still active by inspecting the core/state feedback.

---

## 5. What happens to already-deployed forces when a source is destroyed

Destroying a source stops **new** patrols, reinforcements, hordes, raids, and armies from being launched by that source.

Already-deployed groups do **not** vanish. They are persistent populations already out in the world.

Depending on group/faction policy they may:

- continue their current mission;
- wander after losing their home source;
- retreat toward another allied source;
- merge with another force;
- eventually be destroyed.

For V1, the simplest valid rule is: **existing groups continue their current strategic behavior; the cleared source produces no new groups.**

This avoids magical despawning and makes destroying a source strategically meaningful without erasing an army that has already marched halfway across the world.

---

## 6. Hostile force types and behavior

Not every hostile group should omnisciently target a player.

Data-driven group roles should support at least:

### Patrol

- remains near a home/source region or route network;
- wanders/patrols without a player target;
- may react if it discovers players/activity.

### Roaming horde / warband

- has a broad wandering route or destination;
- can exist far from its source;
- may be encountered by chance while exploring.

### Raid

- has a known player settlement, road, facility, or other objective;
- follows a deliberate route toward that objective.

### Army

- larger persistent composition;
- deliberate destination/objective;
- may materialize in waves for performance while preserving total strategic strength;
- supports siege-capable roles.

### Reinforcement

- travels from a source toward an allied group/source/objective;
- is still a real strategic group and can be intercepted en route.

Optional richer states such as scouting, temporary field camping, retreat, merge/split, or diplomacy are allowed later but must build on the same kernel.

---

## 7. Target knowledge: no magical omniscience

A force should not automatically know the exact coordinates of every player simply because the player logged in.

Potential sources of strategic target knowledge include:

- proximity to source territory;
- a patrol/scout encountering the player or settlement;
- attack on a hostile source;
- known player infrastructure such as major roads/rail/industrial areas if deliberately modeled;
- repeated player activity in an influence region;
- faction-specific objectives;
- explicit retaliation rules.

The first V1 targeting implementation should be deterministic and explainable. Rich information propagation can come later.

A roaming group that has no player objective should continue roaming even if a distant player exists elsewhere in the world.

---

## 8. Unloaded movement is real movement

Strategic groups exist at a geographic position while unloaded.

Each group stores enough information to update along a coarse route without loading Minecraft chunks:

```text
StrategicGroup
  groupId
  faction
  groupType
  sourceId
  dimension
  strategicPosition
  route / routeCursor
  destination / objective
  movementSpeed
  composition
  strength
  state
  lastSimulatedTime
  encounterId
```

For elapsed time `dt`, the group advances along its route by its effective strategic movement budget.

Routing may use chunk-scale or coarser terrain cells and should eventually account for meaningful geography such as:

- distance
- slope/mountains
- water
- crossings/bridges
- roads
- traversability
- faction constraints

No distant entities are kept loaded merely to make movement happen.

No army teleports directly from its source to a player because an event timer fired.

---

## 9. Emergent exploration encounters

A major design goal is that a player can stumble into world events that were not spawned for them.

Examples:

- cresting a ridge and seeing an army marching through a valley;
- discovering a patrol on a road;
- encountering a roaming horde several kilometers from its source;
- finding a hostile source fort before it has ever targeted the player's settlement;
- intercepting reinforcements on the way to another army;
- encountering a wild herd at a watering/grazing area.

When a player approaches a group's **current strategic position**, it materializes there. The group's existence predates the encounter.

This is one of DrewCraft's defining differences from ordinary timed-horde mods.

---

## 10. Materialization contract

Materialization is a transaction, not a spawn event.

1. lock the strategic group as materializing;
2. create/retain a unique encounter ID;
3. determine safe nearby spawn positions consistent with the strategic position/route;
4. instantiate the represented composition up to active-entity limits;
5. tag every entity with group/encounter identity;
6. only then mark the strategic group materialized.

If the strategic force represents more entities than should be loaded at once, encounter waves may represent the remaining strategic strength without losing total accounting.

Two players loading adjacent chunks must never create two copies of the same army/herd.

---

## 11. Tactical hostile AI while loaded

DrewCraft may reuse an existing 1.21.1 NeoForge horde-AI mod for **local tactical behavior** if compatibility tests pass.

Desirable reusable behaviors include:

- horde grouping/wandering;
- collective pursuit;
- stacking/climbing behavior;
- configurable mob participation via tags;
- sensible ranged-team behavior;
- local group awareness.

However:

- the upstream mod's own timed/random horde spawning must be disabled when it conflicts with DrewCraft strategic sources;
- loaded AI cannot become the persistent world authority;
- global indiscriminate block breaking is not acceptable;
- siege damage remains under DrewCraft's path-first breach planner.

Strategic entities may receive tactical-AI tags when materialized while ordinary locally spawned mobs may optionally receive a conservative subset of the same local behaviors.

---

## 12. Siege behavior remains DrewCraft-owned

Even if a tactical horde mod can break blocks, DrewCraft's strategic armies must obey the project siege rule:

1. normal pathfind first;
2. prefer open roads, bridges, gates, doors, entrances and navigable terrain;
3. if no reasonable path exists, invoke a bounded siege planner;
4. choose a low-cost meaningful breach corridor;
5. assign only siege-capable units;
6. damage only blocks participating in that active corridor or explicit interaction categories;
7. once opened, resume normal navigation.

Decorative/off-route builds must not be attacked merely because they are nearby.

---

## 13. Wild animal herds are persistent populations

Important wilderness animals should feel like populations rather than unrelated singleton spawns.

Conceptual herd record:

```text
HerdRecord
  herdId
  species / variant composition
  approximateCount
  dimension
  strategicPosition
  homeRange
  movementState
  preferredTerrain / biome constraints
  currentDestination or roaming tendency
  lastSimulatedTime
  materializationEncounterId
  metadata
```

V1 should prioritize believable group existence and persistence over a complete ecology simulator.

---

## 14. Herd spawning and materialization

Strategic wild populations should materialize **as herds**.

Example behavior:

```text
Strategic herd: 14 horses
        ↓ player approaches
Materialized encounter: coherent group of horses
        ↓ player leaves / area unloads
Strategic herd: surviving count and new position
```

This is preferable to repeatedly spawning isolated animals at random around players.

Ordinary Minecraft passive spawning may remain available for compatibility and farms, but strategic herds are the primary mechanism for memorable persistent wild populations. Passive spawn tuning is balance work and should not destroy vanilla husbandry/farm mechanics.

Domesticated, named, leashed, bred, penned, or otherwise clearly player-owned animals should remain normal persistent entities and must not be silently absorbed into a roaming wild herd.

---

## 15. Loaded herd behavior

When a strategic herd is materialized, animals should behave cohesively rather than scatter independently.

Desired local behaviors include:

- same-species group awareness;
- reasonable spacing rather than entity clumping;
- separated animals attempt to rejoin;
- shared panic/flee response when one member is attacked;
- group movement/wandering;
- avoidance of obvious cliffs/hazards;
- grazing/water/rest behavior if a compatible lightweight AI provides it;
- recognition of player-built pens so domesticated livestock does not constantly migrate away.

A compatible existing herd-AI mod may provide these loaded behaviors. DrewCraft still owns the unloaded strategic herd record and materialization accounting.

Detailed genetics, sickness, thirst micromanagement, reproduction ecology, predator-prey simulation, and animal economy are not V1 requirements.

---

## 16. Wild herd movement while unloaded

Distant herds use the same coarse simulation philosophy as hostile groups but with peaceful movement policies.

Possible movement drivers:

- home range
- biome/terrain suitability
- nearby water/grazing regions
- seasonal movement if cheap to derive
- avoidance of hostile/unsafe regions if later modeled
- bounded random roaming

The herd should not travel enormous distances for no reason. Movement should remain geographically plausible and species-configurable.

---

## 17. Casualties and player interaction

Strategic state must reflect what happened while materialized.

For hostile forces:

- dead entities reduce composition/strength;
- capture/removal is reconciled deliberately;
- unload cannot restore original strength.

For herds:

- hunted/killed animals reduce herd count;
- animals intentionally domesticated/claimed by players leave the wild herd's strategic count;
- surviving wild members remain in the herd;
- normal unload/reload cannot duplicate animals.

---

## 18. Structure-source integration

DrewCraft should use a **whitelist** of qualifying structure IDs rather than treating every modded structure as a strategic source.

A mapping file should eventually look conceptually like:

```yaml
sources:
  minecraft:pillager_outpost:
    class: CAMP
    faction: illager

  some_pack:illager_camp:
    class: CAMP
    faction: illager

  some_pack:illager_fort:
    class: FORT
    faction: illager

  some_pack:hostile_palace:
    class: CITY
    faction: hostile_faction_a
```

The structure's visual theme and ordinary loot/mobs may come from its source mod. DrewCraft adds only the strategic meaning, source core, persistent state, and outgoing groups.

Friendly villages/settlements do not automatically become hostile sources simply because they come from the same structure pack.

---

## 19. Source density and world scale

The world is intentionally huge and should not become a theme park.

Therefore:

- hostile sources must be sparse;
- larger source classes should generally be rarer than camps;
- structure spacing/density is part of the production world-build configuration;
- qualifying structures should be inspected against Terrain Diffusion World Scale 2 before lock;
- the production pregeneration process should output a source-density report by type and region;
- if a structure pack adds too much unrelated content, whitelist/disable structures or reject the pack rather than accepting clutter.

Source density should create meaningful travel time between threat centers so destroying a nearby source changes future attack ETAs.

---

## 20. Required V1 source tests

A source implementation is not complete until all of these pass:

- structure generates and receives exactly one stable source ID;
- source core is inspectable and linked to that source;
- source can launch a strategic group from its real location;
- group moves while source/group chunks remain unloaded;
- player can accidentally encounter the group en route;
- group materializes once;
- casualties persist through unload/restart;
- source core can be destroyed by intended gameplay including supported explosives;
- core destruction atomically marks source cleared;
- cleared state survives unload/restart/backup restore;
- replacing the block does not reactivate the source;
- cleared source launches no new groups;
- already-deployed group does not magically disappear;
- ordinary local spawning/spawners continue independently.

---

## 21. Required V1 herd tests

- create/index a persistent wild herd;
- herd advances coarsely while unloaded;
- player encounter materializes a coherent group rather than duplicate singletons;
- loaded members exhibit group/panic behavior;
- killing some members reduces persistent count;
- claiming/domesticating an animal removes it correctly from wild strategic accounting;
- herd dematerializes safely;
- restart preserves herd count/position;
- nearby farm animals are not accidentally absorbed;
- entity counts and AI remain within the V1 performance budget.

---

## 22. Non-goals / anti-patterns

Do not implement the strategic world as:

- periodic hordes spawned around online players;
- armies teleported from a source when an attack timer fires;
- thousands of permanently loaded distant entities;
- source state inferred from a vanilla spawner;
- sources that silently respawn after restart;
- cleared source cores that can be replaced to reactivate production;
- every hostile mob globally homing toward the nearest player;
- every passive animal becoming a permanently simulated strategic record;
- separate unrelated strategic simulators for armies and herds;
- global mob block breaking that bypasses the siege planner.

The intended result is a world in which geography, exploration, conquest, infrastructure, and chance encounters all matter because important populations actually have persistent locations and histories.
