# DrewCraft V1 Execution Status

**Last updated:** 2026-09-12  
**Current phase:** **BP1-BP7 strategic gameplay/ecology complete -> BP8 production convergence next**  
**Current breakpoint handoff:** `docs/CURRENT_BREAKPOINT.md`  
**Breakpoint protocol:** `docs/DEVELOPMENT_BREAKPOINTS.md`

This is the live execution-state overlay for DrewCraft V1. `docs/CURRENT_BREAKPOINT.md` is the exact stop/resume handoff for user-driven **"go"** sessions. `docs/V1_REMAINING_EXECUTION_PLAN.md` remains the detailed path to `1.0.0`.

## Certified platform and integration profile

DrewCraft V1 remains pinned to Minecraft **1.21.1**, NeoForge **21.1.250**, and Java **21**.

The candidate profile contains **34 dependencies total**: 33 exact provider artifacts plus one exact Terrain Diffusion Plus source build. Dedicated-server baseline: **34704011609**. Provider hashes: **34724313143**. Manifest graph: **34724313201**.

Environment/aviation/radar integration through **8B** is implemented at development scope. Final representative client/world acceptance remains BP9/BP10.

## Strategic-world progress

### BP1 — persistence + coarse simulation — PASS

Persistent strategic groups, cached routes, bounded elapsed-time scheduling, and no distant entity/chunk simulation.

### BP2 — coarse routing + ETA + unloaded travel — PASS

64×64 default strategic cells, bounded cached A*, terrain costs, ETA, no forced loading, and a 10,000-block save/restart unloaded-travel proof. Evidence: **34726835776**, **34726857058**.

### BP3 — transactional materialization + casualties — PASS

One durable encounter per group, loaded-chunk-only materialization, idempotent casualties, bounded waves, stale-entity rejection, and restart recovery. Canonical proof: `100 -> kill 37 -> unload/restart -> 63`. Evidence: **34727614866**, concurrency proof **34727505486**.

### BP4 — hostile sources + permanent clearing — PASS

Persistent generated-geography sources, Source Core, mining/explosion clearing, permanent restart-safe neutralization, bounded source production, and clear-versus-launch race safety. Core evidence: **34728862438**. Source Core checkerboard/chat polish: **34729284337**.

### BP5 — hostile factions and large armies — PASS

Detailed contract: `docs/HOSTILE_FORCES_V1.md`.

JSON-driven undead/raider templates support patrols, hordes, raids, armies, and reinforcements; exact source population debits; persistent explainable mission knowledge; non-omniscient targeting; and large represented populations reusing BP3 tactical caps.

Representative proof: `256 strategic -> 64 active -> kill 37 -> 219 strategic / 27 active -> restart -> same mission/counts -> 37 refill slots`. Evidence: **34729884759**, large-army proof **34729684064**, variable-strength source transaction **34729641645**.

### BP6 — path-first bounded siege planner — PASS

Detailed contract: `docs/SIEGE_V1.md`.

Siege occurs only for loaded blocked `RAID`/`ARMY` encounters after ordinary navigation fails repeatedly. Local planning is bounded/cached; gates/doors/useful weak barriers and hardness affect scoring; protected/stateful/decorative blocks are avoided; one deliberate corridor is executed by designated breaker units. Open-gate, sealed-fort, protected-block, decorative-block, role/unit, and hard-work-bound tests pass.

Final BP6 code/test head **`1bab32c0c6028e57f99f8684d7097c9c33ed02fa`**; CI **34730303373 — SUCCESS**. Runtime compile **34730277755 — SUCCESS**.

### BP7 — strategic herds + local-spawn coexistence — PASS

Detailed contract: `docs/HERDS_ECOLOGY_V1.md`.

BP7 uses a deliberately additive wildlife model:

