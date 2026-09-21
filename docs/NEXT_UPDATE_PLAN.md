# DrewCraft Next Update Plan

**Status:** design/audit plan only; no gameplay dependency is promoted by this document  
**Target:** first post-current-V1 integration pass  
**Primary constraint:** **no world reset, no new ore/resource world generation, and no new strategic/story axis**

## Goal

The next update should make the existing DrewCraft pillars reinforce one another instead of behaving like separate mod islands.

The target loop is:

**explore enormous Terrain Diffusion terrain → find WDA dungeons/resources → bring loot home by vehicle → process/manufacture with Create → build better MTS equipment/vehicles → establish rail/road/air infrastructure → explore farther**

This update deliberately does **not** introduce the deferred Covenant/cult story, strategic armies, sieges, herds, weather, or another dimension. It deepens the current survival/industry/exploration axis.

## Hard design rules

1. **No world regeneration requirement.** New content must work in the already-generated world without requiring new ores, deposits, biomes, structures, or terrain resources.
2. **Create owns general-purpose industrial materials and fabrication.**
3. **MTS owns vehicle-specific components, vehicle workbenches, final assembly, vehicle physics, and installed vehicle parts.**
4. **Generic duplicate stock materials are unified; functional MTS components are preserved.**
5. **Existing MTS vehicle difficulty should remain approximately stable.** Recipe integration is not an excuse to make vehicles dramatically cheaper or more expensive.
6. **MTS workbenches stay.** Create factories produce stock/components that feed the MTS garage/hangar.
7. Prefer configuration/datapack/DrewCraft integration code over upstream forks.
8. Do not add a new tech tree merely because an addon exposes one. Features may be hidden, recipe-gated, or simply left unused until they serve DrewCraft.

---

# Candidate additions

## 1. Create Crafts & Additions + MTS bioethanol bridge — highest priority

Why:

- adds Create-native biomass/bioethanol production from renewable materials already present in the world;
- adds rods, wires, the Rolling Mill, and useful Create manufacturing vocabulary;
- can bridge kinetic power and electricity, but DrewCraft does not need to make electricity a new progression axis immediately;
- requires no new ore generation for the intended DrewCraft loop.

Target loop:

**farm crops/plants → Create processing → biomass → bioethanol → storage/fuel station → MTS cars/trucks/aircraft**

Implementation intent:

- add Create Crafts & Additions only after exact 1.21.1 NeoForge/Create-6 compatibility smoke passes;
- configure C&A bioethanol as an accepted MTS vehicle fuel through MTS fuel configuration/integration;
- keep MTS fuel pumps/tanks as the player-facing vehicle fueling hardware;
- test fluid transfer between Create tanks/pipes and MTS fuel infrastructure;
- initially avoid making motors/alternators/large electrical infrastructure mandatory for vehicle progression;
- no crude-oil worldgen is introduced in this update.

This is the first experiment to implement.

## 2. Create: Steam 'n' Rails

Purpose: deepen the rail network that already belongs in DrewCraft's enormous world.

Desired content:

- richer track options;
- semaphores/signaling;
- conductors;
- coupling;
- whistles and railway infrastructure.

Constraint: the 1.21.1 NeoForge path must be treated as a compatibility candidate, not assumed safe. It must pass Create 6, Aeronautics/Sable, High Seas, MTS coexistence, dedicated-server restart, and chunk-crossing tests before promotion.

## 3. Create: Enchantment Industry

Purpose: connect WDA dungeon exploration and XP to Create industry.

Desired loop:

**dungeon/XP/enchanted loot → fluid XP/storage/processing → automated enchanting/repair/book handling → better player equipment**

No new terrain resources are required. This should make dungeon returns useful to the factory rather than creating a separate progression island.

## 4. Create Stuff 'N Additions

Purpose: add Create-native personal equipment rather than importing an unrelated fantasy armor ecosystem.

Desired role:

- exoskeleton/engineering equipment;
- jetpack and utility gear;
- drills/grappling/industrial tools where balanced.

Acceptance rule: gear must not trivialize MTS aircraft, survival, WDA combat, or Create progression. Individual recipes/features may be disabled or rebalanced.

## 5. Create: Connected

Purpose: add small Create-compatible automation/utility pieces that improve large factories without introducing another gameplay pillar.

Treat as a quality-of-life/engineering expansion, not a progression rewrite.

## 6. Lootr

Purpose: make sparse WDA dungeons work well in multiplayer.

Desired behavior:

- each player gets their own loot instance from supported containers;
- no new structures or resources are generated;
- verify WDA container compatibility and server persistence before promotion.

