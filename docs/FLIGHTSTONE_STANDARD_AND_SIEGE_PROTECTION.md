# Flightstone Standard, Settlement Targeting, and Siege Protection

## Purpose

The Flightstone Standard is DrewCraft's explicit settlement-defense and strategic-targeting system.

It solves four problems at once:

1. hostile strategic armies need a fair, explainable way to learn where player settlements are;
2. players need a deliberate way to mark which builds deserve controlled anti-grief/siege protection;
3. ordinary and modded hostile mobs must still be dangerous outside defended territory;
4. fortifications must be useful without making protected settlements magically indestructible.

The core bargain is:

> **A raised Flightstone Standard protects nearby structures from arbitrary mob grief by enforcing controlled siege rules, but it also creates a discoverable strategic objective that hostile sources can learn and attack.**

A player may instead leave their Standard unraised. That avoids becoming a Standard-based strategic army target, but provides **no structural protection at all** against normally occurring hostile or siege-capable mobs.

---

## 1. Ownership and first join

Every player receives exactly **one Flightstone Standard** the first time they join the server.

The Standard is associated with that player's UUID and should visually match the DrewCraft civilization rather than the Covenant.

The player may carry or store it indefinitely while exploring. There is no requirement to establish a settlement immediately.

This allows meaningful early exploration before choosing where to build permanently.

The Standard is not ordinary decoration. It is a civic/military object that represents the location a player has chosen to defend.

---

## 2. Placement: true sky visibility

A Standard is active only when placed in the world with **true vertical line of sight to the sky**.

The placement validator should check the vertical column above the Standard to world height.

Intended rule:

- open air is valid;
- a roof is invalid;
- glass above the Standard is still considered a roof and is invalid;
- leaves, terrain, trapdoors, slabs, or other covering blocks invalidate placement when they obstruct true sky visibility;
- the Standard may be placed at any Y level if a true open column exists above it.

This means an open shaft from bedrock to the sky is technically legal. That is acceptable because protection is a true 3D sphere; a deeply buried Standard would protect very little useful surface construction and gains no discovery advantage.

Good placements include:

- castle courtyards;
- exposed tower platforms;
- town squares;
- airfields;
- open compounds;
- visible civic plazas.

The design intent is that the Standard naturally becomes an exposed, defended centerpiece rather than a magic block hidden in a bunker.

---

## 3. Protection geometry

Initial V1 tuning value:

- **protection radius: 300 blocks**.

Protection is a **true 3D sphere** centered on the active Standard.

A block is protected when its Euclidean 3D distance from any active Standard is at most 300 blocks.

This intentionally differs from discovery, which ignores Y.

Consequences:

- a Standard at bedrock does not protect a surface city hundreds of blocks above it;
- a Standard on a tall tower does not automatically protect deep underground construction far below it;
- placement matters spatially;
- there is no useful Y-level exploit.

### Overlapping Standards

If multiple active Standard protection spheres overlap, their protected regions simply form a **union**.

There is no stacking bonus. A block protected by five Standards is governed by the same protection rules as a block protected by one Standard.

The system does not protect players or structures from other players. This is strictly a mob/siege-grief system, so overlapping ownership does not create PvP claims or permissions.

A communal settlement may therefore contain several players' Standards and naturally have a larger or more resilient protected footprint.

---

## 4. Protection applies to every mob

Standard protection is **not Covenant-specific**.

Inside an active Standard sphere, any mob or modded AI attempting to damage terrain or structures must respect DrewCraft's protection/siege rules.

This includes:

- Covenant forces;
- vanilla hostile mobs when they have block-damage behavior;
- modded siege mobs;
- any future hostile faction or creature capable of breaking blocks.

The Standard does **not** grant new block-breaking powers to mobs that do not normally possess them.

For example, an ordinary zombie does not suddenly become a tunneling siege unit merely because it entered protected territory. The rule only constrains block destruction that the attacking mob/system is otherwise capable of performing.

---

## 5. Controlled siege rules inside protection

Protection does **not** make blocks invulnerable.

It replaces arbitrary mob grief with **objective-driven siege destruction**.

Inside a protected sphere:

1. attackers prefer an existing navigable route;
2. open gates, doors, roads, bridges, stairs, breaches, and normal terrain are preferred over destruction;
3. if no reasonable route exists, siege-capable units may break protected blocks;
4. the chosen blocks must plausibly create or improve a route toward the active Standard or another legitimate combat objective;
5. once a usable breach exists, unnecessary destruction stops and attackers use the breach;
6. unrelated decorative structures are not valid demolition targets merely because they are nearby.

A useful conceptual path cost is:

`open route < gate/door < weak barrier < strong wall < heavily reinforced wall`

