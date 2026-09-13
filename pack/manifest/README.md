# DrewCraft Pack Manifests

This directory is the machine-readable dependency source of truth for DrewCraft.

## Candidate registries

Stage 1 dependency discovery currently comes from **five companion registries**. The resolver must read the runtime candidate registries as one candidate namespace and reject duplicate/conflicting canonical IDs. `endgame_content.yaml` also records world-build-only assets that are intentionally not runtime mods.

- `upstreams.yaml` — foundational gameplay/platform upstreams: Terrain Diffusion Plus, Chunky, Distant Horizons, Create, MTS, Project Atmosphere, Simple Clouds, seasons and their libraries.
- `performance_candidates.yaml` — intended performance baseline plus isolated optimization experiments. Baseline entries are meant to enter the Stage 2 compatibility stack, but remain candidates until hashes/tests promote them.
- `mob_structure_candidates.yaml` — controlled tactical hostile-AI, herd-AI, strategic-source structure, and structure-density compatibility spikes. Alternatives in this file are **not** additive by default.
- `create_combat_mobility_candidates.yaml` — selected V1 Create combat/physics-mobility stack: Create Big Cannons, CBC Firepower Components, Create: Gunsmithing, Create Aeronautics, Create: High Seas, and their explicitly tracked transitives.
- `endgame_content.yaml` — selected cult/endgame content foundations: Illager Invasion + Puzzles Lib for the cult tactical roster, the xSisyX Fantasy City & Terrain Builder schematic kit for the coherent cult architectural language, the eight derived source-site archetypes, Flightstone/Source Core/flak markers, and the hand-authored hidden capital. Raw third-party schematic/map binaries are not committed here by default.

These files are discovery/evaluation registries, **not production lockfiles**.

## Development profiles

`profiles.yaml` is the machine-readable selector that tells the resolver which candidate IDs belong together for a specific compatibility test.

It currently defines:

- `stage2_base_performance` — foundational stack + conservative optimization baseline;
- `stage2_create_combat_mobility` — selected firearms/artillery/Sable/Aeronautics/High Seas interaction stack;
- separate Enhanced Hordes/Tweaks and Zombie Hordes hostile-AI branches;
- separate Ethological and Herd Instinct herd-AI branches;
- the first Towns and Towers + selective WDA source-structure branch;
- the CTOV alternative branch;
- Sparse Structures as an optional density experiment;
- C2ME as an isolated world-build experiment;
- Structure Essentials as optional world-build/source-debug tooling.

The selected cult/endgame stack in `endgame_content.yaml` is currently separate from the certified baseline. When implementation starts, use an explicit endgame compatibility profile rather than silently changing the frozen baseline.

Profiles are development inputs, **not release locks**. Production releases contain exact promoted dependencies and hashes.

## Future authoritative manifests

- `mods.yaml` — authoritative locked mod set produced after compatibility gates.
- `content-packs.yaml` — authoritative locked content-pack set produced after compatibility gates.
- `pack.yaml` — pack identity/platform/schema/version definition.
- `java.yaml` — managed Java runtime definitions for launcher/server packaging.

The eventual locked manifests contain only the exact promoted choices. For example, they must not contain both Enhanced Hordes and Zombie Hordes merely because both appeared in candidate research.

## Resolver requirements

The Stage 1 resolver/downloader must:

1. parse runtime candidate registries and `profiles.yaml`;
2. normalize canonical dependency IDs;
3. detect duplicate/conflicting candidates;
4. select an explicit compatibility profile;
5. expand profile inheritance and reject incompatible profile combinations;
6. recursively resolve required dependencies such as Placebo, Cupboard, Cristel Lib, Lithostitched, GlitchCore, Gabou's Libs, Puzzles Lib, Sable, NTGL, playerAnimator, and Ritchie's Projectile Library when their parent candidates are selected;
7. acquire artifacts through permitted provider paths;
8. compute/verify SHA-256;
9. classify each artifact as `common`, `client`, `server`, or operational/world-build tooling;
10. generate deterministic client/server layouts;
11. fail closed on missing artifacts, hash drift, wrong-side files or unresolved transitives.

World-build-only asset kits such as the selected cult schematic pack are acquired through their recorded creator/provider path and processed separately from runtime jar resolution.

No friend or server administrator should manually download a hidden prerequisite.

## Compatibility profiles

### Base + performance profile

The first full Stage 2 lock is:

```text
foundational upstream stack
+ intended baseline optimization suite
```

This establishes the pack/platform/performance baseline before optional structure or tactical-AI content is promoted.

### Create combat + mobility profile

The selected V1 expansion is tested together as:

```text
Create Big Cannons
+ CBC: Firepower Components
+ Create: Gunsmithing
+ Create Aeronautics
+ Create: High Seas
+ Sable / NTGL / playerAnimator / Ritchie's Projectile Library
```

MTS remains the practical conventional car/truck/aircraft layer; Create Aeronautics supplies block-built physics vehicles and airships; High Seas supplies block-built ships. Static weapons are validated before moving-platform weapons, and armed ships/airships are only accepted after projectile-collision, persistence, restart and performance gates pass.

### Hostile tactical-AI spikes

Test independently:

```text
Enhanced Hordes + Enhanced Hordes Tweaks
```

versus

```text
Zombie Hordes
```

DrewCraft remains the strategic-state authority in either case.

### Herd-AI spikes

Test independently, with Ethological as the richer experimental branch and Herd Instinct as the narrower fallback. DrewCraft remains authoritative for unloaded herd persistence/materialization.

### Structure-source spike

The first intended V1 structure experiment is:

```text
vanilla pillager outpost control
+ Towns and Towers
+ a tiny whitelist of When Dungeons Arise hostile structures
```

CTOV is initially an alternative to Towns and Towers, not an automatic companion. Pack-owned per-structure spacing is preferred over another global structure-density mod unless testing demonstrates a clear need.

### Cult/endgame content stack

The selected cult campaign foundation is:

```text
Illager Invasion 1.21.1 NeoForge
+ Puzzles Lib
+ DrewCraft strategic spawning/lore/Source Core logic
+ xSisyX Fantasy City & Terrain Builder asset kit (world-build only)
```

Illager Invasion provides the cult tactical entity roster, but DrewCraft owns strategic spawning and progression. Its native structures are not the canonical cult architecture. The eight required cult sites and the hidden capital are derived from one palette-normalized asset kit and fitted to the pregenerated Terrain Diffusion production world.

### Aggressive performance spike

C2ME is tested separately against the same seed/world-build configuration. It is not part of the default baseline until Terrain Diffusion/structure-generation correctness is demonstrated.

## Promotion flow

```text
research/discover upstream
        ↓
candidate registry
        ↓
select profiles.yaml compatibility profile
        ↓
allowed-provider download
        ↓
SHA-256 + recursive dependency resolution
        ↓
Stage 2 / subsystem compatibility matrix
        ↓
performance + restart/unload evidence where relevant
        ↓
license/acquisition validation
        ↓
mods.yaml / content-packs.yaml lock
        ↓
client + server pack build
```

World-build-only schematics follow a parallel provenance/inventory/palette-conversion/site-validation pipeline before being baked into the production world.

Do not manually copy a jar into a release and treat it as locked.

Do not create a DrewCraft fork merely to simplify downloading or packaging. Forks are for maintained source changes; see `docs/UPSTREAM_DEPENDENCIES.md`.

The eventual resolver must fail closed if an acquired artifact does not match the locked SHA-256.
