# DrewCraft Current Development Breakpoint

**Updated:** 2026-09-12  
**Protocol:** `docs/DEVELOPMENT_BREAKPOINTS.md`  
**Last completed breakpoint:** **BP4 — Hostile sources + permanent clearing**  
**Next breakpoint:** **BP5 — Factions, patrols, hordes, raids, and large armies**

## BP4 status — REACHED

BP4 is complete at implementation/compile/unit/runtime-wiring scope. DrewCraft now has persistent hostile strategic producers layered on the BP1-BP3 strategic kernel.

The detailed implementation contract is `docs/STRATEGIC_SOURCES.md`; `docs/SOURCE_CORE_SPEC.md` remains the product-level clearing contract.

## Implementation

### Persistent source authority

World persistence is now schema **4** and stores versioned `SourceRecord`s alongside strategic groups and encounters.

A source persists:

- stable source UUID;
- dimension + generated structure ID + deterministic structure anchor;
- source class and faction ID;
- bound Source Core position;
- `INTACT | DAMAGED | CLEARED` state;
- remaining production budget;
- launch strength/cooldown/speed;
- next production time and launch serial;
- transaction generation counter;
- clear time/cause/actor metadata.

Schema-3 worlds migrate with an empty source registry; future source/world schemas fail closed.

### Stable generated-geography identity

`SourceDescriptor` derives its stable UUID from:

```text
drewcraft-source-v1 | dimension | structureId | anchorX | anchorY | anchorZ
```

The physical Source Core is deliberately not the authority. Rediscovery is idempotent, a cleared source cannot be rediscovered back to life, conflicting immutable rediscovery fails closed, and two source identities may not bind the same core position.

`GeneratedSourceRegistration` is the narrow integration seam for DrewCraft-owned or third-party generated structures/templates. Structure integration supplies the exact generated descriptor; DrewCraft registers it and may place the core only when that core chunk is already loaded. It never searches or force-loads distant chunks.

### Physical Source Core

`drewcraft:source_core` is now a real registered block.

V1 safety behavior:

- no BlockItem is registered;
- piston reaction is `BLOCK`;
- successful player destruction invokes the authoritative clear transaction;
- actual explosion destruction invokes the same transaction;
- an unbound/copied core block is strategically inert;
- replacing a cleared core cannot reactivate its `SourceRecord`.

The current development model uses a placeholder vanilla texture; visual faction theming does not affect strategic authority.

### Permanent clearing transaction

Clearing is synchronized and idempotent.

On the first legitimate clear:

1. source state becomes `CLEARED`;
2. source generation increments;
3. clear metadata is recorded;
4. future production is disabled permanently under V1 rules;
5. world state is marked dirty;
6. the irreversible clear is immediately flushed through world `DimensionDataStorage` rather than waiting for ordinary autosave.

The admin clear command uses the same crash-durable persistence rule.

### Bounded source production

`SourceProductionScheduler` iterates persistent records only. It does not scan source chunks or keep them loaded.

Default work limits:

- production cycle every **200 ticks**;
- **16** source records inspected per cycle;
- **4** successful strategic launches per cycle;
- **1200-tick** backoff after bounded route failure.

The scheduler rotates its source cursor between cycles so a registry larger than the per-cycle inspection cap cannot permanently starve later source UUIDs.

A failed BP2 route consumes no source population.

### Clear-versus-launch race safety

The scheduler captures `source.generation`, performs bounded route planning, then attempts an atomic `commitSourceLaunch` using the captured generation.

Clearing increments the generation. Therefore:

- a group whose commit wins before clearing is a valid independent strategic population and survives;
- a route planned before clear but committed after clear is rejected;
- no new group can commit after `CLEARED` becomes authoritative.

This race is tested directly by clearing a source from inside the planner after generation capture and before commit.

### Real strategic-group production

BP4 launches real BP1/BP2 `StrategicGroup`s carrying their parent `sourceId`, persisted route, composition, strength, and normal BP3 materialization compatibility.

The BP4 content profile is intentionally minimal: deterministic routed zombie `PATROL` groups prove the source→group transaction. **BP5**, not BP4, owns data-driven factions, multiple hostile compositions, patrol/horde/raid/army/reinforcement roles, richer objective selection, and large-army semantics.

### Admin/debug surface

```text
/drewcraft source create-test
/drewcraft source list
/drewcraft source inspect <sourceId>
/drewcraft source clear <sourceId>
/drewcraft source perf
```

Inspection exposes source identity/state/core, budget/cooldown/generation/launch count, clear metadata, and existing strategic groups from that source. Performance diagnostics expose scheduler work, route failures, rejected race commits, fairness cursor, and CPU time.

## BP4 acceptance evidence

Focused automated tests cover:

- stable deterministic source identity;
- idempotent rediscovery;
- conflicting rediscovery fails closed;
- duplicate core binding fails closed;
- SourceRecord NBT round trip;
- future SourceRecord schema rejection;
- schema-3 → schema-4 world migration;
- idempotent permanent clear;
- cleared state survives save/reload;
- rediscovery cannot reactivate a cleared source;
- global source-launch cap;
- fair bounded scheduler rotation;
- failed route consumes no population and backs off;
- clear-during-planning invalidates the stale launch commit;
- group committed before clearing survives clearing;
- that committed group survives save/restart with its source identity;
- cleared source still refuses a new launch after restart.

### CI

- final BP4 code/test head: **`188fff9583d917aeb44fd8802987f0b51604b178`**
- DrewCraft mod CI: **run `34728862438` — SUCCESS**
- job: `build-and-test` — **SUCCESS**
- command: `gradle -p mods/drewcraft test build --stacktrace --no-daemon`
- earlier focused persistence run `34728805083` and source-schema run `34728787877` also passed.

## Important production-world boundary

BP4 completes source identity, discovery, production, clearing, race safety, persistence, physical core behavior, and the structure-registration API.

The final production-world/pregeneration track must still select the concrete DrewCraft/third-party structure templates that act as camps/forts/cities/etc., assign deterministic Source Core anchors to those templates, and call `GeneratedSourceRegistration` as those structures are generated/indexed. This is deliberately a world-build integration task rather than a recurring live server scan.

Later representative/full-stack acceptance will visually prove Source Core placement and destruction in those final structures and backup/restore of their cleared states.

## Next: BP5

On the next **"go"**, continue until BP5 is reached.

BP5 expands the now-proven generic source/group pipeline into the V1 hostile population system:

1. data-driven faction and group templates;
2. patrol, horde/warband, raid, army, and reinforcement roles;
3. multiple meaningful hostile compositions;
4. bounded large-army wave materialization using BP3;
5. non-omniscient/explainable target knowledge;
6. persistent mission/casualty state through unload/restart;
7. representative large-army proof without loading every represented unit.

Stop and report again when BP5 passes. Do not begin BP6 siege planning until the user says **"go"** after that report.