The planner should choose the lowest-cost useful breach rather than the nearest block.

Thus a castle can delay and shape an attack but cannot become perfectly safe by sealing the Standard behind an impossible wall.

---

## 6. Explosions and artillery

The Standard does **not** create blanket explosion immunity.

The protection system primarily governs AI-driven block breaking and siege decisions.

Configured explosion behavior remains meaningful, including:

- creepers;
- Create Big Cannons shells;
- player explosives;
- enemy artillery where applicable.

A badly aimed defensive cannon may therefore damage friendly fortifications.

Heavy explosive block damage should be tuned separately for DrewCraft balance, but the Standard itself should not create a magical blast-proof region.

---

## 7. Unprotected structures

Any structure outside every active Standard sphere receives **no DrewCraft structural protection**.

This applies to:

- cabins;
- frontier outposts;
- temporary camps;
- mines;
- workshops;
- farms;
- abandoned structures;
- any other construction.

Normally occurring zombies, modded hostile mobs, local siege mobs, patrols, and strategic enemies may all attack players there according to their normal AI.

If such a mob can break blocks, DrewCraft does not stop it merely because the blocks belong to a player.

However, unprotected does **not** mean mobs randomly vandalize empty buildings. They still need an AI/combat/navigation reason to destroy something.

Examples of valid unprotected destruction include:

- breaking through a wall to reach a player;
- forcing entry during pursuit;
- destroying an obstacle along an army route;
- breaching an unprotected defensive position.

The rule is:

> **No Standard means no special structural protection, not peaceful mode and not random demolition mode.**

---

## 8. Strategic targeting versus ordinary danger

Leaving the Standard unraised is a valid choice, but it is not a safety mode.

With no active Standard:

- ordinary nighttime hostile spawning still occurs;
- zombies, skeletons, creepers, and other local mobs still attack normally;
- modded hostile and siege-capable mobs still operate normally;
- patrols/scouts may still be encountered in the world;
- player structures receive no Standard protection;
- Covenant strategic sources do **not** have an active Standard settlement to select as a deliberate large-army objective.

This creates the intended tradeoff:

**No Standard:** less strategic attention, zero special structural protection.  
**Raised Standard:** controlled structural protection, but the settlement can eventually be discovered and targeted by organized armies.

---

## 9. Scout discovery

Initial V1 tuning value:

- **Standard discovery radius: 800 blocks**.

Discovery distance uses only horizontal X/Z Euclidean distance:

`d = sqrt((x_scout - x_standard)^2 + (z_scout - z_standard)^2)`

Y is completely ignored.

This means burying the Standard, placing it on a mountain, or raising it at build height gives no strategic concealment advantage.

A Covenant scout/patrol that comes within 800 horizontal blocks of a valid raised Standard may discover it and begin carrying a contact report.

The source does not learn the target immediately merely because the scout detected it.

The intelligence must propagate physically through the Covenant strategic network.

---

## 10. Physical intelligence transmission

Knowledge is local to specific Covenant sources and groups. It is **not faction-wide telepathy**.

A group carrying intelligence may transfer that intelligence when it comes within **100 blocks** of another valid Covenant strategic group, courier, or source representative capable of receiving the report.

This permits intelligence to propagate physically through the world without requiring the original scout to return to the exact fort that launched it.

Examples:

- Scout A discovers a Standard.
- Scout A passes within 100 blocks of Patrol B.
- Patrol B now also carries the report.
- Patrol B reaches Ashen Gate.
- Ashen Gate permanently learns that player's Standard.

First Stone Abbey does **not** automatically learn the same information.

Its forces must receive the knowledge through later physical contact/courier propagation.

Killing every carrier before the report reaches a source prevents that source from learning the target.

---

## 11. Source-specific permanent knowledge

Once a Covenant source successfully receives a report identifying a player's Standard, that source permanently recognizes **that Standard identity**, not merely one set of coordinates.

From that point forward, while that source remains intact:

- it knows whether that player's Standard is currently raised or unraised;
- whenever the player raises that same Standard again, the source immediately receives its new position;
- moving the Standard does not erase the source's knowledge;
- relocating thousands of blocks away does not reset the relationship;
- removing and replacing the Standard does not fool the source.

This is intentionally stronger than first-contact scouting.

The initial discovery must happen honestly through scouts and physical intelligence transfer. After that discovery, the source has identified that player's Standard and maintains strategic knowledge of it until the knowledgeable source is destroyed.

While the Standard is carried/stored, there is no active protected settlement for that Standard to attack. Previously knowledgeable sources simply know that it is currently unraised.

The instant it is legally raised again, those surviving knowledgeable sources know its new active position.

Therefore relocation is not a way to escape a source that already knows you.

The player must either:

