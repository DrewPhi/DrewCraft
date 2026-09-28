# DrewCraft Current Development Breakpoint

## 2026-09-27 quality-of-life rollout

Pack 0.1.12-dev-local is published, active on the Oracle server, and promoted
to the shared launcher channel. The public health endpoint reports ready and
joinable for `drewcraft-production` revision 3. The update kept the existing
world (~18 GB), dock, player data, and DH/pregeneration checkpoint; no live
world was recreated. Jade and AppleSkin are present server-side; Sodium,
LambDynamicLights, Mouse Tweaks, and Nemo's Inventory Sorting are client-only.
The pinned full pack assembled and verified locally (223 client files, 218
server files); 117 Python tests and the Gradle test build passed. The existing
launcher 0.1.10 meets the release's minimum version and should auto-fetch the
new pack. Owner-led in-game acceptance on the actual client platforms remains
open, especially Sodium/Aeronautics/DH rendering and the dynamic-light toggle.

## 2026-09-27 map persistence rollout

Launcher 0.1.10 and pack 0.1.11-dev-local are published and deployed. The shared
client channel matches the healthy, joinable server. World Map is client-only;
map/waypoint folders now survive launcher updates and repairs. Existing world,
dock, welcome book and DH-only catch-up state were preserved. See
`MAP_PERSISTENCE.md` for exact release/backup evidence and remaining owner-led
client acceptance. No terrain expansion was resumed.

## 2026-09-26 owner-directed AOT rollout

Release 0.1.10-dev-local uses `v1_2_paradis_candidate`, extending V1.1 with
Danny's AOT and its exact compatibility dependencies. See `AOT_INTEGRATION.md`
for evidence, the administrator dock command and explicitly unverified gameplay
checks. The owner requested stopping local interactive testing and deploying
for their own real-server acceptance. Preserve world revision 3; no world reset
or automatic dock placement is authorized. Release assets are versioned; promote
the launcher's `drewcraft-dev-pack/live.json` only after server activation/health.

The older breakpoint history below is retained; it is not current release state.

**Updated:** 2026-09-19
**Last completed breakpoint:** **BP-V1A — focused profile convergence**
**Current breakpoint:** **BP-V1B — server and gameplay proof**

## Decision

V1 has been deliberately narrowed to fun, reliable multiplayer survival: Terrain Diffusion, Distant Horizons, MTS vehicles/planes, the compatible Create stack (including Create: Radars and the NTGL/Gunsmithing firearm stack), and the complete upstream WDA dungeon set. Weather and DrewCraft-specific radar/strategic/endgame systems are post-V1.

## BP-V1A implementation

- Added authoritative `v1_survival_exploration` and lean `v1_survival_core` profiles.
- Kept the selected compatible Create family and excluded the known-incompatible CBC Firepower Components release.
- Included WDA through the existing narrow dependency override and restored its complete upstream structure set.
- Removed Atmosphere, clouds, seasons, Covenant, armies, sources, sieges, and herds from the shipping dependency chain.
- Defaulted DrewCraft's deferred weather/radar/strategic feature flags off while retaining ordinary upstream Create: Radars behavior.
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

**Correction:** The prior fresh-world server smoke reached `Done` but did not prove Terrain Diffusion world selection. On 2026-09-19, the live `server.properties` was found to contain `level-type=minecraft\\:normal`, and the saved Overworld uses Minecraft's normal biome source and noise settings. Thus the existing generated world is not a Terrain Diffusion world. Do not reuse the old worldgen claim as evidence.

The current deployment target is `0.1.7-dev-local` / world revision 3. It pins JEI, uses a DrewCraft-owned dedicated-server preset backed by the upstream Terrain Diffusion scale-3 dimension, seeds the upstream per-world scale SavedData before first boot, restores full inference-window overlap, and triples the previous WDA major/minor spacing. A guard checks the saved generator and scale before the pregen controller can generate chunks. The controller centers the new world at its actual saved spawn. Launcher 0.1.9 adds the server to the multiplayer list and preserves user entries; client DH radius defaults to 32 on new installs.

The first attempted release (`0.1.6-dev-local` / revision 2) exposed a packaging mistake: WDA placement JSON was copied into the pack root rather than a loadable world datapack. The server was stopped before any region files were generated. Revision 3 ships the overrides in `datapacks/drewcraft-structures` and installs them into the world before first boot. Do not treat revision 2 as a completed world-generation test.

The owner authorized deleting the old production world without a backup. It and the tiny revision-2 placeholder have been deleted; no reset backup was made. This is a one-time world reset; normal future application updates retain the existing backup policy. Release `0.1.7-dev-local` is staged and active on the Oracle VM. On the fresh revision-3 world, `worldgen_guard.py` verifies the saved Terrain Diffusion generator and World Scale 3, and `level.dat` lists `file/drewcraft-structures` among enabled datapacks. Both the server and idle-only pregeneration controller are active; first spawn generation was still running at the last check, so readiness and gameplay remain unverified. User visual verification is next; no separate preview world is required.
