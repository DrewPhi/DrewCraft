# DrewCraft Mob AI and Strategic-Source Candidate Research

Research snapshot: **2026-09-12**

This document records current candidate mods that may reduce the amount of custom code required for DrewCraft's loaded mob behavior and may provide pregenerated structures that DrewCraft can promote into persistent strategic sources.

Nothing in this file is automatically part of the production pack. Candidates must pass the normal dependency, licensing, compatibility, Terrain Diffusion, multiplayer, performance, and anti-redundancy gates before promotion.

Canonical world behavior is defined in `docs/STRATEGIC_WORLD_MODEL.md`.

---

# 1. Core conclusion

No existing mod found provides DrewCraft's complete required world model:

- real hostile camps/forts/towns/cities as persistent strategic sources;
- persistent forces moving across unloaded geography;
- route/ETA based on world distance;
- chance encounters with forces already moving through the world;
- casualty-preserving materialization/dematerialization;
- source-core destruction permanently preventing new groups;
- persistent wild herds using the same unloaded strategic kernel;
- path-first siege planning with constrained breach corridors.

Therefore DrewCraft still needs its own **strategic world kernel**.

However, existing mods may provide substantial portions of the **loaded tactical AI** and **structure content**, which we should reuse when they fit cleanly.

---

# 2. Hostile tactical-AI candidates

## A. Enhanced Hordes + Enhanced Hordes Tweaks

### Current compatibility candidate

- Enhanced Hordes: 1.21.1 NeoForge line available; current 1.21.1 file is beta.
- Enhanced Hordes Tweaks: `1.2.2` for 1.21.1 NeoForge, release, updated 2026-08-26.
- Both are MIT-licensed according to current project listings.

### Useful behavior

Enhanced Hordes provides cooperative hostile behavior such as:

- horde stacking/climbing;
- configurable horde mob tags;
- configurable breakable/unbreakable block tags;
- intelligent ranged-team behavior;
- leaping behavior and other local combat improvements.

Enhanced Hordes Tweaks adds configurable behaviors particularly relevant to DrewCraft:

- **Horde Wandering** — idle horde mobs gather and walk together;
- **Collective Understanding** — nearby horde mobs join pursuit;
- **Horde Determination** — pursuit can persist across greater distances;
- **Horde Mentality** — group-based block-breaking behavior;
- heightened detection and many toggles/day gates.

### DrewCraft verdict

**High-priority compatibility spike for loaded hostile behavior.**

Use only as a tactical layer. DrewCraft must disable/avoid any behavior that conflicts with strategic source spawning or siege rules.

Most importantly, generic Horde Mentality block destruction cannot be the authority for strategic sieges. DrewCraft siege-capable entities must obey the path-first breach planner.

## B. Zombie Hordes

### Current compatibility candidate

- `horde_hoard-neoforge-1.1.0.jar`
- Minecraft 1.21.1 NeoForge
- release
- updated 2026-07-06
- MIT license

### Useful behavior

Current project features include:

- horde members physically stacking over one another;
- breaking weak environmental blocks;
- local reinforcement behavior;
- other cooperative zombie behavior.

### DrewCraft verdict

**High-priority alternative tactical spike.**

Test this as an alternative to the Enhanced Hordes + Tweaks combination, not automatically alongside it. Both occupy similar behavior territory and may share lineage/IDs/assumptions.

The primary question is whether its local horde behavior can be retained while disabling any spawning/reinforcement mechanics that duplicate DrewCraft's strategic population accounting.

## C. Improved Mobs

### Useful behavior

- powerful hostile AI upgrades;
- pathfinding that can account for breakable blocks;
- climbing/ladder/equipment behaviors.

### DrewCraft verdict

**Reference implementation, not preferred baseline.**

Its global difficulty/block-breaking model is broader than DrewCraft needs and conflicts conceptually with the deliberate path-first siege corridor. Study useful techniques if needed, but do not adopt it merely because it is mature.

## D. Invasion Mod 1.21.1 NeoForge fork

### Useful behavior

The maintained 1.21.1 NeoForge branch contains invasion-oriented specialist mobs, including engineer-style building/obstruction behavior such as bridges/ladders and units designed to overcome defenses.

### DrewCraft verdict

**Siege R&D reference, not baseline gameplay.**

Its Nexus/wave-invasion loop duplicates DrewCraft's strategic system, but its engineer/specialist movement and obstruction-handling code may inform Stage 15 siege implementation.

---

# 3. Friendly/wild herd-AI candidates