- destroy the knowledgeable source(s); or
- stop using that Standard and accept having no protected settlement.

---

## 12. Army target selection

A Covenant source may only deliberately send a strategic raid/army toward Standards that source currently knows and that are currently raised.

When several valid known Standards are available, the source selects one **randomly with weighting by distance**.

Nearer known Standards should be more likely targets, but distance is not deterministic. A more distant settlement can still be selected.

This prevents repetitive nearest-target behavior while preserving geographic logic.

The exact weighting curve is a balance parameter for the small-world playtest.

Armies do not wander randomly hoping to find a base. Scouts and patrols explore; armies receive deliberate strategic objectives.

---

## 13. Escalation after failed attacks

Attack strength/frequency should grow over time, but escalation should particularly respond to **failed armies**.

Each source-to-Standard relationship should maintain an escalation/threat state.

Initial design intent:

- baseline pressure can increase slowly over time;
- every army/raid that source sends and loses raises the chance or weight of a stronger future response;
- repeatedly defeating the same source should teach that source that the target requires more force;
- exact growth curves, caps, cooldowns, and army sizes are balance parameters rather than fixed design constants.

This should create natural escalation without requiring omniscient measurement of player wealth or base size.

---

## 14. Standard durability and destruction

There is no special timed capture interaction.

The Standard is a physical block/objective that attackers must reach and **break**.

Initial rule:

- Standard block hardness should be approximately that of an **iron block**.

Use Minecraft's normal hardness/break-speed semantics rather than hard-coding an arbitrary capture timer.

Only attackers that are legitimately capable of damaging the Standard under siege rules should be able to break it.

This creates a final defensive moment naturally: attackers must physically control the area around the Standard long enough to destroy a relatively durable block.

---

## 15. What happens when a Standard is destroyed

When an attacking strategic army destroys a player's Standard:

1. that Standard becomes `CAPTURED`;
2. its protection sphere disappears immediately, except where another active Standard sphere still overlaps;
3. the captured Standard is **immediately assigned to the Covenant source responsible for that attacking army**;
4. no physical banner-retreat simulation is required;
5. the owning player receives a recovery compass pointing toward the source now holding the captured Standard.

This intentionally avoids complicated and failure-prone simulation of one particular mob physically carrying a unique quest item across unloaded chunks.

The fiction is that the victorious force has seized the Standard and the strategic system records it as a trophy of its originating source.

---

## 16. Recovery compass

When a Standard is captured, its owner should receive a special compass or equivalent recovery item.

The compass points toward the Covenant source holding the captured Standard.

Its purpose is to turn a lost siege into an immediate counter-campaign:

> **They took your Standard. Now you know which fortress must fall.**

The exact compass presentation can be implemented later, but the target source must be unambiguous and persist through logout/restart.

---

## 17. Recovering a captured Standard

The normal recovery method is:

**find and permanently clear/destroy the Covenant source holding it.**

When that source is neutralized:

- all Standards it holds are returned/released to their respective owners;
- its permanent knowledge of those Standard identities is destroyed along with the source;
- other Covenant sources that independently learned those Standards remain knowledgeable.

There is no requirement to chase the army that originally captured the Standard, because capture transfers possession to the source immediately.

This creates a strong personal reason to locate and conquer the exact fort/city responsible for the attack.

---

## 18. Emergency replacement

A disaster-recovery path must exist so bugs or inaccessible world state can never permanently lock a player out of the Standard system.

Preferred direction:

- replacement occurs through a **Flightstone ritual**, not an ordinary crafting-table recipe;
- it requires something expensive, with a **Nether Star** as the current thematic/cost placeholder;
- additional Flightstone/civilization materials may be required.

The exact recipe is a later balance decision.

A replacement should preserve the player's Standard identity for strategic purposes. A surviving Covenant source that already identified that player's Standard should therefore still recognize the replacement when it is raised.

Emergency replacement is recovery from loss, not a way to erase enemy intelligence.

---

## 19. Moving or removing the Standard

Before any Covenant source has successfully identified the Standard, the player may move it freely.

After a source has identified it, moving it does not clear that source's knowledge.

When the Standard is removed:

- its protection sphere deactivates after only a very short accidental-break/replacement grace period;
- the knowledgeable source knows that the Standard is currently unraised;
- strategic armies should not receive a live settlement target for an unraised Standard.

When the player raises it again anywhere in the world:

- all still-intact Covenant sources that previously identified it immediately receive the new active position;
- they do not need to scout it again.

This means relocation is physically possible but strategically transparent once a source has identified the Standard.

The exact tiny replacement grace period can be tuned during implementation; it should be long enough to handle accidental replacement but too short to exploit during a siege.

---

## 20. Moving contraptions

