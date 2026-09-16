# DrewCraft Endgame Plans

> **Post-V1 design archive (2026-09-16):** the custom endgame is intentionally deferred until the focused survival/exploration release is stable. See `FURTHER_IDEAS.md`.

This document is the canonical current design for the DrewCraft long-term campaign/endgame. It is primarily post-V1 content/progression work unless pieces are promoted into the V1 requirements.

The guiding principle is simple:

> **The endgame should require players to build the civilization capable of finding, reaching, supplying, and conquering the enemy capital.**

It should use DrewCraft's defining systems—large geography, aircraft, cars, Create rail, weather, radar, hostile strategic sources, forward bases, and persistent world state—rather than collapsing into a conventional boss room.

---

## 1. The two civilizations

DrewCraft begins with two opposing civilizations/religious worldviews.

### DrewCraft civilization

Every player begins with a short founding book explaining that DrewCraft civilization regards exploration, engineering, and especially aviation as a sacred calling. Humanity is meant to push beyond the horizon and ultimately take to the sky.

This should be concise and atmospheric rather than a long lore dump.

### The cult

The enemy cult holds the inverse belief: humanity belongs to the earth and entering the sky is sacrilege.

The cult is hostile to DrewCraft players from the beginning. There is **no special first-flight hostility trigger** and no need to detect whether a player has crafted or flown an aircraft.

The faction should feel like a coherent civilization rather than generic evil mobs:

- common soldiers and patrols;
- priests/scribes and elites;
- temples, forts, walls, archives and pilgrimage sites;
- scripture and military records;
- Source Cores tied to DrewCraft's existing strategic-source system;
- a consistent visual palette;
- organized defense of its settlements;
- a final holy capital.

---

## 2. Campaign shape

The intended campaign hierarchy is:

**cult mobs/patrols -> coordinate/lore fragments -> 8 major outposts/temples -> Source Core destruction + guaranteed major clues -> hidden capital location -> frontier opens -> approximately 10-minute flight -> forward logistics campaign -> final capital siege**

The eight sites do not all need identical footprints. They can range from fortified temples and monasteries to military outposts or small walled settlements, but they should all belong visibly to the same civilization.

The final capital should be dramatically larger and more monumental—an Anor-Londo-like holy city rather than simply a ninth outpost.

---

## 3. Mob foundation: Illager Invasion

Use **Illager Invasion** as the primary cult mob foundation rather than writing a bespoke combat roster from scratch.

Reasons:

- it already provides multiple distinct illager combat roles;
- its mobs fit a hierarchical religious/military faction naturally;
- DrewCraft can reuse their existing combat behavior rather than inventing new AI;
- the cult can initially use the existing models/behaviors and receive a custom visual reskin later;
- the final reskin can make the mobs match the chosen cult structures and palette.

Useful conceptual roles include:

- common foot soldiers;
- ranged soldiers;
- armored/heavy crusader-like units;
- priest/scribe/support units;
- spellcaster/prelate-like elites;
- inquisitor/high-priest-style elite defenders.

DrewCraft remains authoritative for:

- strategic group spawning;
- faction/source identity;
- army composition;
- unloaded movement;
- materialization/dematerialization;
- casualty accounting;
- lore drops;
- city association;
- Source Core lifecycle;
- siege behavior.

Illager Invasion supplies the local mob behavior/content layer, not a second strategic simulation.

### 3.1 Visual reskin later

Do not block the first playable campaign on custom mob art.

First make the system work with the Illager Invasion roster. Later apply a coherent faction reskin so mobs match the cult architecture. The likely visual direction is religious/crusader-like rather than ordinary pillagers: robes, covered faces, dark metal, restrained heraldry and a shared cult symbol.

The exact palette should be chosen only after the structure palette is finalized so buildings and mobs look like one civilization.

---

## 4. Lore and clue drops

Lore is not just exposition; it is the discovery system for the eight cult sites and eventually the capital.

### 4.1 Random patrol/mob drops

Cult mobs can randomly drop named scripture, dispatches, pilgrimage notes, military orders, maps, or other paper/book items.

Each useful clue is associated with a **named cult site**. A clue can contain different amounts of location information, for example:

- only the X coordinate;
- only the Z coordinate;
- X plus Z but no Y;
- two of the three coordinates;
- a partial/rounded coordinate;
- a directional/geographic hint;
- rarely, the complete coordinates;
- a full coordinate paired with the outpost name.

The important mechanic is that fragments include the **name of the destination**, allowing players to match separate clues together.

Example:

- `Pilgrimage to the Ashen Basilica — X: -8421`
- `Orders for the Ashen Basilica — Z: 3910`
- another rare document may reveal the complete location.

