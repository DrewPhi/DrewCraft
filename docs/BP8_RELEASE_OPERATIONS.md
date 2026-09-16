# DrewCraft Release, Server, and Launcher Operations

This is the retained operational contract originally completed during BP8. It applies to the focused V1 unchanged.

## One release truth

- `release-manifest.json` is the immutable client/server application contract.
- `live.json` is only a channel pointer to an already-published manifest.
- The V1 manifest must be generated from `v1_survival_exploration`.
- Every managed file records side, path, size, SHA-256, origin, and acquisition URL.
- Provider files use their official acquisition paths where possible; the public DrewCraft payload contains only files DrewCraft may distribute.

## Server contract

- A server application includes the exact NeoForge runtime and verified server tree.
- Applications are immutable; world, logs, backups, and operator state are persistent and separate.
- Updates stage and verify, check world compatibility, stop safely, create a checksummed backup, atomically switch, and health-check.
- On failure restore the previous application pointer and metadata. Never blindly roll an authoritative world backward.
- Production defaults use online authentication and a whitelist.

## Launcher contract

- Exact Java and Prism runtimes are pinned per platform.
- Prism owns Microsoft authentication; DrewCraft owns convergence and launch.
- Updates stream to disk, resume safe partials, expose progress/rate/ETA, verify before promotion, and preserve user-owned data.
- A successful DrewCraft invocation launches the managed instance automatically, including after first authentication completes.
- Public packages are Windows x86-64 EXE, Apple Silicon DMG, and Ubuntu/Linux x86-64 DEB.

## World contract

- Application version and world identity are separate.
- `worldId`, `worldRevision`, and `generationPackVersion` gate compatibility.
- Do not require a massive pregenerated production world to prove the focused V1 profile. Choose pregeneration radius only after measuring the actual host and desired map size.
- Backups and restores must be tested with real files before release.

## Promotion rule

Upload content and manifests first, publish `live.json` last, and update stable website aliases only after all referenced launcher artifacts exist. The exact promoted release must be the one that passed server, launcher, multiplayer, and recovery acceptance.