An active Standard must be anchored to the ordinary world.

It cannot provide protection while part of a moving:

- Create contraption;
- train;
- Create Aeronautics craft;
- Create High Seas ship;
- airship;
- other moving sub-level/vehicle.

If a Standard becomes part of a moving contraption, it should deactivate rather than attempting to move a 300-block protection sphere and strategic target continuously through the world.

This is both cleaner gameplay and dramatically simpler implementation.

---

## 21. Behavior after the Standard falls

Destroying the Standard does not cause the attacking army to vanish or immediately retreat.

Once protection collapses, the attacking mobs continue using their normal combat/siege behavior.

They may:

- pursue and try to kill nearby players;
- enter buildings;
- breach obstacles according to their normal unprotected behavior;
- occupy the immediate battle area while combat continues.

If surviving players flee far enough that the force is no longer meaningfully engaged, the army should eventually disengage and return toward its source rather than chase a player across the entire continent.

The exact disengagement distance/time is a balance parameter for playtesting.

---

## 22. Multi-Standard settlements

Standards remain individually owned even when several players build together.

Because protection spheres union, a shared settlement may remain partially or fully protected after one Standard is destroyed if another active Standard still covers the same area.

This is intentional.

A large communal civilization with several active Standards is inherently more resilient than a one-player outpost, without granting any artificial stacking multiplier.

Enemy strategic targeting still tracks Standards individually. A source may know some players' Standards and not others depending on which intelligence has physically reached it.

---

## 23. Recommended persistent model

### `StandardRecord`

- stable Standard ID;
- owner player UUID;
- state (`UNRAISED`, `RAISED`, `CAPTURED`);
- active block position when raised;
- holding Covenant source ID when captured;
- protection radius = 300;
- sky-valid flag;
- known-by source IDs;
- first-join grant state;
- recovery compass state if needed.

### `TargetKnowledge`

Per Covenant source:

- Standard ID;
- owner UUID;
- learned timestamp;
- original reporting group/source path;
- currently raised/unraised state;
- latest active position when raised;
- attack/failure history;
- escalation/threat state.

### `StrategicGroup`

Relevant objective fields:

- source ID;
- objective type (`PATROL`, `SCOUT`, `REPORT`, `RAID`, `SIEGE`, `RETURN`, etc.);
- carried intelligence Standard IDs;
- target Standard ID when assigned;
- target active position snapshot;
- route/ETA state;
- attack outcome.

---

## 24. Canonical initial tuning values

These are the current starting values, subject to empirical tuning in the 4k development world:

| Parameter | Initial value |
| --- | --- |
| Standard protection radius | **300 blocks, true 3D sphere** |
| Scout discovery distance | **800 blocks, X/Z only** |
| Intelligence handoff distance | **100 blocks** |
| Standard durability | **approximately iron-block hardness** |
| Standards granted | **one per player on first join** |
| Overlapping protection | **union, no stacking bonus** |
| Army target choice | **random among known raised Standards, weighted by distance** |
| Knowledge sharing | **physical propagation only** |
| Known Standard relocation | **surviving knowledgeable sources receive new raised position immediately** |
| Captured Standard location | **immediately assigned to attacking army's source** |
| Capture recovery | **destroy/clear holding source** |
| Emergency replacement | **Flightstone ritual; Nether Star currently proposed** |
| Active on moving contraptions | **no** |
| Explosion immunity | **no blanket immunity** |

---

## 25. Remaining balance variables, not creative-design blockers

The conceptual system is now considered designed.

The following should be tuned empirically rather than decided on paper:

- exact distance-weighting function for target selection;
- patrol/scout frequency;
- army frequency;
- army composition and size;
- escalation curve after failed raids/armies;
- escalation caps/cooldowns;
- disengagement distance/time after a settlement is overrun;
- tiny accidental Standard-replacement grace period;
- exact emergency Flightstone ritual cost;
- heavy explosive/artillery terrain-damage tuning.

These belong in the 4k development-world playtest.

---

## 26. Player-facing summary

The system should ultimately be explainable in a few sentences:

> Every player receives one Flightstone Standard. Raise it beneath open sky to protect a 300-block sphere around it from arbitrary mob grief. Mobs can still breach protected structures when necessary to reach the Standard. Covenant scouts can discover a raised Standard from up to 800 blocks away horizontally, and intelligence only spreads through physical contact. Once a Covenant source learns your Standard, moving it will not fool that source: whenever you raise it again, that source knows where it is until you destroy the source. If an army breaks the Standard, its source captures it and you receive a compass pointing toward the fortress you must destroy to recover it. If you never raise a Standard, strategic armies have no Standard settlement to target—but ordinary hostile mobs and siege mobs still attack normally, and your buildings receive no special protection.
