# DrewCraft V1 Remaining Execution Plan

**Updated:** 2026-09-16
**Shipping profile:** `v1_survival_exploration`

The former plan centered on custom weather, armies, Source Cores, sieges, and herds. Those implementations and designs are preserved for later releases, but they are no longer on the V1 critical path.

## Remaining sequence

1. **Profile evidence** — validate the resolved graph, exact identities, side partition, WDA allow-list, and absence of deferred mods.
2. **Server evidence** — build pinned Terrain Diffusion, compile DrewCraft, boot a new server world, stop, and restart it.
3. **Gameplay evidence** — test survival, MTS ground/air vehicles, representative Create features, and one enabled WDA dungeon with deferred custom systems inactive.
4. **Host evidence** — deploy the exact server application to the selected host, measure a small multiplayer session, and record `PASS` or a concrete host migration.
5. **Launcher evidence** — clean install, Microsoft login, one-action subsequent launch, progress/ETA, repair, and update on Windows, Apple Silicon macOS, and Ubuntu/Linux.
6. **Operations evidence** — test backup, clean restore, application rollback, and client/server version mismatch handling.
7. **Release candidate** — freeze one exact manifest, run the multiplayer soak, publish matching launcher aliases, and tag only the tested build.

## Stop conditions

Do not broaden content while closing V1. Stop and fix only failures that block installation, launch, server boot/join, data safety, basic performance, or the four defining gameplay pillars.

Ideas and already-built systems outside those pillars belong to `docs/FURTHER_IDEAS.md`.
