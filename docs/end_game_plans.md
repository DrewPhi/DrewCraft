# DrewCraft Endgame Plans

This document captures the current long-term endgame direction for DrewCraft. It is a design target for post-V1 progression/content work, not a hard V1 release requirement unless later promoted into `v_1_requirements.md`.

## 1. Endgame philosophy

DrewCraft should not end with a conventional isolated boss fight.

The endgame should require the player civilization to use the systems that define DrewCraft:

- long-distance exploration;
- roads, bridges, depots and forward bases;
- cars and trucks;
- Create trains and heavy logistics;
- aircraft and airports;
- weather awareness and radar;
- permanent strategic warfare against hostile sources;
- construction of infrastructure across a genuinely large world.

The final challenge should therefore be a continental campaign in which the hard problem is not merely defeating a high-health enemy, but building the civilization and logistics network capable of finding, reaching and conquering the enemy capital.

## 2. The two civilizations

DrewCraft civilization should have a simple founding mythology introduced to players immediately through a starting book.

Its central cultural belief is that humanity is meant to explore, build, travel and ultimately fly. Aviation is treated as one of civilization's highest callings: reaching the sky is a fulfillment of human purpose rather than a violation of nature.

The opposing civilization is a religious cult with the inverse belief. It considers the sky sacred territory that humans are forbidden to enter. Flight, and especially powered human flight, is an act of sacrilege.

The cult is hostile to DrewCraft players from the beginning. No special "first flight" detection or hostility trigger is required. The conflict is between two civilizations whose core beliefs are already incompatible.

This should remain atmospheric rather than becoming a morality lecture. The cult should feel like a coherent civilization with architecture, scripture, rituals, military organization and recognizable doctrine rather than generic evil mobs.

## 3. Lore progression

Lore should be a real gameplay mechanism rather than decorative exposition.

The progression should be:

**starting DrewCraft book -> cult patrol scriptures -> clues to minor settlements -> city archives -> clues to major cities -> combined regional texts -> hidden capital**

### 3.1 Starting book

Every player begins with a short DrewCraft civilization text explaining:

- the civilization's devotion to exploration and engineering;
- the belief that the sky is meant to be reached;
- the historical existence of a hostile opposing faith;
- enough context to make later cult texts meaningful without revealing the whole story.

### 3.2 Patrol texts

Cult patrol mobs can drop or otherwise provide fragments of scripture, pilgrimage instructions, geographical references, local maps, prayers and doctrinal texts.

These should not directly reveal the final capital.

Instead, they point toward nearby cult settlements through references to real landmarks, directions, rivers, mountains, roads, shrines or named regions.

Important progression information should not rely entirely on random drops. Patrol texts may also appear in camps, shrines, chests or other guaranteed/controlled sources so the campaign cannot be blocked by RNG.

### 3.3 Small-city archives

Minor cult cities and towns contain more authoritative texts: temple archives, military records, pilgrimage books, maps or sacred histories.

These texts reveal additional settlements and eventually identify the regional centers that must be cleared.

Clearing these cities remains mechanically meaningful because they are persistent hostile sources in the strategic simulation.

### 3.4 Regional centers

Major cult cities contain the high-value pieces of the endgame puzzle.

Each regional archive supplies part of a larger sacred pilgrimage text or geographical description. Only after enough regional centers are neutralized and their texts recovered can the information be combined into a reliable location for the true capital.

The important structure is therefore:

**mobs lead to cities; cities lead to the capital.**

## 4. The hidden capital and the world border

The enemy capital should initially lie outside the playable world border.

Players can learn about it through scripture and archives before they are physically capable of reaching it.

Once the required regional cult network has been dismantled and the capital's location has been reconstructed, a specific frontier of the world border opens.

The border should not necessarily expand uniformly in all directions. A new pregenerated frontier region can be exposed specifically in the direction of the capital.