---

# DrewCraft integration layer

The larger value is not the six mods individually. The larger value is making the pack one economy.

The DrewCraft integration layer should own:

- MTS crafting overrides that consume Create/C&A stock;
- the MTS bioethanol fuel bridge;
- recipe normalization across duplicate generic materials;
- curated WDA loot additions;
- optional feature gating for addon content that creates unwanted parallel tech trees;
- compatibility tests that ensure the server/client share the same integrations.

## WDA loot integration

Do **not** make Create/MTS progression primarily dungeon-gated. Normal manufacturing remains the reliable path.

WDA loot may occasionally contain:

- Precision Mechanisms;
- Electron Tubes;
- brass/iron/copper sheets;
- selected MTS circuits/processors;
- selected vehicle repair/components;
- other expensive-but-manufacturable industrial parts.

This makes exploration accelerate industry without replacing industry.

---

# MTS ↔ Create material policy

Canonical rule:

> **Create owns general-purpose materials and industrial fabrication. MTS owns vehicle-specific components and final assembly. Generic duplicate stock materials are unified; functional vehicle components are preserved.**

## Canonical stock materials

| Function | Canonical DrewCraft item |
| --- | --- |
| structural sheet metal | Create Iron Sheet |
| copper sheet | Create Copper Sheet |
| precision/high-tier sheet | Create Brass Sheet |
| reinforced specialty sheet | Create Sturdy Sheet |
| structural rod/shaft stock | Create Crafts & Additions Iron Rod |
| fine iron wire stock | Create Crafts & Additions Iron Wire |
| electrical conductor | Create Crafts & Additions Copper Wire |
| basic mechanical alloy | Create Andesite Alloy |
| electronic primitive | Create Electron Tube |
| precision assembly | Create Precision Mechanism |
| vehicle plastic | MTS Plastic, until a clearly better canonical replacement exists |

MTS generic Metal Sheet/Plating, Screws, Metal Tube, and Copper Wire remain present for compatibility but should stop being normal DrewCraft crafting inputs once the overrides are active.

## Preserve these as MTS components

Keep MTS identity for:

- pistons;
- springs;
- spark plugs;
- circuits;
- processors;
- headlights;
- hydraulics;
- engines;
- wheels;
- aircraft propellers/rotors;
- seats/harnesses;
- fuel tanks and vehicle fuel hardware;
- specialized cargo bodies;
- weapon mounts;
- instruments;
- repair equipment;
- other items whose identity/behavior is specifically automotive or aviation.

---

# Raw-material equivalence audit

This section audits the proposed normalization against the current MTS Official Pack recipe economy.

The public NeoForge V28.1 recipe source was used for the detailed arithmetic because it exposes the individual material lists clearly. DrewCraft currently ships MTS Official Pack V29. **Before implementation, the exact installed V29 must generate/dump its complete MTS crafting overrides and the transform must be rerun against that dump.** No V28.1-only recipe should be blindly shipped.

## Verified Create/C&A stock costs

- Create Iron Sheet: 1 iron ingot → 1 sheet via pressing.
- C&A Iron Rod: 1 iron ingot → 2 rods in the Rolling Mill = **0.5 iron ingot per rod**.
- C&A Iron Wire: 1 iron sheet → 2 wire = **0.5 iron ingot per wire**.
- C&A Copper Wire: 1 copper sheet → 2 wire = **0.5 copper ingot per wire**.

## Generic MTS substitutions

| Current MTS input | Current raw cost | Proposed canonical input | Proposed raw cost | Delta |
| --- | ---: | --- | ---: | ---: |
| 1 MTS Metal Sheet/Plating | 0.544 iron ingot | 0.5 Create Iron Sheet (implemented as 2 plating-equivalents → 1 sheet) | 0.500 iron | **−8.2%** |
| 1 MTS Screw | 0.111 iron ingot | 0.25 C&A Iron Rod (implemented near 4 screws → 1 rod) | 0.125 iron | **+12.5%** |
| 1 MTS Metal Tube | 0.544 iron ingot | 1 C&A Iron Rod | 0.500 iron | **−8.2%** |
| 1 MTS Copper Wire | 0.25 gold + 0.25 redstone | 1 C&A Copper Wire | 0.5 copper | intentional material correction |

The first three conversions intentionally straddle the old cost rather than all moving in the same direction, so whole vehicle recipes stay very close to the original iron burden.

### Integer rule

MTS material lists require whole items. For screws, use the integer number of C&A iron rods that minimizes raw-iron error around **1 rod per 4 old screws** rather than always rounding upward.

