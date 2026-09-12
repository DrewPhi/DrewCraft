# DrewCraft

DrewCraft is a deliberately integrated Minecraft survival server built around **geographic scale, infrastructure, weather, transportation, and a living strategic world**.

The GitHub repository is still named `ServerMc` until a manual repository rename is performed; **DrewCraft** is the player-facing product/server name.

This is not a kitchen-sink modpack. Every major subsystem has one authoritative owner, and new mods are rejected when they merely duplicate an existing system.

## Current status

The project is moving from specification into **Stage 1: reproducible pack foundation**.

Already established:

- V1 product requirements
- dependency-ordered development tree
- subsystem architecture
- anti-redundancy/mod ownership policy
- upstream source/dependency registry
- canonical strategic-world/source-core/herd behavior contract
- researched tactical-AI, herd-AI and strategic-source structure candidates
- launcher/server deployment architecture
- simple DrewCraft download-site HTML

Next implementation milestone:

> resolve the registered upstream candidates into exact verified artifacts, compute hashes, generate reproducible client/server development packs, and run the full compatibility lock.

Target platform:

- Minecraft **1.21.1**
- **NeoForge**
- **Java 21**
- Windows x86-64 clients
- Apple Silicon macOS as a hard V1 client target
- Linux server; Oracle Ampere A1 is the first low-cost benchmark target, not a V1 requirement

## V1 scope

DrewCraft V1 is **feature-complete and integration-complete, not balance-complete**.

V1 requires the intended systems and bridges to exist and work together reliably. Broad recipe, fuel-price, progression, spawn-frequency, radar-tier and difficulty tuning belongs to V1.1+ unless an upstream default clearly destroys a core design pillar.

## System ownership: no redundant mods

| System | Owner |
| --- | --- |
| Overworld generation, terrain/climate fields, tall-world caves | Terrain Diffusion Plus |
| Offline world pregeneration | Chunky |
| Distant terrain LOD | Distant Horizons |
| Industry, logistics and rail | Create |
| Road vehicles and aircraft | Immersive Vehicles / MTS + minimal curated content |
| Atmospheric/weather simulation | Project Atmosphere |
| Cloud/localized-weather rendering substrate | Simple Clouds under Atmosphere integration |
| Season calendar/gameplay hooks | Serene Seasons where required/stable |
| Radar, aviation bridges, strategic populations, armies, herds and sieges | DrewCraft custom NeoForge integration mod |
| Ordinary local spawning/farms | Minecraft/upstream local rules; strategic simulation is additive |

Consequences:

- no second cave/terrain overhaul by default;
- no second giant tech/electrical tree merely to power radar;
- no parallel train progression competing with Create;
- no second weather simulator;
- no generic macro horde/army mod competing with DrewCraft strategic state;
- no generic random mob block-breaking system;
- no Waystones/routine teleportation;
- no giant structure pack unless a narrow, measured need is demonstrated.

See [`docs/MOD_STACK.md`](docs/MOD_STACK.md) for the detailed ownership matrix.

## Geography

Terrain Diffusion Plus at **World Scale 2** is the overworld foundation. The production world is bounded and pregenerated offline with Chunky so the live server does not depend on expensive neural terrain generation during normal play.

Distant Horizons communicates that scale visually.

The world should preserve meaningful empty geography. Structure content is sparse and purposeful, with selected hostile structures able to become persistent strategic sources.

## Transportation

The long-term intended progression is roughly:

**walking / horses / vanilla boats -> roads and cars -> Create rail -> large ships if a stable solution exists -> aircraft**

For V1, these systems must function and interoperate; they do not yet need perfectly tuned costs/economics.

- **Create** owns trains and industrial infrastructure.
- **MTS** supplies cars/trucks and aircraft through the smallest useful curated content set.
- A large player-buildable ship mod is desirable but not a V1 blocker.
- If vanilla Nether 8:1 travel obviously destroys the geography/transport premise, V1 may use a coarse pillar-preserving portal rule rather than waiting for the later balance pass.

## Weather and aviation

**Project Atmosphere is the atmospheric source of truth.**

Simple Clouds is used as the cloud/local-weather visual substrate integrated with Atmosphere, not as a competing weather simulation. The current Project Atmosphere 1.21.1 release requires Serene Seasons and Gabou's Libs and lists Simple Clouds as optional; DrewCraft intentionally evaluates Simple Clouds because distant visible cloud/weather systems are central to the design.