The capital should be far enough beyond the old frontier that reaching it feels like a genuine expedition. The target experience is approximately a **10-minute aircraft flight from the nearest mature DrewCraft airfield**, with exact block distance chosen after testing actual aircraft speeds.

Walking or driving there should remain physically possible, but aircraft should clearly be the natural reconnaissance and personnel-transport solution at that scale.

## 5. Final campaign loop

Discovering the capital is not the same as being ready to conquer it.

The final campaign should naturally require:

1. long-range reconnaissance flights;
2. weather and radar planning;
3. selection of a forward operating site;
4. construction of a remote airstrip or airport;
5. fuel and maintenance supply;
6. a defensible forward base;
7. roads for local vehicle movement;
8. heavy logistics by Create rail where the quantities justify extending the network;
9. protection of bridges, depots, airfields and radar installations from strategic enemy forces;
10. a final siege of the capital.

Different transport systems should retain distinct roles:

- **aircraft:** reconnaissance, rapid personnel movement, emergency/light cargo, distant frontier access;
- **cars/trucks:** exploration and local/final-mile logistics;
- **Create trains:** repeated heavy freight, bulk construction material, fuel and strategic supply;
- **boats/ships:** heavy transport where geography makes waterways useful.

Aircraft must not make all other infrastructure irrelevant.

## 6. Cult military identity

The cult's anti-aviation doctrine should affect military content and architecture.

Possible features include:

- anti-air defensive towers;
- large ballistae or other Minecraft-scale anti-air weapons;
- fortified airspace around major cities;
- specialized anti-air cult units;
- protected temples or command sites that cannot simply be trivialized from above;
- strategic priority for DrewCraft airfields, hangars, fuel depots and radar infrastructure.

The faction should still participate in the existing DrewCraft strategic-group system rather than gaining a separate world simulation.

Regional cities and the capital should launch real strategic forces whose movement, casualties, clearing state and siege behavior use the same DrewCraft persistence architecture as other hostile sources.

## 7. Weather and geography in the endgame

The endgame should deliberately use DrewCraft's weather and terrain systems.

The final capital should ideally occupy dramatic terrain where aviation requires planning: for example a mountain basin, high plateau, remote valley or region with difficult approaches.

Cult scripture can refer to these real geographical features. What initially reads as mythology can later be understood as literal navigation information.

Weather should be relevant to reconnaissance and attack timing. Players may need to check ground or aircraft radar before launching long flights or major operations.

The capital should not be placed in a generic flat arena detached from Terrain Diffusion.

## 8. Asset acquisition and reuse strategy

DrewCraft should avoid building every city, mob, model and animation from scratch where high-quality reusable material already exists.

However, "free to download" is not enough. Assets or code may be reused only where their licenses explicitly permit the intended copying, modification and redistribution.

The preferred process is an audited **parts library**.

For every imported or adapted asset, record:

- upstream project;
- author;
- source URL/repository;
- exact version or commit;
- license;
- original path;
- what DrewCraft changed;
- any attribution or redistribution obligations.

Never scrape All-Rights-Reserved or otherwise incompatible assets merely because the server is private or noncommercial.

### 8.1 Remix components, not whole cities

Permissively licensed projects can supply inspiration or reusable pieces such as:

- houses;
- temples;
- walls;
- gatehouses;
- towers;
- courtyards;
- ruins;
- mob models;
- textures;
- animations;
- AI techniques.

DrewCraft should substantially recombine and adapt these into one coherent cult visual language rather than shipping recognizable copies of entire third-party settlements.

A relatively small modular library can generate substantial variety. A target on the order of 20-40 high-quality cult structure modules may be enough for initial town/city assembly before bespoke passes.

### 8.2 Candidate-source policy

Projects with permissive licenses should be prioritized for actual reuse.

Projects with restrictive licenses may still be used as visual or technical references where lawful, but their assets should not be copied into DrewCraft.

The existing DrewCraft candidate list therefore distinguishes between:

- dependencies used unmodified;
- open-source/permissive projects suitable for adaptation;
- reference-only projects;
- prohibited/incompatible asset sources.

