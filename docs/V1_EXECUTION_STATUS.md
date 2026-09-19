# DrewCraft V1 Execution Status

**Updated:** 2026-09-19
**Shipping profile:** `v1_survival_exploration`
**Phase:** server/gameplay proof

## Scope state

| Area | V1 state |
| --- | --- |
| Terrain Diffusion + Distant Horizons | Included |
| Normal multiplayer survival | Included |
| MTS vehicles and aircraft | Included |
| Create + selected compatible Create family | Included |
| Native Create: Radars | Included; upstream behavior only |
| Create: Gunsmithing firearm stack (NTGL/Sable and required libraries) | Included; requires dedicated crash/compatibility validation |
| Complete upstream WDA structure set with mobs/loot | Included |
| Performance and diagnostics | Included |
| One-manifest server/client release | Exact `0.1.3-dev-local` published and deployed |
| Windows/macOS/Linux launchers | 0.1.8 aliases live; clean platform acceptance pending |
| Weather/clouds/seasons | Post-V1 |
| DrewCraft radar-height/weather/terrain coupling and overlays | Post-V1; disabled |
| Sources/armies/sieges/herds/Covenant endgame | Post-V1; code preserved and disabled by default |

## Reusable completed work

- Exact dependency resolver, hashes, source-build provenance, and side-aware verified trees.
- DrewCraft mod build/injection and immutable release manifest machinery.
- Complete NeoForge server application assembly.
- Staged server update, backup, activation, health, and application rollback.
- Managed Java/Prism launchers for Windows, Apple Silicon macOS, and Ubuntu/Linux.
- Automatic managed-instance launch, repair, self-update, streaming progress, rate, ETA, and resumable downloads.
- WDA runtime compatibility override; upstream structure generation is otherwise unmodified.
- Strategic/weather systems retained for future releases behind feature flags.
- Launcher 0.1.8 retires the old Covenant resource pack from V1 and removes only that DrewCraft-managed directory from existing installs.

## Remaining V1 gates

1. ~~Validate and publish the focused profile.~~ Complete.
2. ~~Pass fresh-server boot and same-world restart.~~ Complete in run `35147504223`.
3. Pass focused hands-on gameplay smoke and small multiplayer performance evidence.
4. ~~Deploy the exact server application.~~ Complete; backup restore drill remains.
5. Pass clean install/login/launch/update on all three client platforms.
6. Freeze, soak, promote, and tag the exact tested release.

No post-V1 feature is part of these gates.

## Current local verification

- Focused profile: 35 dependencies, with only the pinned source-built Terrain Diffusion artifact intentionally unresolved at provider-validation time.
- Full Python test suite: 92 passed.
- Pinned Gradle 9.2.1 DrewCraft tests: passed.
- YAML parse, Python compile, and diff whitespace checks: passed.

## Published evidence

- Focused live pack and manifest: `0.1.3-dev-local` published from commit `c047739` with no Covenant or weather payload paths.
- Launcher 0.1.8: Windows, Apple Silicon macOS, and Ubuntu/Linux builds passed and are the website's latest release aliases.
- Server application layout and native ARM64 DrewCraft build passed.
- Dedicated-server run `35147504223` passed boot and restart, but its world generator was not verified; the production save was subsequently found to use Minecraft's normal Overworld. That run is **not** Terrain Diffusion evidence.
- World revision 2 must prove a Terrain Diffusion scale-3 saved generator before Chunky/DH pre-generation resumes. The current world reset and matched release deployment are tracked in `CURRENT_BREAKPOINT.md`.
