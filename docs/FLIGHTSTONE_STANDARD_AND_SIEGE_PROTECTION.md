# Flightstone Standard, Settlement Targeting, and Siege Protection

## Purpose

The Flightstone Standard is DrewCraft's explicit answer to three problems:

1. hostile armies need a fair, explainable way to discover and target player settlements;
2. players need control over which builds are treated as defended settlements rather than arbitrary strategic targets;
3. mobs need permission to breach fortifications during a real siege without turning ordinary building into indiscriminate griefing.

The core rule is:

> **A raised Flightstone Standard declares a defended settlement. It creates controlled siege protection around that settlement, but it also creates a strategic objective that Covenant scouts can discover and armies can eventually attack.**

Unprotected builds receive no special anti-breach protection.

---

## 1. The Standard

Every player receives one visually distinctive Flightstone Standard on first join.

The Standard should visually match the DrewCraft civilization rather than the Covenant. It should feel important enough that players naturally understand it as a civic/military object rather than ordinary decoration.

A player may carry the Standard indefinitely while exploring. There is no requirement to plant it immediately.

This allows early exploration without forcing the player to choose a permanent settlement before they understand the world.

Multiple nearby Standards may later be merged into one logical `SettlementRecord` so a group of players can share one defended settlement rather than creating overlapping independent wars.

---

## 2. Placement rule: direct sky access

A Flightstone Standard may only be raised where it has direct vertical line of sight to the sky.

The placement validator should scan upward from the Standard to world height.

The intent is to prevent burying the objective underground or hiding it inside an inaccessible bunker.

Recommended rule:

- air is allowed;
- deliberately approved transparent/nonblocking blocks may be allowed if desired;
- solid roofs, terrain, leaves, trapdoors, and similar obstructing blocks invalidate placement;
- Y level does not affect strategic discovery or protection radius.

The Standard may therefore be placed in:

- an open castle courtyard;
- a roof or tower platform;
- a town square;
- an airfield;
- an exposed field;
- another architecturally visible location.

It may not be hidden beneath a mountain, beneath a sealed roof, at bedrock, or at extreme build height to exploit mob navigation.

---

## 3. Protection radius

A raised Standard creates a horizontal siege-protection region centered on the settlement.

Protection distance should be measured in X/Z only. Y is ignored.

Initial tuning target:

- roughly 300–500 blocks radius;
- final value determined through multiplayer testing.

The protection region applies vertically through the full world column within that X/Z footprint.

This prevents exploits based on burying or elevating protected structures while still making one Standard capable of protecting a multi-level settlement, cave infrastructure, towers, and walls.

---

## 4. What protection means

Protection does **not** make blocks invulnerable.

Instead, it activates **controlled siege rules**.

Inside an active Standard's protection radius:

- hostile mobs may attack players and defenders normally;
- mobs should prefer ordinary pathfinding through open terrain, gates, doors, roads, bridges, stairs, and other valid routes;
- mobs must not destroy arbitrary decorative blocks merely because they are nearby;
- only designated siege-capable units may perform meaningful structural breaching;
- breaching is allowed only when needed to open or improve a route toward the Standard or another legitimate military objective;
- once a usable breach exists, mobs should stop unnecessary destruction and advance through it.

The goal is for fortifications to matter without turning every siege into random block deletion.

A useful conceptual breach-cost order is:

`open route < door/gate < weak wall < strong wall < heavily reinforced barrier`

The siege planner should prefer the lowest-cost useful path rather than blindly breaking the nearest block.

---

## 5. Unprotected structures

Player-made structures outside any active Standard protection radius receive **no special anti-breach protection**.

This includes small cabins, frontier outposts, temporary camps, mines, workshops, and other construction.

However, mobs should still require an AI reason to break blocks.

Unprotected mobs may, for example:

- break through a wall to reach a player;
- force entry through a building during pursuit;
- destroy obstacles blocking an army route;
- breach an unprotected defensive position.