DrewCraft bridges the real atmospheric state into supported aircraft:

- crosswind
- headwind/tailwind effects
- bounded turbulence
- storm severity
- terrain/mountain contribution
- reduced visibility

The custom mod should consume Project Atmosphere rather than invent another weather model.

## Physical radar

Radar is infrastructure, not a minimap cheat.

A ground site requires real world blocks such as:

- dish/antenna
- controller
- Create-powered adapter
- data/power connectivity
- physical display

Antenna height and coarse terrain masking affect useful coverage. Multiple displays share a cached controller scan.

Aircraft weather radar uses the same atmospheric data pipeline.

## Persistent strategic world

The world continues to exist outside loaded chunks through compact server-side records rather than permanently loaded mobs.

DrewCraft tracks:

- real hostile source structures such as camps, forts, ruins, towns and cities
- patrols, roaming hordes/warbands, raids, reinforcements and armies
- multiple hostile compositions/factions
- strategic movement and ETA across unloaded geography
- casualties across materialization/unload/restart
- persistent cleared-source state
- strategic wild animal herds

A hostile group is not created just because a player is nearby. It can already be moving through the world while unloaded. A player exploring can accidentally intersect its route and encounter it where it really is.

When players approach a strategic group, it materializes into ordinary entities. When safely distant again, survivors can be summarized back into persistent strategic state.

No teleporting/resetting armies.

### Hostile source cores

Every strategic hostile source has one explicit DrewCraft **Source Core** objective (the visible theme can vary: command table, war banner/controller, corrupted heart, fortress core, etc.).

While the source is active it can launch new strategic groups from its real geographic location.

If players destroy the bound Source Core — including deliberately blowing it up when an explosion actually destroys the core — DrewCraft atomically marks that source **CLEARED** in persistent state. That source then launches **no new patrols, hordes, reinforcements or armies**, even after chunk unload, server restart or backup restore.

Replacing the physical block does not reactivate the source. Already-deployed forces do not magically disappear; they remain real populations already out in the world.

See [`docs/STRATEGIC_WORLD_MODEL.md`](docs/STRATEGIC_WORLD_MODEL.md) for the full contract.

### Wild animal herds

Important wild animals should exist as persistent herds rather than only as unrelated singleton spawns.

A herd can move coarsely while unloaded, materialize as a coherent group when a player approaches, exhibit group/panic behavior while loaded, and collapse back to a strategic record after the player leaves. Hunting reduces persistent herd count; animals deliberately domesticated/claimed by players leave wild-herd accounting.

Player-owned, named, leashed, bred or penned livestock must not be silently absorbed into a roaming herd.

Existing 1.21.1 NeoForge herd-AI mods are being evaluated only for **loaded behavior**; DrewCraft remains the unloaded herd-state authority.

## Tactical mob and structure reuse

DrewCraft should reuse upstream code/content where it fits without surrendering strategic ownership.

Current compatibility-spike research includes:

- Enhanced Hordes + Enhanced Hordes Tweaks versus Zombie Hordes for loaded hostile cooperation/wandering/stacking behavior;
- Ethological! versus the narrower Herd Instinct for loaded passive-herd behavior;
- When Dungeons Arise as a strong source of selectively enabled hostile camps/forts/palaces;
- Towns and Towers as a grounded source of pillager-outpost variants;
- CTOV as a Towns-and-Towers alternative rather than an automatic additional settlement overhaul;
- pack-owned structure spacing/whitelists first, with Sparse Structures only as a compatibility-spike option if global density control is useful.

See [`docs/MOB_STRUCTURE_CANDIDATES.md`](docs/MOB_STRUCTURE_CANDIDATES.md) and [`pack/manifest/mob_structure_candidates.yaml`](pack/manifest/mob_structure_candidates.yaml).

## Sieges

Siege behavior is path-first:

1. use viable roads, bridges, gates, doors and terrain;
2. breach only when a reasonable path does not exist;
3. only siege-capable units can meaningfully breach;
4. breach blocks are selected because they open a useful corridor;
5. off-route decorative builds are not arbitrary targets.