- strategic herds are created only from explicit deterministic `WildHerdDescriptor`s;
- DrewCraft never scans or absorbs existing Minecraft animals into a herd;
- herd IDs derive from dimension + species + migration endpoints;
- `HERD` groups use faction `drewcraft:wildlife`, persisted `MIGRATION_ROUTE` mission state, and no hostile Source Core;
- migration reuses BP1/BP2 cached coarse routes and unloaded arithmetic;
- materialization/casualties/restart reuse BP3 unchanged;
- default tactical cap remains 64 active entities, with the rest of a large herd abstract;
- idempotent re-registration cannot reset an already-moving/casualty-bearing herd;
- `features.strategicHerds` independently pauses herd movement/materialization while preserving herd records;
- disabling the feature collapses only DrewCraft-tagged tactical herd copies, never ordinary local animals;
- `/drewcraft herd create-test|list|ecology` provides diagnostics.

Local ecology is intentionally independent. DrewCraft does not hook global mob-spawn events, replace `NaturalSpawner`, rewrite `SpawnPlacements`, or manipulate `BaseSpawner`; untagged entity joins return before any stale-strategic cancellation path. Thus strategic caps do not quota ordinary night/cave mobs, livestock, mob farms, or vanilla/modded spawners.

Representative automated herd proof:

```text
80 strategic cows
-> abstract migration
-> 64 active / 16 abstract
-> 10 confirmed deaths
-> 70 strategic survivors / 54 active
-> next wave = 10 (64-active ceiling)
-> save/restart preserves HERD + migration mission + counts
-> reconcile -> 70 strategic survivors, TRAVELING
```

Final BP7 code/test head **`dfa507d0ac9c330c16897afe19f88467c06784a6`**; DrewCraft mod CI **34730837899 — SUCCESS**.

Production-world species/count/corridor seeds move to BP8. Representative final-pack observation of migrating herds plus night/cave spawning, a mob farm, and vanilla/modded spawners remains BP9/BP10 acceptance.

## Strategic performance invariant

> **Keep the world abstract while nobody is looking; materialize only what players can interact with; cache expensive decisions; persist every important consequence.**

This now applies to hostile forces and wildlife alike. Ordinary Minecraft ecology remains a separate local system rather than being folded into DrewCraft strategic bookkeeping.

## Remaining critical path

```text
DONE BP1 strategic persistence + coarse scheduler
DONE BP2 coarse routing + ETA + unloaded travel
DONE BP3 transactional materialization + casualties
DONE BP4 hostile sources + permanent clearing
DONE BP5 factions / patrols / hordes / raids / armies / reinforcements
DONE BP6 bounded path-first siege planner
DONE BP7 strategic herds + local-spawn coexistence
→ NEXT BP8 production world / deployment / release / launcher convergence
→ BP9 cross-system scale / failure / recovery hardening
→ BP10 release candidate + hard acceptance
→ 1.0.0
```

## Gate status

| Gate | State | Evidence / remaining condition |
| --- | --- | --- |
| Reproducible manifest/resolver | **PASS** | 34724313201 |
| Provider artifact hashes | **PASS** | 34724313143 |
| Dedicated-server baseline | **PASS** | 34704011609 |
| Environment/radar/aviation dev scope | **PASS** | final visual acceptance later |
| BP1 strategic persistence | **PASS** | focused CI |
| BP2 routing/unloaded travel | **PASS** | 34726835776 + 34726857058 |
| BP3 materialization/casualties | **PASS** | 34727614866 + 34727505486 |
| BP4 hostile sources | **PASS** | 34728862438 |
| BP5 hostile population breadth | **PASS** | 34729884759 + 34729684064 |
| BP6 siege | **PASS** | 34730303373; runtime compile 34730277755 |
| BP7 herds/local spawning | **PASS** | 34730837899; explicit ecology isolation guard |
| BP8 production/release convergence | **NEXT** | world/host/release/updater/launcher convergence |
| V1 full-stack acceptance | **OPEN** | BP9-BP10 |

## Immediate next sequence — BP8

On the next **"go"**, follow `docs/CURRENT_BREAKPOINT.md` and BP8 in `docs/DEVELOPMENT_BREAKPOINTS.md`.

BP8 must converge the production Terrain Diffusion world and pregeneration metadata, real source/herd seeding, production host decision/ARM compatibility, immutable client/server release artifacts and protocol manifest, server update/backup/rollback tooling, off-host restore proof, and one-click Windows plus Apple Silicon macOS install/update/repair paths.

Do **not** begin BP9 full-stack scale/failure/recovery hardening until BP8 is reached, reported, and the user says **"go"** again.
