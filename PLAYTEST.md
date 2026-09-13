# DrewCraft Playtest Checklist

This is the **fast path for the current local single-player development build**. Use this file while playing; the useful commands are beside the test they accelerate.

> **Current test build:** `0.1.0-dev-local` — local/single-player only. You do **not** need Oracle or a DrewCraft server for this checklist. Create the test world with **cheats enabled** (all `/drewcraft` commands require permission level 2). Creative mode is recommended for the first pass.

## 0. Install and launch

- [ ] Open `https://drewphi.github.io/DrewCraft/` and click your OS.
- [ ] Windows: run `DrewCraft-Windows.exe`. This is a development binary, so SmartScreen may identify it as an unrecognized app.
- [ ] Apple Silicon Mac: open `DrewCraft-macOS.dmg`, then DrewCraft. The dev app is not Apple-notarized yet; if Gatekeeper blocks it, Control-click **Open** (or use Privacy & Security → Open Anyway).
- [ ] First DrewCraft launch installs/repairs the exact pack, managed Java 21, and Prism Launcher automatically.
- [ ] If Prism opens for Microsoft authentication, sign in once, close Prism, then open DrewCraft again.
- [ ] In Minecraft choose **Singleplayer** and make a fresh disposable test world. Use the Terrain Diffusion Plus worldgen/config with **World Scale 2** for the V1-style terrain if that option is shown.
- [ ] Keep cheats on. First Terrain Diffusion world generation may also acquire its pinned model assets.

### 10-minute smoke test

Run these first. If any fail, stop and save `latest.log` before doing deeper testing.

```mcfunction
/drewcraft status
/drewcraft env sample
/drewcraft strategic create-test
/drewcraft strategic list
/drewcraft herd create-test minecraft:cow 80
/drewcraft herd list
/drewcraft source create-test
/drewcraft source list
```

Then visually confirm:

- [ ] Terrain is unmistakably Terrain Diffusion-scale terrain and generates without corruption.
- [ ] Weather/clouds render and `/drewcraft env sample` returns environment data rather than crashing.
- [ ] An 80-cow strategic herd never needs more than the bounded tactical population near you.
- [ ] The purple/black Source Core appears; break it and confirm the server/chat says the hostile source was deactivated.
- [ ] Save and quit, relaunch DrewCraft, reopen the world, and rerun `/drewcraft status`, `/drewcraft herd list`, and `/drewcraft source list`.

---

## 1. General integration / persistence

```mcfunction
/drewcraft status
/drewcraft env sample
/drewcraft power sample
/drewcraft state touch
```

- [ ] `status` reports DrewCraft version/protocol/persistence schema and feature flags.
- [ ] `env sample` reports terrain/weather integration at your position.
- [ ] Put yourself next to a powered Create kinetic setup and run `power sample`; verify the Create power adapter reports useful state.
- [ ] Save/quit/relaunch after creating strategic state and verify the counts are still present.

## 2. Strategic routing and unloaded movement

Create one deterministic diagnostic group. It receives a cached route roughly 10,000 blocks east from your current position.

```mcfunction
/drewcraft strategic create-test
/drewcraft strategic list
```

Copy the UUID printed by `list` and use it below:

```mcfunction
/drewcraft strategic inspect <groupId>
/drewcraft strategic route <groupId>
/drewcraft strategic eta <groupId>
/drewcraft strategic step 60
/drewcraft strategic inspect <groupId>
/drewcraft strategic perf
/drewcraft strategic routing-perf
```

- [ ] Position/ETA advances without you traveling with the group or loading a 10,000-block corridor.
- [ ] Save/quit/restart; the same UUID, route, position, mission, and ETA remain coherent.
- [ ] Run several `step 60` calls to accelerate coarse travel without waiting in real time.

Useful terrain-routing debug commands:

```mcfunction
/drewcraft strategic terrain capture-here
/drewcraft strategic terrain set-here ROAD
/drewcraft strategic terrain set-here BRIDGE
/drewcraft strategic terrain set-here NORMAL
/drewcraft strategic terrain set-here DIFFICULT
/drewcraft strategic terrain set-here WATER
/drewcraft strategic terrain set-here BLOCKED
/drewcraft strategic routing-perf
```

Use `set-here` only in a disposable test world; it changes the coarse strategic routing cost for the cell you occupy.

## 3. Hostile Source Core — hand destruction and explosives

Go to a disposable clear spot (the debug command places the core at your current block position):

```mcfunction
/drewcraft source create-test
/drewcraft source list
```

