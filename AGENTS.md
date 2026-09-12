# AGENTS.md — DrewCraft / ServerMc

This repository is the canonical source for the **DrewCraft** Minecraft server experience. `ServerMc` is the repository/internal project name; DrewCraft is the friend-facing product/server name.

Before making architectural or implementation changes, read:

1. `docs/v_1_requirements.md` — the hard V1 product/release contract
2. `docs/v_1_development_tree.md` — the canonical dependency-ordered execution checklist from current state to V1
3. `docs/STRATEGIC_WORLD_MODEL.md` — canonical hostile-source, roaming-force, unloaded-movement, source-core, and wild-herd behavior contract
4. `docs/SOURCE_CORE_SPEC.md` — exact V1 hostile-source core destruction, persistence, replacement, race-safety, and already-deployed-force semantics
5. `docs/MOB_STRUCTURE_CANDIDATES.md` — tactical-AI, herd-AI, structure-source, and structure-density compatibility candidates
6. `docs/PERFORMANCE_STACK.md` — canonical performance/optimization architecture and compatibility matrix
7. `docs/UPSTREAM_DEPENDENCIES.md` — upstream ownership, source access, candidate-version, redistribution, and fork policy
8. `pack/manifest/README.md` — how all candidate registries merge and promote into exact locks
9. `pack/manifest/upstreams.yaml` — foundational upstream candidates
10. `pack/manifest/performance_candidates.yaml` — performance baseline and aggressive optimization spikes
11. `pack/manifest/mob_structure_candidates.yaml` — mob/herd/structure compatibility-spike candidates
12. `docs/PROJECT_SPEC.md`
13. `docs/SYSTEMS.md`
14. `docs/MOD_STACK.md`
15. `docs/REPO_ARCHITECTURE.md`
16. `docs/LAUNCHER_HOSTING.md`
17. `docs/ROADMAP.md` — older/high-level roadmap; where it conflicts with the V1 requirements or development tree, the V1 documents above win

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
- Every hostile strategic source has an explicit DrewCraft Source Core objective or equivalent stable source controller.
- **The Source Core block is only the physical player-facing objective; the persistent `SourceRecord` is authoritative.**
- Destroying a bound Source Core by a valid break/explosion event permanently marks that source `CLEARED`, and the cleared state survives unload/restart/backup restore.
- Replacing, moving, duplicating, Silk-Touching, or otherwise reacquiring the physical core must never reactivate or duplicate strategic authority.
- Source clearing must be race-safe against source launch scheduling: groups committed before clearing survive; no new group may commit after `CLEARED` becomes authoritative.
- Clearing a source does not magically despawn already-deployed groups; they remain persistent world populations unless their strategic behavior later causes retreat/merge/destruction.
- Source state is independent of ordinary mob spawner blocks.
- Wild animal populations may be persistent strategic herds; materialized herds should spawn/behave as coherent groups rather than unrelated singleton events.
- Player-owned/domesticated/penned animals must not be silently absorbed into roaming wild-herd state.
- Normal local Minecraft spawning/farms remain available; strategic spawning is additive.
- Existing mob/herd AI mods may be reused for **loaded tactical behavior only** when they pass compatibility gates. DrewCraft remains authoritative for source identity, strategic movement, materialization, casualties, and herd persistence.
- Enhanced Hordes + Enhanced Hordes Tweaks and Zombie Hordes are **alternative tactical spikes**, not mods to stack blindly.
- Ethological and Herd Instinct are herd-AI candidates; neither may become a second unloaded population simulator.
- Towns and Towers plus a selective When Dungeons Arise whitelist is the first hostile-source structure spike; CTOV is initially an alternative to Towns and Towers, not an automatic companion.
- Siege mobs path normally first and breach only when needed.
- Siege block damage must be constrained to meaningful breach corridors; never implement indiscriminate nearest-block griefing, even if an upstream horde mod supports generic block breaking.
- Structure mods are content suppliers, not strategic-state authorities. Only whitelisted structure IDs become strategic sources.
- Structure density must stay sparse enough that Terrain Diffusion World Scale 2 still feels genuinely large; prefer explicit structure-set configuration/whitelists to indiscriminate structure-pack stacking.
- The performance stack owns **performance only**, never gameplay state or simulation semantics.
- Baseline performance candidates are tested as part of the Stage 2 full-stack lock; do not treat them as optional cosmetic QoL additions.
- Start optimization mods with semantics-preserving settings. Dynamic entity activation, mobcap changes, AI freezing, asynchronous worldgen and similar behavior-changing optimizations require separate evidence before enabling.
- C2ME is an isolated world-build compatibility spike until Terrain Diffusion/structure output, restart safety, and corruption tests pass; do not silently add it to production.
- Client culling must be tested/whitelisted for Create, MTS and DrewCraft block entities whose render bounds exceed normal bounds.
- Every optimizer retained in the production lock needs either measurable benefit or a concrete reliability benefit worth its maintenance/conflict surface.
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
- Stage 1 resolver work must read `upstreams.yaml`, `performance_candidates.yaml`, and `mob_structure_candidates.yaml`, resolve transitives, classify sides, acquire legal artifacts and compute exact hashes;
- perform the upstream ownership/source audit in `docs/UPSTREAM_DEPENDENCIES.md` as part of the reproducible-pack stage;
- use `docs/MOB_STRUCTURE_CANDIDATES.md` only to select controlled compatibility spikes; do not promote candidates by documentation alone;
- use `docs/PERFORMANCE_STACK.md` to extend the Stage 2 technical baseline with the intended optimization suite;
- lock and test the complete foundational + performance baseline before optional structures, ship mods or tactical-AI branches are promoted;
- run Enhanced Hordes/Tweaks versus Zombie Hordes as separate hostile-AI profiles;
- run Ethological versus the narrower Herd Instinct path as separate herd-AI profiles;
- run the first structure-source profile with vanilla control + Towns and Towers + a tiny WDA whitelist, with CTOV held as an alternative;
- run C2ME only as a separate world-build experiment against the same seed/config and compare correctness as well as speed;
- prove the production world pipeline and real host constraints before advanced custom systems;
- establish release/client/server artifact contracts before depending on them;
- build the DrewCraft integration-mod platform and adapters before feature-specific bridges;
- prove one thin vertical slice before adding content breadth;
- prove persistence/materialization correctness before scaling to armies;
- implement/source-index hostile structures only after the strategic kernel/materialization semantics are stable;
- implement Source Core clearing exactly according to `docs/SOURCE_CORE_SPEC.md`, including idempotency, persistence, replacement safety, and launch/clear race tests;
- perform full cross-system, failure/restart, restore, profiling and performance tests before V1.

