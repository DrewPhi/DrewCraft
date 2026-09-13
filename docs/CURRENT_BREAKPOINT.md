# DrewCraft Current Development Breakpoint

**Updated:** 2026-09-12  
**Protocol:** `docs/DEVELOPMENT_BREAKPOINTS.md`  
**Last completed breakpoint:** **BP6 — Path-first bounded siege planner**  
**Next breakpoint:** **BP7 — Strategic herds + local-spawn coexistence**

## BP6 status — REACHED

BP6 is complete at implementation/compile/unit/runtime-wiring scope. Detailed contract: `docs/SIEGE_V1.md`.

## Implemented

- `SiegeRuntime` runs only for already-materialized, loaded strategic encounters.
- Only `RAID` and `ARMY` groups are siege-capable in V1.
- Only designated breakers (`zombie`, `husk`, `vindicator`, `ravager`) may execute a deliberate breach.
- Normal Minecraft navigation is always attempted before any breach planning.
- A breach plan is allowed only after **3 consecutive ordinary-navigation failures**.
- Local snapshots are **12-block radius**, use only already-loaded chunks, and classify unloaded cells as protected rather than loading them.
- `BoundedSiegePlanner` uses a pure deterministic local search with a default **1,200-node hard expansion cap** and **4 breach-cell maximum**.
- Plans are cached per encounter/local-geometry fingerprint; unchanged geometry reuses the plan.
- Block scoring accounts for objective progress, hardness, open space, doors, gates, weak barriers, solid barriers, decorative penalties, and protected cells.
- `#drewcraft:siege_protected` is unbreachable; V1 includes bedrock-class blocks and `drewcraft:source_core`.
- Any block with a block entity is protected by default, shielding containers/machines/stateful blocks.
- `#drewcraft:siege_decorative` is data-pack extensible and receives a very large planning penalty.
- A successful breach is a constrained corridor, not general mob griefing.
- One designated breaker approaches an explicitly planned breach block before destruction.
- The exact block is revalidated immediately before breaking.
- After each successful break the plan is invalidated and the world must be re-snapshotted before another block can be broken.
- Default runtime bound is **8 siege encounters per 20-tick cycle** with a **30-tick per-encounter break cooldown**.
- `features.strategicSiege` is an independent server-side kill switch.

## BP6 acceptance evidence

Focused tests prove:

1. **open gate/open entrance** -> `OPEN_ROUTE`, zero breach blocks;
2. **sealed fort** -> useful weak section selected rather than arbitrary wall destruction;
3. **closed gate vs hard wall** -> gate selected even with a small detour;
4. nearby irrelevant decorative cells are not selected merely because they are close;
5. protected cells never enter a breach corridor;
6. impossible geometry terminates at the configured node/work bound;
7. only `RAID`/`ARMY` roles may siege;
8. only designated breaker entity types may execute a breach.

The real NeoForge runtime compiles against the pinned Minecraft 1.21.1 / NeoForge 21.1.250 APIs, including vanilla navigation, loaded-world block classification, block tags, and deliberate block destruction.

### CI

- final BP6 code/test head: **`1bab32c0c6028e57f99f8684d7097c9c33ed02fa`**
- DrewCraft mod CI: **run `34730303373` — SUCCESS**
- job `build-and-test` — **SUCCESS**
- earlier runtime compile run **`34730277755` — SUCCESS**

## Important deferred acceptance

The final pack still needs representative visual multiplayer tests showing actual mobs choosing an open castle entrance and deliberately breaching a sealed player-built fort. That belongs to BP9/BP10 full-stack acceptance, where final world terrain, Create builds, latency, and real structures are present.

No BP7 herd/ecology work has started.

## Next: BP7

On the next **"go"**, implement strategic wild herds plus coexistence proof for normal Minecraft ecology.

Required outcome: persistent wild herds use the shared abstract/materialized kernel without absorbing protected/domesticated animals, while normal night/cave spawning, mob farms, and ordinary spawners continue working independently.

Stop and report again when BP7 passes. Do not begin BP8 production/release convergence until the user says **"go"** after that report.