They should **not** wander through the world destroying empty buildings for no reason.

The important distinction is:

> **No Standard means no special structural protection, not unconditional random griefing.**

This creates a meaningful frontier-versus-settlement choice. A remote cabin can remain unprotected, but the player accepts that it is physically vulnerable if hostiles have a reason to enter it.

---

## 6. Discovery by Covenant scouts

A raised Standard is not automatically known to the Covenant.

The Covenant should use explainable target knowledge rather than omniscient player tracking.

The intended discovery loop is:

1. Covenant source sends a patrol/scout group;
2. scout follows a coarse strategic route through plausible geography such as roads, valleys, passes, rivers, or neighboring regions;
3. if the scout passes within a configured horizontal discovery radius of an active Standard, it can "see" the settlement;
4. Y difference is ignored for this proximity check;
5. the scout now carries a contact report;
6. the scout, courier, or surviving patrol must return that intelligence to a Covenant source;
7. only after successful reporting does the Covenant source permanently record the settlement as a known target.

Killing the scout before the intelligence is delivered prevents that specific discovery from propagating.

Armies do not randomly wander until they stumble into player builds. Scouts search; armies move toward known strategic objectives.

---

## 7. Persistent enemy knowledge

Once a Covenant source successfully learns a settlement's location, that knowledge is persistent.

Moving the physical Standard later does not cause the Covenant to forget the settlement.

The discovered settlement should receive a stable `SettlementRecord` and strategic anchor.

Before discovery:

- players may freely relocate the Standard;
- moving it moves the protection region.

After discovery:

- the Covenant remembers the original settlement anchor;
- the Standard may be moved locally for reasonable rebuilding or architectural changes;
- moving it thousands of blocks away does not drag an incoming army across the world;
- removing it does not erase Covenant knowledge.

This prevents banner-kiting and repeated relocation exploits.

Knowledge may later propagate between Covenant sources through surviving couriers, patrols, or explicit strategic communication rules.

---

## 8. Settlement lifecycle

Recommended high-level state machine:

`UNRAISED -> RAISED_UNKNOWN -> RAISED_KNOWN -> UNDER_SIEGE -> CAPTURED / OVERRUN`

Possible additional states may be added for implementation, but the player-facing behavior should remain simple.

### UNRAISED

The Standard is carried or stored.

- no settlement protection;
- no Standard-based strategic target exists;
- player may continue exploring indefinitely.

### RAISED_UNKNOWN

The Standard is placed with valid sky access.

- protection radius active;
- Covenant does not yet know the settlement;
- scouts may discover it.

### RAISED_KNOWN

A scout/courier successfully reported the settlement.

- protection radius active;
- settlement is permanently known to one or more Covenant sources;
- raids and armies may be generated according to strategic rules.

### UNDER_SIEGE

A hostile strategic force has arrived to attack the known settlement.

- controlled siege breaching applies;
- attackers seek a path toward the Standard;
- walls, gates, artillery positions, chokepoints, trenches, and fallback positions become meaningful defenses.

### CAPTURED / OVERRUN

The Covenant captures the Standard.

- settlement protection collapses;
- surviving hostiles may pursue players and breach structures much more freely;
- the settlement may be treated as occupied/overrun until the army is defeated or the Standard is recovered.

---

## 9. Standard capture

The Standard should not disappear the instant one hostile mob touches it.

When a valid attacking force reaches the Standard, capture should require a short uninterrupted occupation/capture action.

Suggested initial tuning:

- approximately 10–20 seconds;
- interrupted if the bearer/capturing unit is killed or forced away.

This creates a final defensive moment around the Standard rather than an instantaneous loss condition.

Once captured:

1. the protection radius immediately collapses;
2. the attacking force marks the settlement as overrun;
3. a designated bearer/strategic group takes possession of the Standard;
4. surviving attackers may begin withdrawing toward their originating Covenant source.

The captured Standard should exist as strategic state even when the army is unloaded.

---

## 10. Recovery

