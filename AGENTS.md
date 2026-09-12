# AGENTS.md — DrewCraft / ServerMc

This repository is the canonical source for the **DrewCraft** Minecraft server experience. `ServerMc` is the repository/internal project name; DrewCraft is the friend-facing product/server name.

Before making architectural or implementation changes, read:

1. `docs/v_1_requirements.md` — the hard V1 product/release contract
2. `docs/v_1_development_tree.md` — the canonical dependency-ordered execution checklist from current state to V1
3. `docs/STRATEGIC_WORLD_MODEL.md` — canonical hostile-source, roaming-force, unloaded-movement, source-core, and wild-herd behavior contract
4. `docs/MOB_STRUCTURE_CANDIDATES.md` — researched tactical-AI, herd-AI, structure-source, and structure-density candidates; evaluation only, not the production lock
5. `docs/UPSTREAM_DEPENDENCIES.md` — upstream ownership, source access, candidate-version, redistribution, and fork policy
6. `pack/manifest/upstreams.yaml` — machine-readable upstream/candidate registry; candidates are not production locks
7. `docs/PROJECT_SPEC.md`
8. `docs/SYSTEMS.md`
9. `docs/MOD_STACK.md`
10. `docs/REPO_ARCHITECTURE.md`
11. `docs/LAUNCHER_HOSTING.md`
12. `docs/ROADMAP.md` — older/high-level roadmap; where it conflicts with the V1 requirements or development tree, the V1 documents above win

## Non-negotiable design principles

- Minecraft target is 1.21.1 / NeoForge / Java 21 until an explicit migration decision is made.
- DrewCraft V1 is **feature-complete and integration-complete, not balance-complete**. Broad recipe, economy, fuel-cost, spawn-frequency, and difficulty tuning belongs in V1.1+ unless an upstream default clearly destroys a core design pillar.
- Geography must matter. Do not introduce routine teleportation or systems that make roads, rail, ships, aircraft, or weather irrelevant.
- Create is the primary infrastructure/technology language. Avoid redundant giant tech trees.
- Project Atmosphere is the atmospheric source of truth; bridge it rather than building another weather simulation.
- Strategic mobs outside loaded chunks are persistent lightweight records, not permanently loaded entities.
- Important hostile groups must exist at real strategic positions while unloaded; do not implement attacks as timed spawn events around players.
- Players may encounter patrols/hordes/armies by chance because their routes intersect during exploration.
- Hostile camps/forts/towns/cities are real persistent strategic sources tied to generated structures.
- Every hostile strategic source has an explicit DrewCraft source-core objective or equivalent stable source controller.
- Destroying/clearing a source core permanently marks that source cleared and prevents it from launching new strategic forces across unload/restart/backup restore.
- Clearing a source does not magically despawn already-deployed groups; they remain persistent world populations unless their strategic behavior later causes retreat/merge/destruction.
- Source state is independent of ordinary mob spawner blocks.
- Wild animal populations may be persistent strategic herds; materialized herds should spawn/behave as coherent groups rather than unrelated singleton events.
- Player-owned/domesticated/penned animals must not be silently absorbed into roaming wild-herd state.
- Normal local Minecraft spawning/farms remain available; strategic spawning is additive.
- Existing mob/herd AI mods may be reused for **loaded tactical behavior only** when they pass compatibility gates. DrewCraft remains authoritative for source identity, strategic movement, materialization, casualties, and herd persistence.
- Siege mobs path normally first and breach only when needed.
- Siege block damage must be constrained to meaningful breach corridors; never implement indiscriminate nearest-block griefing, even if an upstream horde mod supports generic block breaking.
- Structure mods are content suppliers, not strategic-state authorities. Only whitelisted structure IDs become strategic sources.
- Structure density must stay sparse enough that Terrain Diffusion World Scale 2 still feels genuinely large; prefer explicit structure-set configuration/whitelists to indiscriminate structure-pack stacking.
- Radar is physical infrastructure with power/data connectivity and physical displays.
- Radar antenna height/terrain obstruction should matter.
- Friends must not manually manage Java, NeoForge, or mod folders.
- Client and server releases come from one locked manifest and must not drift.
- Do not commit the full generated world, third-party jars by default, Java runtimes, model weights, credentials, backups, or large caches to Git.
- Do not add automatic cloud autoscaling that can silently create charges.

## Development order

