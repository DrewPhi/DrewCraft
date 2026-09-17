# DrewCraft Current Development Breakpoint

**Updated:** 2026-09-17
**Last completed breakpoint:** **BP-V1A — focused profile convergence**
**Current breakpoint:** **BP-V1B — server and gameplay proof**

## Decision

V1 has been deliberately narrowed to fun, reliable multiplayer survival: Terrain Diffusion, Distant Horizons, MTS vehicles/planes, the compatible Create stack, and the complete upstream WDA dungeon set. Weather and the custom strategic/endgame systems are post-V1.

## BP-V1A implementation

- Added authoritative `v1_survival_exploration` and lean `v1_survival_core` profiles.
- Kept the selected compatible Create family and excluded the known-incompatible CBC Firepower Components release.
- Included WDA through the existing narrow dependency override and restored its complete upstream structure set.
- Removed Atmosphere, clouds, seasons, Covenant, armies, sources, sieges, and herds from the shipping dependency chain.
- Defaulted DrewCraft's deferred weather/radar/strategic feature flags off.
- Repointed dev release, RC, server smoke, full-profile verification, validation, and hash workflows to the shipping profile.
- Updated website messaging while retaining stable Windows/Mac/Linux launcher aliases.
- Retired the Covenant resource pack from V1 release injection; launcher 0.1.8 removes only that formerly managed pack while preserving user resource packs.
- Rebased V1 documentation and moved the larger design into `docs/FURTHER_IDEAS.md`.

## Local evidence

- Shipping profile resolves deterministically to 35 dependencies; the only unresolved provider identity is the expected pinned Terrain Diffusion source build.
- The resolved graph contains every intended Create/MTS/WDA component and none of the deferred weather/Covenant/strategic dependencies.
- `/usr/bin/python3 -m pytest -q`: **92 passed**.
- Python bytecode compilation, YAML parsing, and `git diff --check`: passed.
- Pinned Gradle 9.2.1 `test`: **BUILD SUCCESSFUL**.

## BP-V1A remote evidence

- Commit `3ac388a` is pushed to `main`.
- Pack manifests, provider hashes, DrewCraft mod CI, full V1 profile verification, source-structure smoke, BP8 convergence, and live-pack publication passed.
- The published evidence names `v1_survival_core` and `v1_survival_exploration`; the release manifest contains no Covenant or weather paths.
- Launcher **0.1.8** was published as GitHub's latest release with the exact Windows EXE, Apple Silicon DMG, and Linux DEB filenames used by the website.
- The existing website buttons therefore download 0.1.8, and existing launchers converge through the corrected `live.json`.
- The focused pack is versioned `0.1.3-dev-local`, requires launcher 0.1.8, and carries the OCI server address plus health endpoint so DrewCraft launches directly into the matching server. This revision adds a temporary Overworld-only generated-area boundary without constraining Nether or End.

## BP-V1B

Pack `0.1.2-dev-local` is published from `v1_survival_exploration` and live on OCI. The ARM64 host generated a fresh Diffusion spawn, reached `Done`, stopped cleanly, reopened the same persistent world, and reached `Done` again. Post-start manifest verification was exact, the fatal-log scan was clean, both systemd services are enabled, and the public health endpoint reports the matching pack ready. The public website points at manifest SHA-256 `b7706a74bacbae1ede53ba4b6547715fae32bbf09badee4978219f6169146bb6`.

Next, launch through DrewCraft 0.1.8 and complete the hands-on gameplay checklist: join, normal survival, vehicle, aircraft, representative Create content, and a WDA dungeon. Then run platform acceptance, a small multiplayer soak, and the retained backup restore drill. Do not require production world pregeneration or post-V1 features.