DrewCraft owns strategic wild-herd persistence regardless of the local AI chosen below.

## A. Ethological!

### Current compatibility candidate

- Minecraft 1.21.1
- NeoForge
- current `0.1.2` release (2026-08-29)
- All Rights Reserved
- very new/small adoption, therefore experimental

### Particularly relevant behavior

Current features describe cows, sheep, pigs, and chickens that:

- form dynamic living herds;
- graze and seek water;
- sleep as groups;
- react to weather and threats;
- maintain herd spacing;
- recognize separation and attempt to rejoin;
- recognize player-made pens and stop migration behavior there;
- avoid problematic cliff/swimming behavior.

### DrewCraft verdict

**Most functionally interesting herd-AI spike.**

It maps unusually well to the desired materialized-herd experience. Because it is very new and ARR, it must be treated as a compatibility candidate rather than a foundational dependency. We should test performance, API/tag control, interaction with strategic materialization, and whether domesticated/penned animals can be cleanly excluded from strategic handling.

## B. Herd Instinct

### Current compatibility candidate

- Minecraft 1.21.1
- NeoForge
- `v2` release, 2026-07-16
- MIT license
- very small jar / narrow scope

### Useful behavior

- when one passive animal panics, nearby herd members panic and flee together;
- configurable behavior;
- optional player-proximity panic.

The author has described roaming/group exploration as planned rather than already complete.

### DrewCraft verdict

**Low-risk fallback / complementary local behavior candidate.**

This is much narrower than Ethological!, but that can be an advantage. If DrewCraft implements local group-following itself or via another framework, Herd Instinct may cheaply provide believable shared panic without importing a full husbandry/ecology overhaul.

## C. Animal Husbandry

### Current compatibility candidate

- Minecraft 1.21.1
- NeoForge/Fabric
- current 0.4.x line
- active 2026 development

### Behavior

Adds domestication, happiness, sickness, hunger/dehydration, genetics, breeding traits, grooming, feeding/watering systems, etc.

### DrewCraft verdict

**Do not add for V1.**

It solves a different problem and would introduce substantial husbandry micromanagement that is outside DrewCraft's current pillars. Revisit only if the group later wants deep ranching gameplay.

## D. Other herd behavior projects

Projects such as Mean Mobs, Wild Behavior, and other livestock overhauls demonstrate useful ideas, but are not currently preferred over the two focused spikes above. Some are either broader realism overhauls, newer/less proven, or add behavior beyond the V1 requirement.

---

# 4. Strategic-source structure candidates

The preferred structure architecture is **not** "install every structure pack." DrewCraft should select the minimum structure content that provides convincing source classes and then control its density aggressively.

Qualifying structures are mapped by structure ID into DrewCraft source classes. A structure can exist without being a strategic source.

## A. When Dungeons Arise — strongest hostile-source content candidate

### Current 1.21.1 candidate

- `DungeonsArise-1.21.1-2.1.68-release.jar`
- Minecraft 1.21.1
- NeoForge
- release
- CurseForge project 442508
- current 1.21.1 release uploaded 2025-10-26
- All Rights Reserved

### Why it is unusually useful for DrewCraft

Unlike generic "more structures" packs, When Dungeons Arise already contains structure concepts that directly map onto strategic source tiers. Its structure configuration exposes independent enable/spacing/separation controls for structures including examples such as:

- Illager Campsite
- Illager Fort
- Bandit Towers
- Plague Asylum
- Shiraz Palace
- other large hostile/fortified structures

That gives DrewCraft a natural mapping such as:

```text
Illager Campsite -> CAMP
Bandit Tower     -> FORT / OUTPOST
Illager Fort     -> FORT
Plague Asylum    -> major hostile RUIN / FORT
Shiraz Palace    -> CITY / major kingdom source
```

Its structures can be made extremely rare rather than accepting default density.

The audited 2.1.68 registry namespace is `dungeons_arise`. DrewCraft's required
built-in datapack replaces `dungeons_arise:major_structures` with exactly five
structures and disables `dungeons_arise:minor_structures`:

```text
dungeons_arise:illager_campsite -> CAMP / raiders
dungeons_arise:illager_fort     -> FORT / raiders
dungeons_arise:bandit_towers    -> FORT / raiders
dungeons_arise:plague_asylum    -> RUIN / undead
dungeons_arise:shiraz_palace    -> CITY / undead
```

