# DrewCraft Current Development Breakpoint

**Updated:** 2026-09-12  
**Protocol:** `docs/DEVELOPMENT_BREAKPOINTS.md`  
**Last completed breakpoint:** **BP5 — Factions, patrols, hordes, raids, and large armies**  
**Next breakpoint:** **BP6 — Path-first bounded siege planner**

## BP5 status — REACHED

BP5 is complete at implementation/compile/unit/runtime-wiring scope. DrewCraft now has a data-driven hostile population layer on top of the BP1-BP4 strategic substrate.

Detailed contract: `docs/HOSTILE_FORCES_V1.md`.

## Implementation

### Data-driven factions and force roles

Packaged hostile-force content now lives in:

`mods/drewcraft/src/main/resources/data/drewcraft/strategic/factions.json`

`StrategicFactionCatalog` parses the versioned JSON into immutable `StrategicForceTemplate`s. Templates define:

- faction;
- strategic role;
- allowed source classes;
- strength multiplier;
- target policy;
- strategic travel-distance range;
- weighted Minecraft entity composition.

V1 data contains:

- `drewcraft:test_hostile`;
- `drewcraft:undead`;
- `drewcraft:raiders`.

The hostile roles are:

- `PATROL`;
- `HORDE` / warband;
- `RAID`;
- `ARMY`;
- `REINFORCEMENT`.

Undead and raider profiles use meaningfully different entity compositions. Composition allocation is deterministic and always sums exactly to represented strategic strength.

### Variable-size source production

Sources no longer assume every strategic launch costs the same number of units.

A template computes its represented strength from the source base production strength. The source is charged the exact resulting `StrategicGroup.totalStrength()` inside the same synchronized `DrewCraftSavedData` authority used by Source Core clearing.

Before commit DrewCraft verifies source identity/generation, source state, group source ID, faction, dimension, duplicate group ID, and available source budget.

This preserves BP4 clear-versus-launch race safety while allowing genuinely large strategic forces.

Example V1 stronghold army:

```text
base source launch strength = 32
army multiplier = 8
represented army strength = 256
persistent source population debit = 256
```

### Persistent mission state

`StrategicGroup` is now schema **3** and persists a `StrategicMission` containing:

- force-template ID;
- target-knowledge category;
- human-readable knowledge explanation;
- exact objective position;
- mission issue game time.

Schema-1 and schema-2 strategic groups migrate to `LEGACY_ROUTE` mission state using their existing route destination. Future group schemas still fail closed.

The group constructor also verifies that composition counts sum exactly to `totalStrength`.

### Non-omniscient targeting

Target selection explicitly records **why** the force knows its target:

- `SOURCE_GEOGRAPHY` — local/regional routes derived from the source itself;
- `SCOUTED_REGION` — deterministic scouting objective;
- `ALLIED_SOURCE_LOCATION` — another persistent intact same-faction source;
- `LEGACY_ROUTE` — migration state for old groups.

The BP5 source planner has no nearest-player/base lookup. A scouted army target is deterministic from persistent source/template/launch state and carries the explanation `no player position queried`.

This policy is separated from runtime route calculation and is unit-tested as a pure strategic decision.

### Large armies remain lightweight

BP5 deliberately does not increase BP3's tactical caps.

Default loaded limits remain:

- **64 active entities per encounter**;
- **128 successful new strategic entities globally per materialization cycle**;
- **32 encounter records processed per cycle**.

A 256-unit strategic army can therefore travel unloaded as one record while at most 64 of its units exist as tactical entities around players.

### Representative BP5 acceptance proof

The automated large-army scenario proves:

```text
source budget = 384
        |
commit 256-unit ARMY
        v
source budget = 128
        |
materialize encounter
        v
64 tactical reservations, 192 still abstract
        |
37 confirmed deaths
        v
strategic survivors = 219
loaded survivors = 27
        |
next wave eligibility = exactly 37
        |
save / restart
        v
ARMY role + mission + target + 219 population + 27 encounter reservations all preserved
```

At no point does the test require 256 Minecraft entities to be loaded.

## BP5 acceptance evidence

Focused tests cover:

- packaged versioned faction catalog loading;
- undead and raider support for all five hostile roles;
- deterministic exact weighted composition allocation;
- affordability filtering;
- exact variable-strength source population debit;
- BP4 generation-lock compatibility for variable-strength launches;
- mission NBT round trip;
- schema-1/schema-2 mission migration;
- future group-schema rejection;
- non-omniscient scouted target policy without runtime routing/config dependency;
- **256-unit army -> 64 active -> kill 37 -> 219 strategic / 27 active -> exactly 37 refill slots**;
- save/restart preservation of army role, mission, target, casualties, and encounter authority.

### CI

- final BP5 code/test head: **`c8bb18e8e6af986b614db08235c0d8b4202926a9`**
- final DrewCraft mod CI: **run `34729884759` — SUCCESS**
- job: `build-and-test` — **SUCCESS**
- command: `gradle -p mods/drewcraft test build --stacktrace --no-daemon`
- representative large-army proof run **`34729684064` — SUCCESS**
- variable-strength source transaction run **`34729641645` — SUCCESS**

## Important V1 boundaries

BP5 establishes force identity, faction composition, represented population size, mission/objective knowledge, exact source accounting, bounded materialization, casualty persistence, and restart behavior.

Still intentionally deferred:

- exact balance/frequency/composition tuning beyond sane V1 defaults;
- final production structure-to-faction assignments during world-build integration;
- representative in-world visual/load testing in the final pack;
- any fortification block-breaking or breach selection — **BP6 owns siege behavior**.

## Next: BP6

On the next **"go"**, continue until BP6 is reached.

BP6 must implement a bounded path-first siege planner with these rules:

1. ordinary navigation is attempted first;
2. siege planning runs only for loaded, genuinely blocked encounters;
3. only siege-capable hostile roles/units may breach;
4. breach search is bounded and cached;
5. gates, doors, weak/useful barriers, hardness, and protected tags affect scoring;
6. a breach is a constrained useful corridor rather than indiscriminate destruction;
7. an open gate is used instead of breaking walls;
8. a sealed fort yields a useful deliberate breach;
9. irrelevant nearby decorative structures/blocks are not selected merely because they are close.

Stop and report again when BP6 passes. Do not begin BP7 herds/local-spawn coexistence until the user says **"go"** after that report.