After collecting several documents, players can combine the matching fragments and locate that outpost.

### 4.2 Avoid progression deadlocks

The system should feel random without allowing bad RNG to make progression impossible.

Therefore:

- useful fragments can be random drops from roaming cult mobs;
- camps/chests/archives may contain additional clue rolls;
- every major site should guarantee the critical clue needed for the next stage when its Source Core is cleared;
- rare full-coordinate drops can accelerate discovery but should not be required.

Players who fight and explore normally should eventually accumulate enough overlapping intelligence to identify all eight sites.

### 4.3 Lore text

The clue items should also contain actual cult religious writing so they work simultaneously as navigation objects and worldbuilding.

The coordinate information can be embedded in:

- pilgrimage routes;
- military dispatch headers;
- archive catalog numbers;
- temple location records;
- maps;
- scribal annotations;
- references to real mountains, rivers or regions.

The cult texts should gradually reveal its anti-aviation theology without requiring players to read every book to understand the mechanics.

---

## 5. Source Cores and city clearing

Each of the eight important cult sites uses DrewCraft's existing **Source Core** concept.

A site is not cleared because every decorative block is destroyed or every mob is hunted down. The authoritative transition is the destruction/capture of its Source Core.

Clearing a Source Core should:

1. mark the site permanently cleared in DrewCraft SavedData;
2. stop or sharply reduce future strategic force generation from that source;
3. preserve already-deployed enemy forces according to the normal strategic rules;
4. guarantee the site's major lore/intelligence unlock;
5. update global endgame progression;
6. update the spawn monument/Flightstone.

This reuses the strategic-source architecture rather than creating a separate quest system.

---

## 6. The Flightstone / spawn progression monument

Working name: **Flightstone**. The name can change later.

Spawn should contain an unbreakable DrewCraft monument/monolith representing the aviation-oriented founding religion/civilization.

It serves two purposes:

1. a diegetic progression interface;
2. a permanent archive so critical progress cannot be lost because someone misplaced a book.

### 6.1 Initial state

At the beginning it contains the DrewCraft founding text and eight dormant markers/sigils representing the eight major cult sites.

### 6.2 On Source Core destruction

When one of the eight sites is cleared:

- its marker activates;
- the monument permanently records the site's completion;
- the major intelligence recovered there is archived;
- a short new inscription/message may appear.

These messages are framed as communication/interpretation from the DrewCraft aviation spirit or religious tradition.

Keep this **sparse**. It should not chatter after every minor event or become a quest-board parody.

The physical books remain useful and collectible, but the Flightstone is the durable record of campaign progress.

### 6.3 Final resolution

After all required major sites are cleared, the collected city intelligence resolves into the location of the true capital beyond the current world border.

At that point the Flightstone triggers or announces the opening of the relevant frontier.

---

## 7. One architectural asset kit

Do **not** assemble the cult civilization from a dozen unrelated structure mods if one coherent building kit can supply the visual language.

The currently selected direction is the **xSisyX Fantasy City & Terrain Builder asset/schematic pack** as the primary cult architecture kit.

The attraction is not its original block palette. What matters is the geometry, silhouette and modular building vocabulary:

- fantasy/medieval houses;
- religious/cathedral-style buildings;
- church/temple forms;
- roads and paths;
- terrain/environment pieces;
- enough repeated architectural language to create both settlements and a capital.

Because this is a private friends-only server/project, the immediate operational focus is on getting the assets into the world and preserving basic source attribution/provenance rather than building a public redistribution pipeline.

### 7.1 One coherent cult palette

All imported structures should be normalized into one DrewCraft cult palette so buildings from the kit look like one civilization.

The important rule for asset selection is therefore:

> **Prioritize good geometry and silhouette; block palette is cheap to change.**

Possible replacements might map woods, stones, roofs, metals and colored decorative blocks into a consistent cult vocabulary.

### 7.2 Offline structure editing

Palette conversion should be scripted directly against structure/schematic/NBT files. Minecraft does not need to be opened for bulk conversion.

Build a small DrewCraft structure-processing tool that can:

- inspect the structure palette;
- replace block IDs while preserving compatible state properties;
- remap stairs/slabs/walls/fences/doors safely;
- remove or replace unwanted mod-specific blocks;
- normalize chests/loot tables;
- replace spawners;
- add DrewCraft Source Core markers/hooks;
- add lore/archive containers;
- rotate/mirror templates where appropriate;
- record source/provenance metadata;
- emit final DrewCraft-ready structure files.

Minecraft is still useful later for visual QA and artistic touch-up, but not required for the bulk transformation process.

