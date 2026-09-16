# DrewCraft V1 Playtest

This checklist tests the focused `v1_survival_exploration` build. Use a disposable world until the profile passes.

## Install and launch

- [ ] Download the correct Windows, Mac, or Linux launcher from `https://drewphi.github.io/DrewCraft/`.
- [ ] Confirm install/update progress shows bytes, rate, and ETA once estimable.
- [ ] On first use, authenticate through Prism if requested; close it when instructed and start DrewCraft again.
- [ ] On later uses, one DrewCraft invocation should update and launch the managed Minecraft instance automatically—never manually double-click the instance.
- [ ] Confirm Minecraft reaches the main menu without a missing dependency or mod-loading error.

## Create a disposable world

- [ ] Select Terrain Diffusion world generation, not superflat, for the real compatibility test.
- [ ] Allow the first model/world initialization to finish; save the log if progress stops advancing.
- [ ] Confirm terrain is unmistakably Diffusion terrain and Distant Horizons begins populating normally.
- [ ] Save, quit, reopen the same world, and confirm the restart is substantially simpler than first generation.

## Survival baseline

- [ ] Break/place blocks, craft, sleep, die/respawn, and save normally.
- [ ] Confirm ordinary hostile/passive mobs, caves, villages/vanilla structures, farms, redstone, and Nether access work.
- [ ] Confirm no custom army, Source Core, strategic herd, siege, Covenant, or weather-driven flight behavior activates.

## Vehicles and aircraft

- [ ] Spawn or craft one MTS ground vehicle; enter, drive, refuel if applicable, unload/reload, and restart.
- [ ] Spawn or craft one MTS aircraft; take off, fly, land, unload/reload, and restart.
- [ ] Confirm controls/keybinds do not conflict critically with Create Aeronautics.

## Create family

- [ ] Operate basic Create rotation, machinery, belts, and a train.
- [ ] Fire representative Create Big Cannons and Gunsmithing content without a crash.
- [ ] Assemble/move/save/reload a simple Aeronautics craft.
- [ ] Assemble/move/save/reload a simple High Seas vessel.
- [ ] Confirm Create: Radars loads and works as ordinary upstream content; custom DrewCraft weather products are not expected in V1.

## Dungeon exploration

- [ ] Locate or encounter one of the five enabled WDA dungeons.
- [ ] Confirm the structure generates cleanly and contains expected mobs and loot.
- [ ] Confirm WDA structures do not create a Source Core or launch strategic forces.

## Multiplayer/server

- [ ] Join with a client produced from the same release manifest.
- [ ] Complete a short vehicle, aircraft, Create, and dungeon session with at least two players where practical.
- [ ] Record server MSPT, client FPS/frame-time, memory, disconnects, and warnings.
- [ ] Stop the server cleanly, restart the same world, and rejoin.
- [ ] Complete one backup and clean restore before declaring the candidate releasable.

## Bug report bundle

Include the operating system, launcher version, pack version, exact action, screenshot, `latest.log`, and any crash report. For downloads, include the failed path and displayed verification message. Never paste Microsoft tokens, private keys, or account files.