A dedicated license-and-assets audit should precede ingestion of any third-party content.

## 9. Terrain-aware city placement

Important cult settlements should not rely solely on ordinary random structure placement.

DrewCraft's bounded, pregenerated production world gives us a better option:

**generate Terrain Diffusion first, then deliberately fit strategic settlements to the resulting terrain.**

The world-build pipeline can evaluate candidate locations using criteria such as:

- usable footprint;
- local elevation variance;
- slope;
- nearby rivers or coastline;
- biome/climate;
- mountain proximity;
- distance from spawn;
- distance from other hostile sources;
- strategic relationship to roads/passes/waterways;
- visual quality.

Different city archetypes can prefer different geography, for example:

- valley town;
- plateau fortress;
- mountain monastery;
- river city;
- coastal stronghold.

Structures should adapt to terrain rather than flatten enormous rectangular pads into Terrain Diffusion landscapes.

Useful techniques include:

- terraced districts;
- foundations and retaining walls;
- stepped roads;
- bridges over ravines;
- walls following ridges;
- limited local cut/fill beneath individual structures.

## 10. The final capital should be hand-authored for the production world

The final capital is unique and should exploit the fixed production seed rather than aiming for universal procedural placement.

Recommended workflow:

1. lock the production world seed and Terrain Diffusion configuration;
2. generate/pregenerate the hidden frontier region;
3. identify an exceptional site at the desired flight distance;
4. use DrewCraft's modular cult pieces as a starting kit;
5. hand-author or heavily adapt the capital around the exact terrain;
6. integrate real surrounding mountains, rivers, approaches and weather into the city's design and lore;
7. validate the final site in the complete server before release.

This is preferable to trying to write a generator capable of producing an equally memorable final capital on every arbitrary seed.

## 11. Mob implementation strategy

The cult does not need dozens of completely bespoke mobs.

Prefer a coherent small roster built from reusable Minecraft-compatible rigs and permissively licensed assets where available.

A possible initial set is:

- ordinary cult soldier/zealot;
- ranged unit;
- priest/scribe;
- heavy guard;
- siege or anti-air specialist;
- one or a small number of genuinely distinctive capital/endgame units.

Shared skeletons, adapted illager-style rigs and reusable animation systems can keep implementation cost reasonable.

DrewCraft remains authoritative for:

- strategic spawning;
- faction identity;
- patrol and army persistence;
- city/source association;
- lore drops;
- materialization and casualty accounting;
- source clearing;
- siege behavior.

Third-party mobs or AI code should not bring an independent strategic spawning/progression system into the pack.

## 12. Production-world audit

The world-build pipeline should emit a machine-readable registry of endgame/cult content, for example `cult_sites.json`.

For each strategic site, record information such as:

- stable source ID;
- settlement type;
- coordinates;
- terrain/site score;
- templates/modules used;
- regional hierarchy;
- lore dependency/progression role;
- initial-frontier vs hidden-frontier status;
- validation state.

The production build should make it possible to inspect and reject bad settlement placements before the survival world is released.

## 13. Victory state

Capturing or neutralizing the final capital should permanently alter strategic world state.

The central cult command/religious authority should stop or dramatically reduce organized large-scale force generation according to an explicit rule.

Ordinary Minecraft mobs and any deliberately surviving minor threats remain, but the players have meaningfully won the continental campaign.

The roads, railways, airports, radar towers, depots and forward bases constructed during the campaign remain useful physical evidence of that victory.

## 14. Post-victory expansion

A natural long-term extension is to use DrewCraft's bounded-world architecture to create successive eras.

After the first continental campaign is completed, a future release can pregenerate and expose another frontier region rather than relying on endless live generation.

The existing civilization then becomes the logistical heartland for the next frontier.

This preserves the long-term DrewCraft loop:

**explore -> gather intelligence -> discover threats -> build routes -> establish infrastructure -> move supplies -> secure territory -> open the next frontier.**