Copy the Source UUID if you want details:

```mcfunction
/drewcraft source inspect <sourceId>
/drewcraft source perf
```

### Break by hand

- [ ] Move clear of the core and destroy it normally.
- [ ] Confirm the DrewCraft deactivation chat message appears once.
- [ ] Run `/drewcraft source list`; that source should be `CLEARED`.
- [ ] Save/quit/restart; it must still be `CLEARED` and must never reactivate.

### Blow one up

Move to a **different location** first so this is a different deterministic test source:

```mcfunction
/drewcraft source create-test
```

- [ ] Use TNT / an explosive that actually destroys the Source Core.
- [ ] Confirm the same permanent deactivation message/state.
- [ ] If the blast does **not** destroy the core block, the source should remain active — that is intentional.

Admin fallback when needed:

```mcfunction
/drewcraft source clear <sourceId>
```

### Let a test source produce a hostile group

Create a source and leave it intact briefly, then inspect:

```mcfunction
/drewcraft source create-test
/drewcraft source perf
/drewcraft strategic list
```

- [ ] New launched strategic forces are persistent records.
- [ ] Clearing the Source Core stops **future** launches but does not erase a force that already launched.

## 4. Strategic herd / bounded materialization

This is the quickest way to see the LOD population system in-game:

```mcfunction
/drewcraft herd create-test minecraft:cow 80
/drewcraft herd list
/drewcraft herd ecology
```

Expected behavior:

- [ ] Herd represents 80 cows strategically.
- [ ] At most **64** should be active tactical entities for one encounter; the remainder stays abstract.
- [ ] Kill 10 strategic herd cows while they are materialized.
- [ ] `/drewcraft herd list` should eventually reflect **70** strategic survivors.
- [ ] Move more than roughly 224 blocks away so the tactical herd can collapse back to its strategic record.
- [ ] Save/quit/relaunch and verify the same herd still has the surviving population and migration objective.

Try another species if desired:

```mcfunction
/drewcraft herd create-test minecraft:sheep 120
/drewcraft herd create-test minecraft:pig 50
```

### Ordinary ecology must stay ordinary

- [ ] Spawn/breed some normal cows yourself.
- [ ] Name one, leash one, and pen some animals.
- [ ] Verify `/drewcraft herd list` does **not** absorb those ordinary animals.
- [ ] Run `/drewcraft herd ecology` for the intended isolation contract.

## 5. Vanilla spawning / farms / spawners coexistence

```mcfunction
/difficulty normal
/time set night
/drewcraft herd ecology
```

- [ ] Ordinary hostile mobs still spawn at night / in caves.
- [ ] Ordinary passive mobs still behave normally.
- [ ] A vanilla or modded spawner still works.
- [ ] If convenient, test a small mob-farm setup; strategic caps must not quota local vanilla mobs.

## 6. Weather, clouds, seasons, and terrain

```mcfunction
/drewcraft env sample
```

- [ ] Walk/fly through varied Terrain Diffusion terrain and sample several locations.
- [ ] Weather/cloud visuals remain coherent over large terrain.
- [ ] Check rain/storm/wind transitions during normal play rather than relying only on vanilla `/weather` commands.
- [ ] Use Project Atmosphere's handheld **Weather Radar** from creative inventory and confirm it is useful as the V1 pilot/explorer weather device.
- [ ] Check Serene Seasons behavior does not visibly fight Terrain Diffusion/Atmosphere climate behavior.

For Project Atmosphere-specific debug commands, type `/pa` and use Minecraft tab completion rather than relying on a memorized upstream subcommand.

## 7. Create + radar

Build a tiny Create setup in creative mode.

```mcfunction
/drewcraft power sample
```

- [ ] Shafts/cogs/kinetic networks behave normally.
- [ ] `power sample` near the setup reports meaningful power state.
- [ ] Build Create: Radars hardware from creative inventory and verify the normal upstream radar/network/monitor flow works.
- [ ] Materialized mobs may be radar contacts; **abstract unloaded armies/herds must not magically appear as physical radar contacts**.
- [ ] Terrain/weather integration must not break the upstream radar hardware.

## 8. Vehicles / aircraft

Use Immersive Vehicles / MTS Official Pack items from creative inventory.

- [ ] Spawn and drive a ground vehicle.
- [ ] Spawn and fly an aircraft.
- [ ] Cross varied Terrain Diffusion terrain at speed.
- [ ] Observe flight during weather/wind where possible.
- [ ] Confirm ordinary vehicle controls and MTS behavior are still intact.