The major-set spacing is initially 128 chunks with 96-chunk separation. This is
a deliberately sparse test value for Terrain Diffusion World Scale 2 and must be
validated by representative pregeneration counts before production promotion.

WDA 2.1.68's embedded NeoForge metadata declares Minecraft
`[1.21,1.21.1)`, even though its provider artifact is published for 1.21.1.
The isolated source-structure profile therefore uses FML's scoped dependency
override for `dungeons_arise -> minecraft`; it is not promotable until the exact
artifact completes a real 1.21.1 client/server boot and generation test.

### DrewCraft verdict

**Top hostile-source structure spike.**

Do not enable every structure automatically. Build a whitelist of source-worthy structures and disable or aggressively spread structures that would make Terrain Diffusion's world feel saturated.

Test terrain placement very carefully under World Scale 2.

## B. Towns and Towers — strong vanilla-like outpost/village candidate

### Current 1.21.1 candidate

- version `1.13.11`
- Minecraft 1.21.1
- NeoForge/Fabric/Quilt release available
- latest 1.21.1 release published 2026-08-15
- adds village variants, pillager outpost variants, and ships
- requires Cristel Lib on the current packaged line

### DrewCraft use

The important hostile content is the expanded **pillager outpost family**. These can become lower-tier `CAMP`/`OUTPOST` strategic sources while the village variants remain friendly/neutral settlements.

### DrewCraft verdict

**High-priority source-content candidate.**

It provides more grounded/vanilla-like source sites than the larger WDA complexes. This makes a good potential complement to a *carefully selected* WDA subset.

Do not automatically classify its villages as hostile.

## C. ChoiceTheorem's Overhauled Village (CTOV)

### Current 1.21.1 candidate

- `3.6.3`
- Minecraft 1.21.1
- NeoForge release
- 20 village/pillager-outpost variants

### DrewCraft verdict

**Alternative to Towns and Towers, not an automatic companion.**

Both mods significantly expand villages/outposts. Test them against the actual desired visual style and Terrain Diffusion; prefer one unless a compatibility/content audit shows they add clearly non-overlapping value.

## D. Repurposed Structures

### Current 1.21.1 candidate

- current 1.21.1 NeoForge line includes `7.5.22`
- release
- broad set of vanilla-style structure variants, including fortress/village variants
- LGPL-3.0-only project listing

### DrewCraft verdict

**Useful but broad; medium priority.**

This can supply many potential source archetypes, but it also modifies/adds many structure families and risks redundancy with Towns and Towers/CTOV/WDA. Consider only after source gaps are identified.

## E. Structory

### Current compatibility

- supports 1.21–1.21.1
- NeoForge/data-pack/server-side forms available
- includes ruins, towers, cottages, graveyards, settlements, boats, manor-style content and light lore

### DrewCraft verdict

**Good atmospheric-world candidate; selective strategic-source potential.**

Likely more useful for exploration texture, ruins, and occasional minor source sites than for the primary hostile kingdom hierarchy. Must be density-tested before inclusion.

## F. Dungeons and Taverns

### Current compatibility

- supports 1.21.1 NeoForge, though the old 1.21.1 NeoForge files are marked beta
- adds vanilla-style dungeons, taverns, ruins, and hostile structures such as illager hideouts/outposts

### DrewCraft verdict

**Interesting content, lower priority for the initial lock.**

The 1.21.1 NeoForge release status is less attractive than Towns and Towers/WDA for the first compatibility spike.

## G. Moog's Voyager Structures

### Current compatibility

- 1.21.1 NeoForge release exists (`4.2.7` line)
- MIT project listing
- 130+ vanilla-style structures

### DrewCraft verdict

**Probably too broad for the first V1 structure layer.**

Could be revisited if we need specific missing archetypes, but adding 130+ structures conflicts with the sparse-world goal unless heavily filtered.

## H. Integrated Dungeons Arise

### DrewCraft verdict

**Reject for baseline despite attractive structures.**

The current 1.21.1 project requires a substantial dependency stack including Create, Farmer's Delight, Integrated API, Quark, Supplementaries, and Amendments. Create is already desired, but the rest would add unnecessary systems/dependency surface solely to obtain structures. The project also explicitly warns against combining it with original When Dungeons Arise without custom structure-set work.

Use original/selective WDA instead if it passes Terrain Diffusion testing.

---

# 5. Structure density/control candidates

## A. Pack-owned structure-set configuration — preferred first

Where source mods expose normal datapack/structure-set controls, DrewCraft should own exact enable/spacing/separation configuration in the production world-build layer.

Advantages:

