# DrewCraft Pack Manifests

This directory is the machine-readable dependency source of truth for DrewCraft.

## Candidate registries

Stage 1 dependency discovery currently comes from **three companion registries**. The resolver must read them as one candidate namespace and reject duplicate/conflicting canonical IDs.

- `upstreams.yaml` — foundational gameplay/platform upstreams: Terrain Diffusion Plus, Chunky, Distant Horizons, Create, MTS, Project Atmosphere, Simple Clouds, seasons and their libraries.
- `performance_candidates.yaml` — intended performance baseline plus isolated optimization experiments. Baseline entries are meant to enter the Stage 2 compatibility stack, but remain candidates until hashes/tests promote them.
- `mob_structure_candidates.yaml` — controlled tactical hostile-AI, herd-AI, strategic-source structure, and structure-density compatibility spikes. Alternatives in this file are **not** additive by default.

All three files are discovery/evaluation registries, **not production lockfiles**.

## Future authoritative manifests

- `mods.yaml` — authoritative locked mod set produced after compatibility gates.
- `content-packs.yaml` — authoritative locked content-pack set produced after compatibility gates.
- `pack.yaml` — pack identity/platform/schema/version definition.
- `java.yaml` — managed Java runtime definitions for launcher/server packaging.

The eventual locked manifests contain only the exact promoted choices. For example, they must not contain both Enhanced Hordes and Zombie Hordes merely because both appeared in candidate research.

## Resolver requirements

The Stage 1 resolver/downloader must:

1. parse all candidate registries;
2. normalize canonical dependency IDs;
3. detect duplicate/conflicting candidates;
4. select the requested compatibility-spike profile;
5. recursively resolve required dependencies such as Placebo, Cupboard, Cristel Lib, Lithostitched, GlitchCore and Gabou's Libs;
6. acquire artifacts through permitted provider paths;
7. compute/verify SHA-256;
8. classify each artifact as `common`, `client`, `server`, or operational/world-build tooling;
9. generate deterministic client/server layouts;
10. fail closed on missing artifacts, hash drift, wrong-side files or unresolved transitives.

No friend or server administrator should manually download a hidden prerequisite.

## Compatibility profiles

The candidate registries imply explicit test profiles rather than one giant development `mods/` folder.

### Base + performance profile

The first full Stage 2 lock is:

```text
foundational upstream stack
+ intended baseline optimization suite
```

This establishes the pack/platform/performance baseline before optional structure or tactical-AI content is promoted.

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

The first intended structure experiment is:

```text
vanilla pillager outpost control
+ Towns and Towers
+ a tiny whitelist of When Dungeons Arise hostile structures
```

CTOV is initially an alternative to Towns and Towers, not an automatic companion. Pack-owned per-structure spacing is preferred over another global structure-density mod unless testing demonstrates a clear need.

### Aggressive performance spike

C2ME is tested separately against the same seed/world-build configuration. It is not part of the default baseline until Terrain Diffusion/structure-generation correctness is demonstrated.

## Promotion flow

```text
research/discover upstream
        ↓
candidate registry
        ↓
select explicit compatibility profile
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

Do not manually copy a jar into a release and treat it as locked.

Do not create a DrewCraft fork merely to simplify downloading or packaging. Forks are for maintained source changes; see `docs/UPSTREAM_DEPENDENCIES.md`.

The eventual resolver must fail closed if an acquired artifact does not match the locked SHA-256.