The normal recovery loop should be physical and strategic rather than administrative.

Primary recovery paths:

### Defeat the retreating army

If players catch and defeat the army carrying the captured Standard before it reaches home, the Standard is recovered.

### Assault the source holding it

If the army successfully returns the Standard to its origin source, the Covenant stores it there as a trophy/strategic asset.

Clearing or conquering that source returns the Standard.

This creates a strong personal reason to counterattack the specific fort or city responsible for the siege.

### Emergency replacement

There should also be an expensive disaster-recovery route so a bug, inaccessible army, or lost item can never permanently remove a player's ability to participate in settlement warfare.

A possible recipe may require something expensive such as:

- Nether Star;
- Flightstone-related material;
- additional thematic components.

The exact recipe is a later balance decision.

Emergency replacement should be possible but undesirable compared with recovering the original Standard.

---

## 11. Removing a Standard voluntarily

Players should be allowed to temporarily remove/reposition a raised Standard for construction or redesign.

A short grace period should prevent accidental loss of protection while rebuilding.

Suggested initial behavior:

- local repositioning within the settlement is allowed;
- protection remains active briefly while the Standard is being moved;
- if no valid Standard is raised again before the grace period expires, protection ends;
- Covenant knowledge of an already discovered settlement remains.

Removing the Standard is therefore not a method for erasing an incoming war.

---

## 12. Army targeting

Strategic armies target `SettlementRecord`s, not arbitrary player blocks and not the Standard's constantly changing live block position.

The intended strategic loop is:

`Covenant source -> scout/patrol -> discover Standard -> return report -> known settlement -> escalating raid/army -> geographic route -> siege -> Standard capture -> withdrawal/recovery`

Army routing should use the existing DrewCraft strategic geography model:

- source location;
- coarse terrain cost;
- roads;
- passes;
- bridges;
- water constraints;
- destination settlement anchor.

This removes ambiguity around where armies should go while avoiding magical player tracking.

---

## 13. Design principles

The Standard system should preserve these principles:

- **explicit player choice:** players decide which location is their defended settlement;
- **exploration first:** carrying the first Standard indefinitely must remain valid;
- **no omniscience:** Covenant sites learn targets through scouts/couriers;
- **persistent consequences:** once discovered, a settlement remains known;
- **no Y exploits:** discovery and protection use horizontal distance;
- **sky-visible objective:** the Standard cannot be hidden underground or beneath a sealed roof;
- **fortifications matter:** protected blocks can still be breached when necessary to reach the objective;
- **minimum useful destruction:** siege units breach routes rather than randomly demolishing builds;
- **unprotected means vulnerable:** structures outside a Standard radius receive no special anti-grief rules;
- **capture has consequences:** losing the Standard collapses protection and raises the stakes;
- **recovery creates gameplay:** defeat the carrying army or conquer the source that holds the captured Standard;
- **no irreversible softlocks:** an expensive emergency replacement path always exists.

---

## 14. Implementation notes

Likely persistent records:

### `SettlementRecord`

- stable settlement ID;
- owning/allied player IDs;
- strategic anchor X/Z;
- active Standard position if present;
- protection radius;
- current state;
- discovered-by source IDs;
- first discovery time;
- siege/occupation state;
- captured Standard state/location.

### `TargetKnowledge`

Per Covenant source or faction:

- settlement ID;
- known/unknown;
- confidence/quality if later desired;
- report origin;
- reporting group/courier ID;
- time learned;
- propagated-to source IDs.

### `StrategicGroup`

Relevant objective additions:

- objective type (`SCOUT`, `REPORT`, `RAID`, `SIEGE`, `WITHDRAW_WITH_STANDARD`, etc.);
- target settlement ID;
- target strategic anchor;
- captured Standard ID if carrying one.

The first implementation should prefer deterministic, inspectable state over elaborate hidden heuristics. Admin/debug commands should make it possible to inspect why a source knows a settlement, which army is targeting it, and where a captured Standard currently exists.