- no extra runtime dependency;
- exact per-structure control;
- easy to whitelist only source-worthy structures;
- world-generation identity remains explicit and versioned.

This is especially attractive for When Dungeons Arise because its structures expose individual generation controls.

## B. Sparse Structures

### Current candidate

- `3.0` for Minecraft 1.21.1 NeoForge
- release
- file `sparsestructures-neoforge-1.21.1-3.0.jar`
- CurseForge file 6456912
- MIT
- designed to spread out vanilla and modded structures globally

### DrewCraft verdict

**Useful compatibility-spike tool, not automatically required.**

It matches DrewCraft's large-world philosophy extremely well, but a global structure multiplier is less precise than a pack-owned per-structure source configuration. Test it only if maintaining explicit structure-set spacing becomes cumbersome or if it provides cleaner global control without interfering with Terrain Diffusion/world pregeneration.

## C. Limited Structures

### Current compatibility

- supports 1.21.1 NeoForge
- can limit specific structures to a configurable count per dimension

### DrewCraft verdict

**Interesting for unique capitals/major strongholds, but experimental.**

The concept is useful for "only one/few kingdom capitals in the entire bounded world," but the project is small and adds another worldgen dependency. Prefer deterministic world-build/source-selection logic unless testing demonstrates a clear benefit.

## D. Structurify

### Current compatibility

- 1.21.1 NeoForge release/beta lines exist
- can alter frequency, overlap, size, biome and terrain constraints

### DrewCraft verdict

**Do not add by default.**

It is powerful, but structure packs can have project-specific incompatibilities with generic structure-frequency modifiers. In particular, Integrated Dungeons Arise explicitly warns users not to use Structurify/Sparse Structures with its own generation-frequency scheme. Prefer pack-owned configuration for whichever source packs we actually select.

---

# 6. Recommended first structure spike

The first test should be deliberately small:

1. **Vanilla pillager outpost** as the control source.
2. **Towns and Towers** for a few grounded pillager outpost variants.
3. **When Dungeons Arise**, with only a tiny whitelist such as:
   - Illager Campsite
   - Illager Fort
   - one major fortress/palace-class structure
4. Increase spacing aggressively so these structures are genuinely distant on Terrain Diffusion World Scale 2.
5. Pregenerate a representative test region.
6. Index qualifying structures and produce a source-density map/report.
7. Reject the combination if the landscape feels saturated.

This would give DrewCraft a natural hierarchy:

```text
small outpost/camp -> frequent-ish local threat source
fort               -> rarer regional military source
major palace/city  -> very rare high-capacity kingdom source
```

Exact population strength and attack frequency are balance work; the geographic hierarchy itself is architectural.

---

# 7. Recommended first mob-behavior spike

Test separately so overlapping AI mods do not contaminate results.

### Hostile branch A

```text
Enhanced Hordes
+ Enhanced Hordes Tweaks
+ DrewCraft strategic test group
```

Verify:

- externally materialized mobs can participate;
- horde wandering/cooperation works;
- strategic ID/accounting survives;
- mod spawning features can be disabled;
- generic block destruction can be disabled/restricted for strategic entities.

### Hostile branch B

```text
Zombie Hordes
+ DrewCraft strategic test group
```

Run the same tests.

Choose one tactical path or implement only the small missing behaviors in DrewCraft; do not stack multiple horde overhauls merely because each has one appealing feature.

### Friendly branch A

```text
Ethological!
+ DrewCraft strategic herd materialization
```

Verify:

- herd membership does not fight DrewCraft encounter identity;
- herds stay cohesive;
- grazing/water/sleep behavior is affordable;
- player pens/domestication can opt animals out;
- unload/dematerialize is reliable.

### Friendly branch B

```text
Herd Instinct
+ minimal DrewCraft local follow/group goal
```

This is the simpler fallback if Ethological! proves too young/heavy/restrictive.

---

# 8. Promotion rule

No candidate in this document becomes baseline merely because its feature list matches DrewCraft.

Promotion requires:

- exact 1.21.1 NeoForge artifact/source record;
- license/redistribution audit;
- reproducible acquisition + SHA-256 lock;
- dedicated-server boot;
- Windows and Apple Silicon client compatibility where relevant;
- Terrain Diffusion World Scale 2 compatibility for worldgen mods;
- no duplicate subsystem ownership;
- multiplayer/restart/unload testing;
- measured performance;
- clean failure/disable path;
- proof that the mod reduces custom work more than it increases maintenance risk.
