# DrewCraft Upstream Dependency Ownership and Fork Policy

This document is the operational companion to the candidate registries under `pack/manifest/`.

It answers two separate questions:

1. **Where does each third-party DrewCraft dependency come from, and which 1.21.1/NeoForge build are we currently evaluating?**
2. **When should DrewCraft fork an upstream project rather than consuming its normal release?**

The short rule is:

> **Track every upstream repository. Fork only when DrewCraft actually needs to maintain source changes.**

Forking everything would not make packaging more reproducible. The manifest/build system provides reproducible packaging. A fork creates an additional maintenance obligation and is therefore reserved for dependencies that DrewCraft must patch or maintain.

---

## Candidate registry architecture

Candidate research is split by purpose so the foundational registry does not become an unreadable kitchen-sink list:

- `pack/manifest/upstreams.yaml` — foundational gameplay/platform dependencies;
- `pack/manifest/performance_candidates.yaml` — intended optimization baseline plus isolated aggressive performance experiments;
- `pack/manifest/mob_structure_candidates.yaml` — tactical hostile-AI, herd-AI, source-structure and structure-density compatibility branches.

`pack/manifest/README.md` defines how the Stage 1 resolver merges these registries and how candidates are promoted.

**All three are candidate registries, not production locks.** The future `mods.yaml` / `content-packs.yaml` contain only exact promoted choices with hashes.

A candidate can be intentionally profile-specific. For example, Enhanced Hordes + Tweaks and Zombie Hordes are alternative test branches, and CTOV is initially an alternative to Towns and Towers rather than an automatic companion.

---

## Ownership classes

Every direct dependency that reaches a production lock is classified as one of:

- `UPSTREAM_BINARY` — consume an official artifact from CurseForge, Modrinth, GitHub Releases, or another approved upstream provider. We still record the source repository for debugging/API research.
- `UPSTREAM_SOURCE` — track/build a specific upstream source ref because no suitable immutable release artifact has yet been selected.
- `DREWCRAFT_FORK` — DrewCraft carries source modifications against an upstream project.
- `DREWCRAFT_OWNED` — DrewCraft owns the implementation, such as the custom integration mod.

`UPSTREAM_BINARY` should be the default for ordinary dependencies.

Candidate-only manifests may omit the ownership class until the candidate is serious enough to promote, but source/provider/license information should still be recorded as early as practical.

---

## Why upstream repos are not copied into the monorepo

The DrewCraft repo should remain the source of truth for **which upstream versions are used**, not become a duplicate of every upstream codebase.

Vendoring or submoduling every source tree would create several problems:

- every upstream release would require source-tree synchronization work;
- it would be easy to accidentally ship locally modified upstream code;
- licensing/redistribution becomes harder to reason about;
- clone/build size grows dramatically;
- source forks can drift silently from upstream;
- the same version would exist in both the DrewCraft manifest and an embedded source checkout.

Instead, DrewCraft records immutable provider/version/file IDs and eventually SHA-256 hashes. The build/launcher acquires the exact artifact from its permitted source and verifies it.

---

## Candidate registry vs production lock

A candidate appearing in any registry does not mean it is already approved for the pack. This matters because some current 1.21.1 releases are Beta/Alpha, some are mutually exclusive alternatives, and some are only world-build experiments.

Promotion flow:

1. discover a sensible 1.21.1/NeoForge candidate;
2. record official source repo, release provider, IDs, status, license, dependencies and intended profile;
3. acquire the candidate through a permitted upstream path;
4. compute SHA-256;
5. resolve transitive dependencies;
6. run the relevant DrewCraft compatibility matrix/profile;
7. test Windows and Apple Silicon where client-relevant;
8. benchmark performance when the candidate claims performance benefits;
9. verify release/redistribution policy;
10. promote the exact artifact into the authoritative locked mod/content-pack manifest.

This lets DrewCraft test newer or experimental builds without pretending they are already stable production dependencies.

---

## Current foundational candidate set — researched 2026-09-12

`pack/manifest/upstreams.yaml` currently tracks:

| Dependency | Official source | Candidate for MC 1.21.1 / NeoForge | Status | DrewCraft ownership |
| --- | --- | --- | --- | --- |
| Terrain Diffusion Plus | `derekvawdrey/terrain-diffusion-plus` | source ref `05fdcf5681cc53a9685325d714750b4427661a21` | source-head candidate | `UPSTREAM_SOURCE` |
| Chunky | `pop4959/Chunky` | `1.4.23`, CurseForge file `6383261` | Release | `UPSTREAM_BINARY` |
| Distant Horizons | official GitLab `distant-horizons-team/distant-horizons` | `3.2.0-b`, CurseForge file `8389148` | Beta | `UPSTREAM_BINARY` |
| Create | `Creators-of-Create/Create`, branch `mc1.21.1/dev` | `6.0.10`, CurseForge file `7963363` | Release | `UPSTREAM_BINARY` |
| Immersive Vehicles / MTS | `DonBruce64/MinecraftTransportSimulator` | `24.0.0`, CurseForge file `7926606` | Release | `UPSTREAM_BINARY` |
| MTS Official Content Pack | upstream content pack | `V29`, CurseForge file `7933734` | Release | `UPSTREAM_BINARY` |
| Project Atmosphere | `xGabou/Project-Atmosphere`, branch `NeoForge-1.21.1` | `0.9.1.2`, Modrinth version `QBPZU1Dp` | Release | `UPSTREAM_BINARY` |
| Simple Clouds | `nonamecrackers2/simple-clouds`, branch `1.21.1` | `0.7.3+1.21.1`, CurseForge file `6928979` | Beta | `UPSTREAM_BINARY` |
| Serene Seasons | `Glitchfiend/SereneSeasons`, branch `1.21.1` | `10.1.0.3`, CurseForge file `6182596` | Beta | `UPSTREAM_BINARY` |
| GlitchCore | `Glitchfiend/GlitchCore`, branch `1.21.1` | `2.1.0.2`, CurseForge file `8109792` | Beta | `UPSTREAM_BINARY` |
| Gabou's Libs | `xGabou/Gabou-s-Libs`, branch `1.21.1` | `1.9`, CurseForge file `8774265` | Release | `UPSTREAM_BINARY` |

