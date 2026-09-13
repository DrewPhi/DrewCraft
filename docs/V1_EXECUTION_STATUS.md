# DrewCraft V1 Execution Status

**Last updated:** 2026-09-12  
**Current phase:** **BP1-BP6 strategic hostile-world gameplay complete -> BP7 herds/ecology next**  
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

JSON-driven undead/raider force templates now support patrols, hordes, raids, armies, and reinforcements; exact variable-strength source debits; persistent explainable mission knowledge; non-omniscient targeting; and large represented populations that reuse BP3 tactical caps.

Representative proof: `256 strategic -> 64 active -> kill 37 -> 219 strategic / 27 active -> restart -> same mission/counts -> 37 refill slots`. Evidence: **34729884759**, large-army proof **34729684064**, variable-strength source transaction **34729641645**.

### BP6 — path-first bounded siege planner — PASS

Detailed contract: `docs/SIEGE_V1.md`.

Implemented:

- independent `features.strategicSiege` kill switch;
- siege only for already-materialized loaded `RAID`/`ARMY` encounters;
- designated breaker types only (`zombie`, `husk`, `vindicator`, `ravager`);
- normal Minecraft navigation attempted first every siege check;
- 3 failed navigation checks required before planning;
- already-loaded 12-block-radius local snapshots only; unloaded cells become protected rather than force-loaded;
- deterministic bounded local breach search with 1,200-node default hard limit;
- maximum 4 breach cells in one corridor;
- encounter/local-geometry plan caching;
- scoring for objective progress, hardness, gates, doors, weak barriers, hard barriers, decorative penalties, and protected blocks;
- `#drewcraft:siege_protected` hard exclusion, including Source Core and bedrock-class blocks;
- block entities protected by default so stateful containers/machines are not casually breached;
- data-pack-extensible `#drewcraft:siege_decorative` high-cost tag;
- one designated breaker approaches only the explicit planned breach position;
- block is revalidated immediately before destruction;
- every successful break invalidates the plan and forces a later re-snapshot/replan;
- max 8 siege encounters inspected per 20-tick cycle and 30-tick per-encounter break cooldown.

Acceptance tests prove:

- open entrance/gate -> open route, **zero destruction**;
- sealed fort -> useful weak breach;
- gate preferred over harder wall even with a detour;
- irrelevant decorative cells are not chosen because of proximity;
- protected cells never enter a breach corridor;
- impossible geometry obeys the hard search bound;
- only eligible strategic roles and designated units can breach.

The actual NeoForge loaded-world runtime compiles against the pinned 1.21.1 mappings, including vanilla navigation and deliberate block destruction.

Final BP6 code/test head **`1bab32c0c6028e57f99f8684d7097c9c33ed02fa`**; DrewCraft mod CI **34730303373 — SUCCESS**. Earlier full runtime compile **34730277755 — SUCCESS**.

Representative visual multiplayer castle tests remain BP9/BP10 acceptance, where final Terrain Diffusion terrain and real player/Create structures are available.

## Strategic performance invariant

> **Keep the world abstract while nobody is looking; materialize only what players can interact with; cache expensive decisions; persist every important consequence.**

In particular, distant groups never run siege logic. Siege work is small, local, bounded, cached, and only exists while a relevant tactical encounter is loaded.

## Remaining critical path

```text
DONE BP1 strategic persistence + coarse scheduler
DONE BP2 coarse routing + ETA + unloaded travel
DONE BP3 transactional materialization + casualties
DONE BP4 hostile sources + permanent clearing
DONE BP5 factions / patrols / hordes / raids / armies / reinforcements
DONE BP6 bounded path-first siege planner
→ NEXT BP7 strategic herds + local-spawn coexistence
→ BP8 production world / deployment / release / launcher convergence
→ BP9 cross-system scale / failure / recovery hardening
→ BP10 release candidate + hard acceptance
→ 1.0.0
```

Production-world/pregeneration, host benchmarking, immutable release artifacts, server updater/backups, and Windows/macOS launcher work remain parallel tracks and converge before the RC freeze.

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
| BP7 herds/local spawning | **NEXT** | ecology/coexistence proof |
| Production world/pregen/restore | **OPEN / PARALLEL** | converge by BP8 |
| ARM/production host benchmark | **OPEN / PARALLEL** | representative world required |
| Release/server updater | **OPEN / PARALLEL** | converge by BP8 |
| Windows/macOS launcher | **OPEN / PARALLEL** | converge by BP8 |
| V1 full-stack acceptance | **OPEN** | BP9-BP10 |

## Immediate next sequence — BP7

On the next **"go"**, follow `docs/CURRENT_BREAKPOINT.md` and the BP7 definition in `docs/DEVELOPMENT_BREAKPOINTS.md`.

BP7 must add persistent wild herds using the same abstract/materialized kernel while explicitly excluding named/domesticated/leashed/penned/player-owned animals from silent absorption, and must prove strategic systems do not replace or suppress ordinary night/cave spawning, mob farms, or normal spawners.

Do **not** begin BP8 production/release convergence until BP7 is reached, reported, and the user says **"go"** again.
