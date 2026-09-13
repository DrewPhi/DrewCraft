# DrewCraft V1 Strategic Herds and Ecology Isolation

BP7 adds persistent wild herds without replacing or quota-managing ordinary Minecraft ecology.

## Core rule

> **Only explicitly registered DrewCraft herd records are strategic wildlife. Existing Minecraft animals are never scanned into, merged into, or absorbed by DrewCraft.**

This is intentionally stronger than trying to classify every nearby animal as wild versus owned.

Therefore all ordinary entities remain outside strategic ownership, including:

- naturally spawned animals;
- player-bred livestock;
- named animals;
- leashed animals;
- tamed/player-owned animals;
- animals kept in pens or farms;
- animals created by ordinary/modded spawners or other mods.

DrewCraft does not install a global natural-spawn cancellation hook, does not replace vanilla `NaturalSpawner`, does not rewrite spawn-placement rules, and does not modify ordinary spawner logic. Strategic entity caps count only entities explicitly materialized from DrewCraft strategic encounters.

## Herd identity

A V1 strategic herd is a normal `StrategicGroup` with:

- `groupType = HERD`;
- faction `drewcraft:wildlife`;
- deterministic UUID derived from dimension + species + migration origin + migration destination;
- species/count composition;
- `MIGRATION_ROUTE` target knowledge;
- persisted migration target and route;
- no hostile `SourceRecord` / Source Core dependency.

`WildHerdDescriptor` is the explicit world-build seed. `WildHerdRegistration` is idempotent and refuses to overwrite/reset an already-moving or casualty-bearing herd with the same stable identity.

Production-world tooling in BP8 will choose the actual wildlife species, counts, and migration corridors used in the pregenerated V1 world. Runtime does not discover herds by scanning distant chunks.

## Simulation and performance

Herds reuse BP1-BP3 unchanged:

1. while distant, the herd is one persisted record following a cached coarse route;
2. no chunks are loaded to move the herd;
3. no Minecraft entity AI exists for the distant herd;
4. near a player, BP3 creates one durable encounter;
5. at most the configured tactical cap is materialized (64 by default);
6. remaining herd strength stays abstract;
7. confirmed deaths decrement strategic strength exactly once;
8. after players leave, surviving tactical animals collapse back to the same herd record;
9. save/restart preserves route, population, casualties, and active encounter authority.

This means a herd of 200 animals can cross the strategic world without 200 continuously ticking entities.

## Local-spawn coexistence

Normal Minecraft ecology remains independent of strategic wildlife.

DrewCraft's `EntityJoinLevelEvent` handling is validation-only for entities that already carry DrewCraft strategic group/encounter tags. Untagged entities return immediately before any cancellation path.

DrewCraft does **not**:

- consume vanilla mob-cap slots through an abstract herd record;
- count ordinary entities against strategic encounter limits;
- cancel normal night/cave hostile spawning;
- disable or replace mob farms;
- disable vanilla or modded spawners;
- convert nearby livestock into strategic population when a herd unloads.

The BP7 architecture test deliberately fails if strategic code begins referencing global natural-spawn events, vanilla natural-spawner replacement, spawn-placement rewrites, or ordinary spawner internals.

## Admin diagnostics

```text
/drewcraft herd create-test <species> <count>
/drewcraft herd list
/drewcraft herd ecology
```

`create-test` explicitly seeds a 2,048-block migration from the admin's current position using the normal BP2 strategic route service. It is a diagnostic and does not imply production V1 herds originate from player positions.

## V1 boundaries

BP7 establishes herd identity, explicit registration, unloaded movement, bounded materialization, casualties, restart safety, and architectural coexistence with vanilla spawning.

Still deferred to later full-stack acceptance:

- final production-world species/count/corridor selection (BP8);
- visual observation of a large migrating herd in the final Terrain Diffusion world (BP9/BP10);
- balance tuning of herd density and migration frequency;
- optional richer animal capture/ownership interactions beyond the core rule that existing local animals are never absorbed.