---

## 8. Eight cult sites

Use the selected asset kit to create **eight distinct but related** major outposts/temples.

They do not need eight completely unique architecture sets. Variety should come from composition, terrain and function.

Possible archetypes include:

- small fortified monastery;
- shrine/outpost compound;
- mountain temple;
- walled military-religious fort;
- archive complex;
- river/bridge stronghold;
- plateau citadel;
- large regional basilica/temple settlement.

Each contains:

- a unique stable site name;
- a Source Core;
- local cult defenders;
- lore/intelligence relevant to progression;
- optional AA coverage depending on importance;
- terrain-aware placement.

The eight site names should be stable because mob-dropped clue fragments use those names to associate partial coordinates.

---

## 9. Terrain-aware placement

The cult structures have to look intentional on Terrain Diffusion rather than like structures pasted onto arbitrary slopes.

DrewCraft's bounded/pregenerated world gives us an important advantage:

> **Generate the Terrain Diffusion world first, then fit important cult sites to the actual terrain.**

The world-build pipeline can score candidate locations using:

- available footprint;
- slope/elevation variance;
- nearby rivers/coasts;
- mountain proximity;
- biome/climate;
- distance from spawn;
- distance between cult sites;
- defensibility;
- road/pass access;
- visual quality.

Different archetypes can prefer different terrain rather than forcing every structure onto flat land.

Useful fitting techniques include:

- stepped foundations;
- retaining walls;
- terraced districts;
- roads following contours;
- ridge-following walls;
- bridges over ravines;
- limited local cut/fill beneath individual modules.

Avoid bulldozing enormous flat pads into Terrain Diffusion landscapes.

---

## 10. Air defenses: deliberately cheap V1 implementation

Do **not** build a full turret/ballistics/missile simulation for the endgame.

The gameplay requirement is simply:

> **Flying directly over an intact cult stronghold should be dangerous, but not impossible or unfair, and destroying its defensive sites should make the airspace safer.**

### 10.1 Flak-zone controller

Designate selected tower/defense structures as AA sites with a simple hidden DrewCraft controller.

When a supported aircraft is inside the AA radius:

1. periodically roll a low probability of a flak event;
2. use the aircraft's current position and velocity from `VehicleService`;
3. estimate a short lead position;
4. add a substantial random spatial error;
5. spawn a visible/audible explosion/flak burst near that point;
6. apply modest damage only if the aircraft/player is sufficiently close to the burst;
7. do **not** damage terrain/blocks.

This creates the experience of anti-aircraft fire without implementing guns, shells, targeting AI or projectile simulation.

### 10.2 Altitude and balance

Flak should not be overpowered.

The probability/accuracy of a damaging burst should generally **decrease as altitude increases**. Higher flight therefore trades safety against navigation/weather/mission considerations rather than being equally dangerous at every altitude.

Other cheap tunable factors can include:

- distance from the AA site;
- aircraft speed;
- number of surviving AA sites covering the aircraft;
- maneuvering/change in velocity;
- weather/visibility;
- site tier.

These are balance knobs, not requirements for the first implementation.

### 10.3 Destroying defenses

AA coverage is tied to a physical defensive tower/controller.

Destroying that tower/controller disables its flak zone. Destroying the site's Source Core can optionally disable remaining local AA as part of the cleared-state transition.

Approximate intended density:

- minor site: zero or one AA site;
- important regional site: one to several overlapping zones;
- final capital: enough distributed AA sites that simply flying straight to the central palace is risky, while careful high-altitude reconnaissance remains possible.

The purpose is to encourage reconnaissance and ground operations, not to shoot players out of the sky arbitrarily.

---

## 11. Discovering the hidden capital

The eight major cult sites ultimately contain the reliable pieces needed to locate the final holy capital.

Patrol/mob drops lead players to those sites. **The sites themselves lead to the capital.**

Each cleared site contributes a major fragment—scripture, map section, pilgrimage record, military record or geographical description. Once all required fragments have been acquired, the Flightstone can interpret/archive them into a final location.

The capital initially lies **outside the playable world border**.

This lets players learn that it exists before they can physically reach it.

---

## 12. Frontier opening

Once the eight-site progression resolves the capital location, open a specific new frontier rather than necessarily expanding the border uniformly.

The hidden region should already be pregenerated offline.

The target experience is that the capital is roughly a **10-minute real-time aircraft flight from the nearest mature DrewCraft airfield**, with exact block distance determined from the actual aircraft chosen for the server.

This should feel like leaving known civilization and entering a distant enemy homeland.

---

## 13. The final capital

