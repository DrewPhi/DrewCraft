# DrewCraft V1 Siege Contract

> **Post-V1 design archive (2026-09-16):** this completed design is not part of the focused V1 shipping profile. See `FURTHER_IDEAS.md`.

**Scope:** BP6 path-first bounded siege behavior for materialized hostile raids and armies.

## Core rule

> Ordinary Minecraft navigation gets the first chance. Deliberate block destruction is a local fallback for a loaded encounter that has repeatedly failed to find a path toward its already-known strategic objective.

DrewCraft does **not** run siege planning for distant strategic records, does not load chunks to plan a siege, and does not let every hostile mob break arbitrary nearby blocks.

## Eligibility

Only strategic groups with role `RAID` or `ARMY` may initiate V1 deliberate breaching.

Only designated breaker entity types may execute a breach:

- `minecraft:zombie`
- `minecraft:husk`
- `minecraft:vindicator`
- `minecraft:ravager`

Skeletons, pillagers, witches, patrols, hordes, reinforcements, herds, and ordinary locally spawned mobs never gain DrewCraft siege breaking merely by being nearby.

## Path-first runtime

Every siege cycle:

1. inspect only a bounded number of already-materialized encounters;
2. choose one currently loaded designated breaker;
3. project the persistent mission target into a small local already-loaded goal;
4. ask normal Minecraft navigation for a path first;
5. if a normal path exists, use it and clear any blocked/breach state;
6. only after repeated failed path checks may the local breach planner run.

An open gate/door corridor therefore wins without any block destruction.

## Bounded local planner

Default V1 bounds:

- check interval: **20 ticks**;
- local snapshot radius: **12 blocks**;
- repeated ordinary-navigation failures required: **3**;
- encounters inspected per cycle: **8**;
- local planner node-expansion cap: **1,200**;
- breach cells allowed in one corridor: **4**;
- break cooldown per encounter: **30 ticks**.

The snapshot uses only already-loaded blocks around the tactical encounter. Unloaded cells are treated as protected/impassable rather than triggering a load.

The pure planner scores progress toward the local objective. Traversal preference is approximately:

`OPEN < GATE < DOOR < WEAK_BARRIER < SOLID_BARRIER << DECORATIVE < PROTECTED`

Hardness increases destruction cost. This means a useful door/gate or weak section is preferred over a hard wall, while destroying an unrelated nearby statue provides no value simply because it is close.

## Protection semantics

`#drewcraft:siege_protected` is completely unbreachable. V1 ships with critical examples including bedrock-class blocks and the DrewCraft Source Core.

Any block position containing a block entity is also protected by default. This prevents the planner from casually selecting containers, Create machinery, or other stateful blocks as a breach target.

`#drewcraft:siege_decorative` is data-pack extensible and receives a very large planning penalty. It is not treated as the nearest easy target; it can only enter a route if the objective geometry genuinely makes it useful and no substantially better route exists.

Servers/modpack data can extend both tags without code changes.

## Constrained execution

A successful plan is a local corridor, not permission to grief.

- only blocks explicitly present in the current cached corridor may be broken;
- only one designated breaker executes the corridor;
- the breaker approaches the planned breach location before breaking;
- the exact target block is reclassified immediately before destruction;
- protected/non-breachable changes invalidate the plan;
- after every successful block break the plan is invalidated and the world is re-snapshotted on a later cycle;
- there is no nearest-block destruction loop.

The cache is keyed by encounter and local geometry fingerprint. Repeated blocked checks reuse an unchanged plan; world changes force replanning.

## BP6 acceptance scenarios

Automated pure-planner evidence covers:

1. **Open gate:** an open corridor through a fort wall produces `OPEN_ROUTE` and zero breach steps.
2. **Sealed fort:** a sealed wall with a useful weak section produces a constrained breach through that section.
3. **Gate preference:** a closed gate is preferred over a nearby harder wall even with a small detour.
4. **Decorative safety:** decorative cells near the attackers but irrelevant to the objective are not selected.
5. **Protected safety:** protected cells never appear in a breach corridor.
6. **Work bound:** a deliberately impossible local map terminates at the configured expansion bound.
7. **Role/unit safety:** only `RAID`/`ARMY` groups and designated breaker types are eligible.

Representative final-pack observation of real mobs using gates and breaking a sealed fort is repeated during BP9/BP10 full-stack acceptance, where Terrain Diffusion terrain, Create builds, player structures, and actual multiplayer latency are present.
