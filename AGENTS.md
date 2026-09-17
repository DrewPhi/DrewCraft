# AGENTS.md — DrewCraft

This repository is the canonical source for the DrewCraft Minecraft server, pack, launcher, and download site.

## Read first

1. `docs/v_1_requirements.md` — hard V1 scope
2. `docs/v_1_development_tree.md` — ordered execution gates
3. `docs/CURRENT_BREAKPOINT.md` — exact stop/resume state
4. `docs/V1_EXECUTION_STATUS.md` — live evidence summary
5. `docs/FURTHER_IDEAS.md` — explicitly deferred systems
6. `docs/BP8_RELEASE_OPERATIONS.md` — retained release/server ownership
7. `docs/PERFORMANCE_STACK.md`, `docs/MOD_STACK.md`, and `pack/manifest/README.md`
8. `docs/LAUNCHER_HOSTING.md` and `docs/REPO_ARCHITECTURE.md`

Archived strategic/weather/endgame documents are design references for post-V1 only. They do not override the focused V1 requirements.

## V1 scope

The one shipping profile is `v1_survival_exploration`.

V1 includes Terrain Diffusion Plus, Distant Horizons, normal multiplayer survival, MTS vehicles and aircraft, Create and the compatible selected Create family, the complete upstream When Dungeons Arise structure set, conservative performance mods, one-manifest client/server releases, and one-click Windows/macOS/Linux launchers.

V1 excludes weather/clouds/seasons, custom radar/weather coupling, strategic sources/armies/sieges/herds, Covenant invasion/endgame, and broad balance redesign. Preserve existing work, but keep it disabled by default and out of the shipping profile.

Do not add gameplay mods or restore deferred systems to V1 without an explicit owner decision.

## Release rules

- `release-manifest.json` is client/server application truth; `live.json` is only a channel pointer.
- Client and server always derive from the same shipping profile and immutable manifest.
- Provider artifacts use exact identities and hashes; do not casually change versions.
- DrewCraft's compiled mod must be injected and hash-recorded on both sides.
- Persistent world/logs stay outside immutable server applications.
- Server updates stage, verify, back up, atomically activate, health-check, and roll back only the application on failure.
- Never publish a pointer or website alias before its referenced artifacts exist.

## Launcher rules

- Supported public artifacts are `DrewCraft-Windows.exe`, `DrewCraft-macOS.dmg`, and `DrewCraft-Linux.deb`.
- Prism remains an implementation detail for Microsoft authentication; DrewCraft owns install, sync, repair, update, and automatic instance launch.
- Preserve user-owned saves, screenshots, resource packs, shader packs, and options where not pack-managed.
- Stream downloads, show progress/rate/ETA, support resumable partials, and report the exact failed file.

## Testing policy

Prefer resolver, schema, unit, compile, and focused integration tests during ordinary development. Fresh Terrain Diffusion world generation is expensive; run it only when dependency/worldgen changes invalidate evidence or at the dedicated server gate. Never claim a world, host, launcher, or multiplayer gate without real evidence.

## Current path

Follow `docs/CURRENT_BREAKPOINT.md`. The next proof is the revised shipping-profile build and server/gameplay smoke gate. Post-V1 systems cannot block V1 release.