The capital should feel Anor-Londo-like in **scale and monumentality**, not as a literal copy.

Desired composition:

- dramatic Terrain Diffusion setting;
- visible skyline from far away while approaching by aircraft;
- lower settlement/districts;
- large walls and gates;
- layered elevation;
- religious buildings using the same vocabulary seen in the eight outposts;
- major stairways/processional routes;
- upper sacred district;
- enormous central temple/cathedral/palace;
- distributed AA defenses;
- final Source Core / central authority.

The visual payoff comes from recognition: players have seen this civilization's architecture in small fragments for the entire campaign, and now they encounter it at city scale.

### 13.1 Hand-author for the production terrain

Do not require a universal procedural capital generator.

Once the production seed is selected:

1. pregenerate the hidden frontier;
2. identify an exceptional site at the desired flight distance;
3. compose the capital from the shared asset kit around the actual landscape;
4. use algorithms to help with footprints, overlap, roads, walls and candidate layouts;
5. visually inspect several candidate master plans;
6. refine the best one manually/algorithmically;
7. validate it from both ground level and long-range aircraft approach.

The capital should be designed **from the airplane inward**: distant silhouette first, district hierarchy second, street-level detail third.

---

## 14. Final logistics campaign

Finding the capital is not equivalent to being ready to conquer it.

The intended final loop is:

1. reconnaissance flight into the new frontier;
2. observe terrain, weather, city defenses and AA coverage;
3. return or establish a safe landing area;
4. build a forward airstrip/airport;
5. establish fuel, food, repair and material storage;
6. build radar/weather infrastructure;
7. establish a defensible forward base;
8. use trucks/cars for local and final-mile transport;
9. extend heavy Create rail logistics if the required material flow justifies it;
10. suppress/destroy AA positions and outer defenses;
11. assault the capital;
12. destroy/capture the final Source Core/central authority.

Transport roles should remain distinct:

- **aircraft:** reconnaissance, personnel, rapid/light supply and frontier access;
- **cars/trucks:** local/final-mile logistics;
- **Create trains:** repeated heavy freight and strategic supply;
- **boats/ships:** heavy transport when waterways make sense.

Aircraft should make distance manageable without making infrastructure irrelevant.

---

## 15. Flightstone progression and final messages

The Flightstone is the durable player-facing campaign record.

It should change visually as the eight Source Cores are cleared. Exact writing can be authored later.

Use only sparse milestone messages so the effect remains special rather than corny.

Possible cadence:

- founding inscription at server start;
- first major city cleared;
- halfway point;
- all eight cleared / capital resolved;
- frontier opens;
- final capital victory.

Most storytelling remains in cult books and the physical world rather than repeated supernatural dialogue.

---

## 16. Victory state

Neutralizing the final capital permanently changes the strategic world.

The cult's central command/religious authority should stop or dramatically reduce organized large-scale force generation according to an explicit rule.

Ordinary Minecraft hostility and deliberately surviving threats remain, but the players have meaningfully completed the continental campaign.

The infrastructure they built—roads, railways, airports, forward bases, radar towers, depots and bridges—remains as the physical history of that victory.

---

## 17. Post-victory expansion

DrewCraft's bounded-world architecture makes later campaign eras possible.

A future release can pregenerate and expose another frontier instead of relying on endless live generation. The civilization created in the first campaign becomes the logistical heartland for the next one.

The durable long-term loop is:

**explore -> gather clue fragments -> locate hostile sites -> clear Source Cores -> expand infrastructure -> reconstruct the enemy geography -> open frontier -> establish logistics -> conquer -> push the frontier farther outward.**

---

## 18. Implementation priority / scope discipline

For the first playable endgame, prefer simple systems that create the desired experience over bespoke technology.

High-value, low-complexity choices already made:

- Illager Invasion mobs instead of a new mob AI roster;
- reskin later rather than blocking gameplay on custom art;
- one coherent schematic/asset kit instead of many unrelated structure packs;
- offline palette conversion instead of manually rebuilding every structure;
- existing DrewCraft Source Cores as the authoritative city-clear mechanic;
- named random coordinate fragments rather than a large quest framework;
- Flightstone as a simple persistent campaign/progress interface;
- probabilistic flak bursts instead of a full AA weapons simulator;
- fixed pregenerated terrain + deliberate site placement instead of demanding universal procedural city generation;
- one hand-composed final capital rather than a complex arbitrary-seed capital generator.

The endgame succeeds if it creates a compelling reason to explore, fly, drive, build infrastructure, gather intelligence and undertake a long-distance campaign. Complexity that does not materially improve that experience should be avoided.
