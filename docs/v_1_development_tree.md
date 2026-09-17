# DrewCraft V1 Development Tree

**Authoritative profile:** `v1_survival_exploration`
**Scope frozen:** 2026-09-16

## Critical path

```text
V1 scope/profile lock
  -> exact dependency resolution and hashes
  -> dedicated-server fresh boot + restart
  -> focused gameplay smoke test
  -> one-manifest server/client release
  -> Windows/macOS/Linux launcher acceptance
  -> multiplayer soak + backup/restore
  -> 1.0.0
```

## 1. Scope and dependency lock

- [x] Define the focused V1 product in `docs/v_1_requirements.md`.
- [x] Add the single shipping profile `v1_survival_exploration`.
- [x] Include Terrain Diffusion, Distant Horizons, MTS vehicles/planes, the compatible Create stack, WDA, and performance essentials.
- [x] Restore the complete upstream WDA structure set by removing DrewCraft's former allow-list datapack.
- [x] Remove weather/seasons and custom strategic/endgame content from the shipping inheritance chain.
- [x] Default deferred DrewCraft systems off while preserving their implementation.
- [x] Point CI, dev releases, RC builds, server smoke tests, and hash jobs at the shipping profile.
- [ ] Obtain green remote evidence for the revised exact profile.

## 2. Server compatibility gate

- [ ] Rebuild every provider artifact and the pinned Terrain Diffusion source artifact.
- [ ] Compile and inject the DrewCraft mod.
- [ ] Install the exact NeoForge runtime.
- [ ] Reach readiness on a new Diffusion world.
- [ ] Stop cleanly, restart the same world, and reach readiness again.
- [ ] Reject missing dependencies, loader failures, mixin failures, and server tick-loop crashes.

No production-scale pregeneration is required for this gate. A disposable test world is enough.

## 3. Focused gameplay gate

- [ ] Confirm normal survival, mobs, farms, villages, structures, redstone, and saving.
- [ ] Drive one MTS ground vehicle and fly one MTS aircraft.
- [ ] Build and operate representative Create machinery and a train.
- [ ] Smoke-test Big Cannons, Gunsmithing, Aeronautics, High Seas, and Radars as ordinary Create content.
- [ ] Find or locate a WDA dungeon and verify generation, mobs, and loot.
- [ ] Confirm no deferred weather, strategic army, siege, herd, Source Core, or Covenant behavior activates.
- [ ] Record FPS, memory, server MSPT, and any crash/log warnings from a small multiplayer session.

## 4. Release and server gate

- [x] Maintain one provider-aware immutable `release-manifest.json` for client and server.
- [x] Maintain staged verification, atomic activation, server backup, health check, and application rollback.
- [ ] Produce a complete V1 server application from the shipping profile.
- [ ] Deploy it to the selected host and prove join/restart behavior.
- [ ] Complete one clean backup/restore drill.

## 5. Launcher and website gate

- [x] Support Windows x86-64, Apple Silicon macOS, and Ubuntu/Linux x86-64 packages.
- [x] Preserve Microsoft authentication through managed Prism.
- [x] Auto-launch the managed instance after authentication.
- [x] Stream downloads with progress, rate, ETA, resumable partials, and exact verification errors.
- [x] Point the website buttons at stable launcher aliases.
- [ ] Publish a launcher build whose live pack manifest was generated from `v1_survival_exploration`.
- [ ] Run clean install/login/launch/update tests on all three platforms.

## 6. V1 release gate

- [ ] Freeze one exact dependency and world-generation identity.
- [ ] Run a representative friend multiplayer soak.
- [ ] Resolve every V1-blocking defect.
- [ ] Promote the exact tested artifacts and website aliases.
- [ ] Tag `1.0.0` only after the promoted artifacts match the tested release.

## Post-V1

All weather, custom strategic simulation, custom endgame, and broader content work follows `docs/FURTHER_IDEAS.md`. It cannot re-enter V1 without an explicit scope decision.