Examples:

- 24 screws → 6 rods;
- 42 screws → 11 rods;
- 45 screws → 11 rods;
- 48 screws → 12 rods;
- 58 screws → 15 rods;
- 90 screws → 23 rods;
- 120 screws → 30 rods.

Direct structural iron should remain cost-neutral:

- 1 old structural iron ingot → 1 Create Iron Sheet when a fabricated sheet makes sense;
- 1 old iron block used as generic engine/chassis mass → an exact 9-ingot-equivalent mix such as **6 Iron Sheets + 6 Iron Rods**;
- special vanilla ingredients such as glass, wood, wool, diamonds, obsidian, dyes, etc. remain unless there is a specific integration reason to change them.

---

# Audited MTS component recipes

## Core manufacturing components

| MTS component | DrewCraft recipe/policy | Old raw-material burden | New raw-material burden | Audit |
| --- | --- | --- | --- | --- |
| Metal Sheet/Plating | retire from normal recipes; use Create Iron Sheet | 0.544 iron each | 0.500 iron-equivalent each | −8.2% |
| Screws | retire from normal recipes; use C&A Iron Rod at ~4:1 | 0.111 iron each | 0.125 iron-equivalent each | +12.5% |
| Metal Tube | retire from normal recipes; use C&A Iron Rod 1:1 | 0.544 iron each | 0.500 iron | −8.2% |
| Copper Wire | retire from normal recipes; use C&A Copper Wire 1:1 | 0.25 gold + 0.25 redstone | 0.5 copper | intentional correction |
| Small Piston | **1 Iron Sheet + 1 Iron Rod → 2 MTS Pistons** | 0.722 iron each | 0.750 iron each | **+3.8%** |
| Spring | **1 C&A Iron Wire + 2 Iron Nuggets → 1 MTS Spring** | 0.767 iron | 0.722 iron | **−5.8%** |
| Spark Plug | **2 Iron Rods + 1 C&A Copper Wire + 1 Quartz → 2 MTS Spark Plugs** | ~0.556 iron each plus quartz/flint | 0.500 iron each + 0.25 copper | ~−10% iron; adds real copper |
| Headlight | **2 Iron Sheets + 1 C&A Copper Wire + 1 Redstone Lamp + 1 Glass Pane → 2 MTS Headlights** | 1.0 iron each + old wire/lamp | 1.0 iron each + copper/lamp | iron-exact |
| Electronic Circuit | **1 Create Electron Tube + 1 C&A Copper Wire + 1 MTS Plastic → 2 MTS Circuits** | per circuit: ~0.125 gold + 3.125 redstone + 1 quartz + 0.5 plastic | per circuit: 0.5 iron + 0.25 copper + 4 redstone + 0.5 quartz + 0.5 plastic | comparable burden, moves fake gold wire to real copper and Create electronics |
| Processing Unit | **1 Create Precision Mechanism + 2 MTS Circuits + 1 Iron Rod → 2 MTS Processors** | per processor: ~1.311 iron + 0.625 gold + 5.625 redstone + 1 quartz + 0.5 plastic | per processor: ~1.306 iron + 0.5 gold + 4 redstone + 0.25 copper + 0.5 quartz + 0.5 plastic, plus Andesite/wood/assembly work from the Precision Mechanism | **iron almost exact (−0.4%)**; somewhat less rare electronic raw material, compensated by multi-step Create assembly |
| Plastic | keep MTS Plastic initially | existing MTS recipe | existing MTS recipe | no reason to create another plastic system |
| Hydraulics | preserve MTS Hydraulic System; only add/rewrite recipe after exact V29 dump | V28.1 item exposes no equivalent standalone raw-material recipe for a clean comparison | candidate: Create Fluid Pipe + Copper Sheets + Iron Rods + Andesite Alloy | **not yet equivalence-certified** |
| Armored Plating | preserve MTS Armored Plating; only use after budgeting against the vehicle it replaces | no normal V28.1 standalone material recipe to compare | candidate heavy recipe can use Sturdy Sheet + iron sheets | **must be costed at vehicle level before use** |

### Why the processor recipe outputs two

A one-for-one Precision Mechanism → Processor recipe makes processors noticeably more expensive in gold/industrial inputs than the current MTS economy. Producing **2 processors from 1 Precision Mechanism + 2 Circuits + 1 Iron Rod** restores the old iron burden almost exactly while retaining meaningful Create sequenced assembly.

---

# Wheels, seats, and aircraft parts