Dedicated MTS cockpit weather radar is **not** a V1 requirement; the handheld Atmosphere Weather Radar is the V1 pilot weather device.

## 9. Distant Horizons / exploration

- [ ] Fly to altitude and explore quickly.
- [ ] Lower normal Minecraft render distance enough that Distant Horizons' distant terrain is obvious.
- [ ] Confirm distant terrain transitions are visually sane with Terrain Diffusion.
- [ ] Watch memory/frametime while exploring; report severe stutters, visual holes, or persistent corrupted LODs.

## 10. Hostile materialization / casualties / restart

The easiest local path is to leave a test source intact until it launches a group, then stay near the group's area and inspect it:

```mcfunction
/drewcraft source perf
/drewcraft strategic list
/drewcraft strategic inspect <groupId>
```

- [ ] A nearby force materializes only a bounded tactical subset.
- [ ] Kill several members; only actual confirmed deaths reduce strategic strength.
- [ ] Move away, return, and verify dead members are not resurrected by dematerialization.
- [ ] Save/quit during/after the encounter and restart; verify no duplication and no lost casualties.

## 11. Siege

BP6 siege is implemented and CI-tested, but the current local dev commands do **not** contain a fake `spawn-army`/`force-siege` command. Do not invent one just for this checklist.

If you naturally obtain a materialized `RAID` or `ARMY` during testing:

- [ ] Give it an obvious open gate/path first — it should use navigation and break nothing.
- [ ] Then test a truly sealed simple fort — designated siege-capable units may choose a bounded useful breach.
- [ ] Put decoration/stateful blocks nearby; the planner should avoid pointless griefing.

The representative large-raid/army siege test belongs in **BP9** once the real production-source geography and multiplayer server are running.

## 12. Performance snapshot

During a busy test:

```mcfunction
/drewcraft strategic perf
/drewcraft strategic routing-perf
/drewcraft source perf
```

Spark is included. Type `/spark` and use tab completion for the installed build's profiler commands, then capture a short profile while flying/materializing mobs if something feels slow.

Record:

- FPS / obvious frame spikes
- server TPS/MSPT symptoms
- memory growth or long freezes
- what you were doing (worldgen, aircraft, herd, source force, radar, Create machine, etc.)

## 13. Update / repair test

The DrewCraft launcher itself is the repair path.

- [ ] Close Minecraft.
- [ ] Delete or corrupt one **managed mod file inside the DrewCraft Prism instance** (do this only in this disposable test install).
- [ ] Reopen DrewCraft.
- [ ] Verify it reconstructs the exact managed instance rather than requiring you to manually repair a mods folder.
- [ ] Verify your screenshots/options/resource packs are preserved where they are user-owned rather than pack-managed.

## 14. What to send with a bug

For every reproducible problem, capture:

1. exact steps you performed;
2. screenshot/video if visual;
3. the relevant `groupId` / `sourceId` from `/drewcraft strategic list` or `/drewcraft source list`;
4. output of `/drewcraft status`;
5. `latest.log` (and crash report if one exists).

Fastest way to find the log is from Prism: right-click the DrewCraft instance → **Instance Folder** → `minecraft/logs/latest.log`.

For a performance bug also include:

```mcfunction
/drewcraft strategic perf
/drewcraft strategic routing-perf
/drewcraft source perf
```

---

# Command cheat sheet

```mcfunction
# Overall
/drewcraft status
/drewcraft env sample
/drewcraft power sample
/drewcraft state touch

# Strategic groups
/drewcraft strategic create-test
/drewcraft strategic list
/drewcraft strategic inspect <groupId>
/drewcraft strategic destination <groupId> <x> <z>
/drewcraft strategic route <groupId>
/drewcraft strategic eta <groupId>
/drewcraft strategic step <seconds>
/drewcraft strategic perf
/drewcraft strategic routing-perf
/drewcraft strategic terrain capture-here
/drewcraft strategic terrain set-here <ROAD|BRIDGE|NORMAL|UNKNOWN|DIFFICULT|WATER|BLOCKED>

# Hostile sources
/drewcraft source create-test
/drewcraft source list
/drewcraft source inspect <sourceId>
/drewcraft source clear <sourceId>
/drewcraft source perf

# Wild herds
/drewcraft herd create-test <entityId> <count>
/drewcraft herd list
/drewcraft herd ecology
```

When the local build is behaving well, the next development step is **BP9**: lock the real production world, deploy the real multiplayer server, then stress all of these systems together with friends.