The goal is for castle design to matter without making decorative building unsafe.

## Normal Minecraft still matters

Strategic simulation is additive.

DrewCraft preserves:

- caves
- night danger
- ordinary local spawning
- mob farms
- ordinary spawners
- mining/building/redstone
- Create contraptions
- normal exploration

Clearing a strategic hostile source is independent from preserving an ordinary mob spawner for a farm.

## One-click friend experience

Friends should not manually manage Java, NeoForge, Prism, mods or configs.

The intended flow is:

1. visit the DrewCraft page;
2. click **Windows** or **Mac**;
3. run the DrewCraft bootstrapper;
4. authenticate normally through Prism/Microsoft once;
5. thereafter launch/update through DrewCraft.

The launcher manages Java 21, Prism, the exact pack, hashes, updates and server-version readiness.

## Upstream/source strategy

DrewCraft tracks the official source repository and artifact provider for every important dependency in [`pack/manifest/upstreams.yaml`](pack/manifest/upstreams.yaml).

We **do not fork every mod** merely to package it. Normal upstream releases remain upstream dependencies. A DrewCraft fork is created only when a required V1 integration/bug fix genuinely needs a source patch that cannot live cleanly in the DrewCraft integration mod.

See [`docs/UPSTREAM_DEPENDENCIES.md`](docs/UPSTREAM_DEPENDENCIES.md).

## Repository direction

The planned monorepo owns the reproducible game experience:

```text
ServerMc/ (eventually DrewCraft/ if renamed)
├── README.md
├── AGENTS.md
├── docs/
├── pack/
│   ├── manifest/
│   ├── common/
│   ├── client/
│   ├── server/
│   └── overrides/
├── mods/
│   └── drewcraft/
├── launcher/
├── server/
├── infra/
├── world/
├── tools/
├── tests/
└── .github/workflows/
```

Third-party binaries, huge generated worlds, Java runtimes, model assets, backups and caches are not committed to Git by default. Releases are generated from manifests and verified artifacts.

## Canonical documentation order

1. [`docs/v_1_requirements.md`](docs/v_1_requirements.md) — hard V1 product/release contract
2. [`docs/v_1_development_tree.md`](docs/v_1_development_tree.md) — canonical dependency-ordered execution checklist
3. [`docs/STRATEGIC_WORLD_MODEL.md`](docs/STRATEGIC_WORLD_MODEL.md) — persistent sources, source cores, roaming forces and wild-herd behavior contract
4. [`docs/MOB_STRUCTURE_CANDIDATES.md`](docs/MOB_STRUCTURE_CANDIDATES.md) — current AI/herd/structure compatibility-spike research
5. [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md) — product/gameplay architecture
6. [`docs/MOD_STACK.md`](docs/MOD_STACK.md) — mod ownership and anti-redundancy policy
7. [`docs/UPSTREAM_DEPENDENCIES.md`](docs/UPSTREAM_DEPENDENCIES.md) — source/fork policy
8. [`docs/SYSTEMS.md`](docs/SYSTEMS.md) — custom systems design
9. [`docs/REPO_ARCHITECTURE.md`](docs/REPO_ARCHITECTURE.md) — repository/artifact boundaries
10. [`docs/LAUNCHER_HOSTING.md`](docs/LAUNCHER_HOSTING.md) — launcher/server/deployment architecture
11. [`docs/ROADMAP.md`](docs/ROADMAP.md) — high-level roadmap; the V1 development tree is more authoritative

## Definition of V1 success

One release candidate must demonstrate the whole intended system together:

- clean one-click Windows and Apple Silicon installation/update
- reliable huge pregenerated Terrain Diffusion world
- Distant Horizons
- functional road vehicles, Create trains and aircraft
- real weather affecting flight
- physical ground radar and aircraft weather radar
- persistent hostile sources and unloaded strategic travel
- multiple hostile compositions and large armies
- chance encounters with strategic groups already moving through the world
- casualty-preserving materialization/dematerialization
- source-core destruction permanently preventing new forces from that source
- already-deployed forces surviving source destruction appropriately
- path-first constrained sieges
- persistent wild animal herds that materialize as coherent groups
- normal local spawning/farms/building intact
- reliable release updates, backups and restores

That is DrewCraft V1. Fine-grained balance comes after the complete game exists.