| MTS part | Proposed recipe translation | Raw-cost note |
| --- | --- | --- |
| Small Wheel | 1 Iron Sheet + 1 MTS Plastic | old metal content ≈1.089 iron; new =1 iron (−8.2%) |
| Medium Wheel | 1 Iron Sheet + 2 MTS Plastic | old metal content ≈1.089 iron; new =1 iron (−8.2%) |
| Large Wheel | 1 Iron Sheet + 3 MTS Plastic | old metal content ≈1.089 iron; new =1 iron (−8.2%) |
| Seat | 1 Iron Sheet + 2 Iron Rods | old ≈2.178 iron; new =2.0 iron (−8.2%) |
| Seat Harness | 1 Iron Sheet + existing wool/string | old ≈1.089 iron; new =1.0 iron (−8.2%) |
| Small 2-blade prop | 1 Iron Rod + existing planks | old generic metal ≈0.544 iron; new =0.5 (−8.2%) |
| Small 3-blade prop | 1 Iron Sheet + 2 Iron Rods + existing redstone/dyes | old generic metal ≈2.089 iron; new =2.0 (−4.3%) |
| Large 2-blade prop | existing obsidian + 1 Iron Sheet + 2 Iron Rods | old generic metal ≈2.089 iron; new =2.0 (−4.3%) |
| Helicopter rotor | 2 Iron Sheets + 3 Iron Rods + existing iron bars/dyes | old generic metal ≈3.633 iron before bars; new =3.5 (−3.7%) |
| Bell 206 rotor | translate 20 plating → 10 sheets, 6 tubes → 6 rods, retain hydraulics/bars | within roughly 6% of old generic iron burden before hydraulics |

### Important audit correction: do not substitute Create Propeller wholesale

Although semantically tempting, the base Create Propeller costs **4 Iron Sheets + 1 Andesite Alloy**. That is much more expensive than several MTS aircraft propellers.

Therefore:

- **Create Propeller remains a Create component.**
- **MTS aircraft propellers/rotors remain MTS components.**
- Their duplicate generic metal inputs are normalized, but they are not replaced by the Create Propeller item.

---

# Engine policy

Engines remain MTS items and are still crafted/selected through MTS's vehicle-part ecosystem.

First-pass rule: translate generic stock while preserving the existing engine's component identity and approximate raw cost.

Examples:

- old MTS plating → Create Iron Sheets at 2:1;
- old screws → C&A Iron Rods near 4:1;
- old tubes → C&A Iron Rods 1:1;
- old MTS wire → C&A Copper Wire 1:1;
- direct structural iron → equal-iron Create sheet/rod combinations;
- MTS pistons and spark plugs stay and use their audited new recipes;
- obsidian, blaze powder, redstone, etc. stay unless there is a deliberate reason to change them.

A later semantic pass may fix oddities such as spark plugs in turbine/jet recipes, but it must be **cost-neutral within roughly ±10%** by replacing deleted components with appropriate circuits, processors, Precision Mechanisms, sheets, or rods rather than simply making the engine cheaper.

Do not mix the economy conversion and realism rewrite into one unmeasured change.

---

# Vehicle-body iron-equivalence audit

The table below applies the audited conversion rules to the 17 current Official Pack vehicle-body recipes.

It counts the iron-equivalent burden of the generic MTS stock being replaced plus obvious direct vanilla iron-bearing body ingredients. Separately installed engines/wheels/propellers remain their own component recipes and are audited separately.

| Vehicle | Current approx. iron-equivalent | Proposed approx. iron-equivalent | Delta |
| --- | ---: | ---: | ---: |
| Bell 206 | 45.89 | 45.61 | **−0.6%** |
| Bell 47G | 22.73 | 23.00 | **+1.2%** |
| Comanche | 50.48 | 49.67 | **−1.6%** |
| E500 | 56.63 | 57.51 | **+1.6%** |
| Firetruck | 61.42 | 59.28 | **−3.5%** |
| 1969 Mustang | 53.00 | 51.89 | **−2.1%** |
| FT-17 | 113.60 | 111.44 | **−1.9%** |
| GMC Brigadier | 51.02 | 49.78 | **−2.4%** |
| MC-172 | 7.93 | 8.00 | **+0.8%** |
| Mercedes 230 | 59.36 | 57.89 | **−2.5%** |
| PZL.37 Łoś | 72.67 | 68.89 | **−5.2%** |
| PZL P.11 | 26.24 | 25.00 | **−4.7%** |
| Quad | 11.20 | 10.89 | **−2.8%** |
| Scout | 46.58 | 45.39 | **−2.6%** |
| Skyhawk | 42.37 | 40.67 | **−4.0%** |
| Trimotor | 96.58 | 91.50 | **−5.3%** |
| Vulcanair | 55.08 | 54.72 | **−0.6%** |