These versions are **candidates**, not the final lock. Artifact SHA-256 values are intentionally still unset until DrewCraft's resolver downloads and verifies the actual files.

Project Atmosphere's selected candidate declares Serene Seasons and Gabou's Libs as required content, while Simple Clouds is optional upstream. DrewCraft nevertheless intends to include Simple Clouds as part of the V1 weather/rendering stack, subject to compatibility testing.

Serene Seasons requires GlitchCore, so GlitchCore is explicitly tracked rather than left as an invisible transitive dependency.

---

## Current performance and content candidate sets

The two companion manifests deliberately record candidates that are not all meant to coexist.

### Performance

The intended baseline profile includes the current 1.21.1 NeoForge candidates for ModernFix, FerriteCore, Lithium, ServerCore, ScalableLux, Chunk Sending, AllTheLeaks, FastSuite/FastWorkbench/FastFurnace, Clumps, Connectivity, spark, Embeddium, ImmediatelyFast, Entity Culling, MoreCulling and required libraries such as Placebo/Cupboard.

C2ME is an isolated world-build experiment until Terrain Diffusion/structure correctness and restart/corruption testing pass. See `docs/PERFORMANCE_STACK.md`.

### Tactical AI / herds / source structures

Current profiles include:

- Enhanced Hordes + Enhanced Hordes Tweaks **versus** Zombie Hordes;
- Ethological **versus** Herd Instinct;
- Towns and Towers + selective When Dungeons Arise as the first source-structure spike;
- CTOV as an alternative settlement/outpost branch;
- pack-owned structure density first, with Sparse Structures only if needed.

Required candidate libraries are recorded explicitly, including Cristel Lib for Towns and Towers and Lithostitched for the CTOV branch.

See `docs/MOB_STRUCTURE_CANDIDATES.md`.

---

## When a DrewCraft fork is justified

Create a DrewCraft fork only when at least one of these is true:

- an upstream project lacks an API/hook needed for a required V1 bridge;
- a blocking bug has a known source fix but upstream cannot ship it in the required time/version line;
- a project is abandoned and DrewCraft must maintain it to remain viable;
- ARM/server compatibility requires a source change that cannot live in the DrewCraft integration mod;
- a critical compatibility change cannot be safely implemented as an external NeoForge adapter/mixin;
- the upstream license explicitly allows the required modification/distribution arrangement.

Do **not** fork because:

- we want an easier download URL;
- we want every repo under `DrewPhi`;
- we want to tweak recipes/balance;
- a release is marked Beta but otherwise works;
- we want to rename upstream branding;
- a one-line adapter can live cleanly in the DrewCraft integration mod.

---

## Required fork workflow

If a dependency crosses the fork threshold:

1. verify its license permits the intended use;
2. create a fork/mirror under the DrewCraft maintainer account or organization;
3. preserve the original project as the canonical `upstream` remote;
4. choose an exact upstream base commit/tag;
5. create a DrewCraft maintenance branch for the target Minecraft line;
6. keep the patch set as small and isolated as possible;
7. document every DrewCraft-specific patch and why it cannot live in the integration mod;
8. update the relevant registry from `UPSTREAM_BINARY`/`UPSTREAM_SOURCE` to `DREWCRAFT_FORK`;
9. record upstream base ref, fork URL, DrewCraft commit SHA, build command, license notes, and artifact hash;
10. CI builds/tests the exact recorded fork commit;
11. regularly test rebasing/cherry-picking the patch set onto upstream maintenance releases;
12. upstream generally useful fixes when practical so DrewCraft can return to an unmodified upstream release later.

The goal of every fork should be to minimize permanent divergence.

---

## Source access without forking

Public source repositories recorded in the registries can be inspected directly when implementing adapters or diagnosing compatibility.

Distant Horizons is an exception only in hosting location: its official source is GitLab. It should remain recorded as GitLab rather than creating a GitHub mirror merely for uniformity.

For All Rights Reserved or otherwise restrictive projects, source visibility does **not** imply permission to redistribute modified builds. The manifests therefore record source access separately from artifact acquisition/redistribution policy.

---

## What Stage 1 should produce

Before Stage 2 compatibility testing starts, the upstream/dependency portion of Stage 1 is complete only when:

- [ ] all three candidate registries parse successfully as one dependency namespace;
- [ ] every direct baseline dependency has an official source/provider record;
- [ ] every selected compatibility-spike dependency has an official provider/source record where available;
- [ ] every known required transitive dependency has a record;
- [ ] every promoted dependency has an ownership class;
- [ ] the target 1.21.1/NeoForge maintenance branch/ref is known where source exists;
- [ ] the selected candidate artifacts are identified without pretending Beta/Alpha candidates are stable;
- [ ] provider project/file/version IDs are recorded where available;
- [ ] licenses and acquisition/redistribution constraints are recorded sufficiently to avoid accidental rehosting;
- [ ] no dependency has been forked merely for convenience;
- [ ] compatibility profiles prevent mutually exclusive alternatives from silently being stacked;
- [ ] the resolver can turn selected candidate/lock metadata into verified local artifacts;
- [ ] SHA-256 is computed from actual downloaded artifacts before any candidate is considered locked.

The Stage 2 compatibility matrix then decides what becomes the first known-good DrewCraft mod lock.