`docs/v_1_development_tree.md` is the canonical implementation order and checklist. Work from the earliest unmet dependency/gate rather than jumping to the most interesting feature.

In particular:

- prove reproducible pack generation first;
- perform the upstream ownership/source audit in `docs/UPSTREAM_DEPENDENCIES.md` and `pack/manifest/upstreams.yaml` as part of the reproducible-pack stage;
- use `docs/MOB_STRUCTURE_CANDIDATES.md` only to select compatibility spikes; do not promote candidates by documentation alone;
- lock and test the complete baseline mod stack second;
- prove the production world pipeline and real host constraints before advanced custom systems;
- establish release/client/server artifact contracts before depending on them;
- build the DrewCraft integration-mod platform and adapters before feature-specific bridges;
- prove one thin vertical slice before adding content breadth;
- prove persistence/materialization correctness before scaling to armies;
- implement/source-index hostile structures only after the strategic kernel/materialization semantics are stable;
- perform full cross-system, failure/restart, restore, and performance tests before V1.

Do **not** start substantial radar, army, siege, or balance work while an earlier hard gate in the V1 development tree is still failing.

## Strategic world contract

`docs/STRATEGIC_WORLD_MODEL.md` is the detailed player-facing behavioral contract. In particular:

- strategic sources are indexed from real generated structures and have stable IDs;
- the DrewCraft Source Core is the V1 clearing objective;
- legitimate core destruction atomically persists `CLEARED` state before the source may launch another force;
- replacing the physical core block does not reactivate a source;
- sources launch real strategic groups from their real geographic location;
- groups advance using coarse unloaded simulation with routes/ETAs rather than teleportation;
- patrols and roaming hordes need not target a player at all;
- player-targeting forces should gain target knowledge through explicit, explainable rules rather than omniscience;
- materialization is transactional/idempotent and casualties survive unload/restart;
- wild herds reuse the same strategic-kernel philosophy and materialize as groups;
- tactical mob/herd AI is replaceable compatibility infrastructure, not the persistence authority.

## Upstream dependency and fork policy

The upstream registry is part of Stage 1 of the V1 development tree.

- Track the official source repository for every third-party dependency even when DrewCraft consumes the official binary.
- `pack/manifest/upstreams.yaml` contains discovered/test candidates; it is not the authoritative production lock until compatibility testing and SHA-256 verification promote an artifact.
- Do not fork or vendor an upstream project merely to simplify packaging. The manifest/resolver is responsible for packaging.
- Prefer upstream binaries plus a DrewCraft compatibility adapter.
- Create a DrewCraft fork only when a required V1 integration or blocking bug genuinely needs maintained source changes **and** the upstream license permits the intended modification/distribution model.
- If a fork is created, record the upstream base ref, fork URL, exact DrewCraft commit, build procedure, license notes, and resulting artifact hash in the upstream registry.
- Keep fork patch sets minimal and upstream generally useful fixes when practical.
- Source visibility is not redistribution permission. Respect provider/license restrictions, especially for All Rights Reserved projects.
- Never silently replace a provider artifact with a locally modified build under the same version identity.

## Custom mod architecture

Prefer one NeoForge integration mod with internal modules/adapters rather than many tiny mutually dependent custom mods.

Keep third-party integrations behind explicit adapters so upstream changes are localized.

Every major custom subsystem should have:

- a server-side feature flag
- versioned persistence where applicable
- admin/debug observability
- bounded performance behavior
- tests for restart/unload edge cases

## Performance assumptions

The initial production target is constrained. Therefore:

- no global per-tick scans
- no distant entity ticking
- no full-resolution unloaded-chunk entity pathfinding
- use coarse elapsed-time strategic simulation
- cache radar products and terrain masks
- cap expensive siege planners
- make performance limits configurable

## Release discipline

Do not update a dependency merely because a newer version exists.

A dependency change is complete only after the generated client/server pack boots, connects, loads the existing world where relevant, and the affected integration has been tested.

World-generation changes require special caution because new terrain may differ permanently from existing terrain.

Do not call a V1 feature complete because it worked once in a development world. Completion requires the relevant gate in `docs/v_1_development_tree.md`, including restart/unload/performance testing where specified.

## User experience

The public-facing name is **DrewCraft**.

The download site should remain deliberately simple: Windows and Mac install buttons. Complexity belongs in the launcher, not in setup instructions for friends.