**Result:** every audited vehicle body stays between approximately **−5.3% and +1.6%** of its current iron-equivalent burden. This is the desired range: the industrial process changes substantially, but the raw-material difficulty does not.

The remaining balance change is the intentional electrical-material correction: MTS's old pseudo-copper wire consumes gold/redstone, while C&A wire consumes actual copper. That change should be playtested because copper is more abundant even though the metal mass per wire increases.

---

# MTS crafting implementation strategy

MTS already provides `config/mtscraftingoverrides.json` specifically so modpacks/servers can replace MTS bench material lists with arbitrary modded items.

Use that mechanism instead of forking the MTS Official Pack.

Implementation procedure:

1. On the **exact installed V29**, enable/generate the complete MTS crafting override dump.
2. Commit a canonical DrewCraft source/template for the desired overrides, not an ad-hoc hand-edited live-server file.
3. Transform every Official Pack recipe using the audited material rules.
4. Hand-review engines, wheels, propellers, electronics, weapons, and unusual vehicle variants.
5. Validate every referenced item ID against the exact Create/C&A/MTS versions.
6. Ensure the launcher/server release injects the same override deterministically.
7. Verify JEI/MTS bench displays match actual craftability.
8. Add automated checks for missing IDs and unexpected reintroduction of retired generic stock.
9. Compare raw-resource budgets against the V29 baseline and flag any item outside the target range.

### Balance gates

- generic chassis/body iron-equivalent target: **within ±10%**, preferably ±5%;
- engines: **within ±10%** of old raw-metal burden unless explicitly approved;
- electronics may shift from gold to copper/iron/redstone but should not become trivial;
- no vehicle becomes available without its meaningful MTS functional parts;
- no recipe should require new worldgen-only resources.

---

# Development order

## Phase A — establish the material economy first

1. Resolve and smoke-test exact Create Crafts & Additions 1.21.1 NeoForge artifact with current Create 6 stack.
2. Dump exact MTS V29 crafting overrides.
3. Generate the audited DrewCraft MTS override set.
4. Add tests for raw-material-equivalence budgets.
5. Verify MTS benches and JEI.
6. Add bioethanol fuel acceptance to MTS.
7. Test farm → bioethanol → MTS pump → car/plane end to end.

This phase should happen before the other addon integrations so later content enters an already coherent economy.

## Phase B — add the low-axis expansions

In compatibility-tested order:

1. Lootr;
2. Create: Connected;
3. Create: Enchantment Industry;
4. Steam 'n' Rails;
5. Create Stuff 'N Additions.

The order may change if dependency/compatibility evidence makes another ordering safer.

## Phase C — cross-system integration

- curated WDA industrial loot;
- rail logistics for bulk industrial materials/fuel;
- Create tank/pipe ↔ MTS fuel infrastructure tests;
- addon recipe normalization so no new duplicate metal/wire/plate economy appears;
- equipment balance checks so exoskeleton/jetpack gear does not invalidate MTS aircraft or normal survival.

---

# Acceptance criteria

The next update is ready only if:

- the existing world loads unchanged and no reset/regeneration is required;
- no selected addon requires a new ore/resource worldgen layer for DrewCraft progression;
- all current MTS vehicles/parts remain craftable;
- MTS workbenches remain the final vehicle assembly interface;
- the exact V29 recipe audit passes the ±10% raw-metal budget gate;
- bioethanol can be manufactured from renewable existing-world inputs and consumed by MTS vehicles;
- Create/MTS fluid transfer and fueling survive server restart;
- WDA + Lootr works correctly for multiple players;
- Create trains/Steam 'n' Rails survive chunk crossing and restart;
- Create Enchantment Industry does not create XP duplication;
- Stuff 'N Additions gear does not trivialize survival/vehicles;
- client and server resolve the same immutable dependency/config set;
- fresh join, same-world restart, backup/restore, and multiplayer smoke all pass.

## Non-goals

Still deferred:

- Project Atmosphere/Simple Clouds/weather-driven flight;
- seasons;
- cult/Covenant story;
- strategic armies and unloaded marches;
- sieges;
- Source Cores;
- strategic herds;
- custom endgame progression;
- new dimensions;
- new ore/deposit worldgen;
- broad difficulty rebalance unrelated to integration.

This update is about making **the world we already have** feel deeper and more coherent.