Do **not** start substantial radar, army, siege, or balance work while an earlier hard gate in the V1 development tree is still failing.

## Candidate-manifest architecture

`pack/manifest/README.md` defines the promotion flow.

- `upstreams.yaml` contains foundational platform/gameplay candidates.
- `performance_candidates.yaml` contains the intended Stage 2 performance suite plus isolated aggressive experiments.
- `mob_structure_candidates.yaml` contains mutually exclusive or subsystem-specific gameplay/content spikes.
- The future `mods.yaml` / `content-packs.yaml` contain only exact promoted choices with hashes.

A candidate appearing in a registry does **not** mean it belongs in every generated profile.

## Strategic world contract

`docs/STRATEGIC_WORLD_MODEL.md` is the detailed player-facing behavioral contract. `docs/SOURCE_CORE_SPEC.md` is authoritative for the exact source-core clearing implementation contract.

In particular:

- strategic sources are indexed from real generated structures and have stable IDs;
- the DrewCraft Source Core is the V1 clearing objective;
- the core block itself is not the source state;
- legitimate core destruction atomically persists `CLEARED` state before the source may launch another force;
- replacing the physical core block does not reactivate a source;
- core duplication/movement must not create, move, or duplicate source authority;
- groups already committed before clearing remain valid persistent groups;
- no group may be newly committed after clearing becomes authoritative;
- sources launch real strategic groups from their real geographic location;
- groups advance using coarse unloaded simulation with routes/ETAs rather than teleportation;
- patrols and roaming hordes need not target a player at all;
- player-targeting forces should gain target knowledge through explicit, explainable rules rather than omniscience;
- materialization is transactional/idempotent and casualties survive unload/restart;
- wild herds reuse the same strategic-kernel philosophy and materialize as groups;
- tactical mob/herd AI is replaceable compatibility infrastructure, not the persistence authority.

## Performance contract

`docs/PERFORMANCE_STACK.md` defines the optimization architecture.

The intended baseline compatibility suite includes ModernFix, FerriteCore, Lithium, ServerCore, ScalableLux, Chunk Sending, AllTheLeaks, the FastSuite/FastWorkbench/FastFurnace family, Clumps, Connectivity, spark, Embeddium, ImmediatelyFast, Entity Culling, MoreCulling, and their required libraries where applicable.

Rules:

- offline pregeneration remains the primary defense against live Terrain Diffusion + giant-structure worldgen cost;
- measure p50/p95/p99 MSPT, memory/GC and representative client frame performance rather than relying on mod marketing;
- inspect mixin/lighting/network/render conflicts after every baseline change;
- generic AI/entity-freezing optimizers are not a substitute for DrewCraft's strategic record/materialization architecture;
- a large strategic army is bounded as active entities/waves rather than kept permanently ticked;
- spark is required development/diagnostic tooling even though it does not itself make the server faster.

## Upstream dependency and fork policy

The upstream registries are part of Stage 1 of the V1 development tree.

- Track the official source repository for every third-party dependency even when DrewCraft consumes the official binary.
- Candidate registries are not authoritative production locks until compatibility testing and SHA-256 verification promote an artifact.
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
- pregenerate expensive production terrain/structures offline
- profile before introducing additional optimization dependencies

## Release discipline

Do not update a dependency merely because a newer version exists.

A dependency change is complete only after the generated client/server pack boots, connects, loads the existing world where relevant, and the affected integration has been tested.

World-generation changes require special caution because new terrain may differ permanently from existing terrain.

Do not call a V1 feature complete because it worked once in a development world. Completion requires the relevant gate in `docs/v_1_development_tree.md`, including restart/unload/performance testing where specified.

## User experience

The public-facing name is **DrewCraft**.

The download site should remain deliberately simple: Windows and Mac install buttons. Complexity belongs in the launcher, not in setup instructions for friends.
