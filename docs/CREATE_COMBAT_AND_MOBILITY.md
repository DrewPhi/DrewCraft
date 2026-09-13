# DrewCraft Create Combat and Block-Built Mobility

This document records the current design for DrewCraft's Create-based combat and physics-vehicle layer.

The guiding rule is:

> **Create should turn warfare and mobility into engineering/logistics problems, not just add stronger items.**

## Selected stack

### Create Big Cannons

Selected role: heavy artillery, autocannons, structural gun positions, ammunition systems, loading, aiming, fuzes, and siege weapons.

DrewCraft use cases:

- castle-wall guns;
- gate/chokepoint autocannons;
- field artillery;
- bunker emplacements;
- ship guns;
- airship guns after moving-platform compatibility is proven;
- ammunition factories and magazines;
- Create-powered loading/aiming.

Routine horde defense should favor controllable anti-personnel roles such as autocannons, grapeshot/shrapnel-style ammunition, and other lower-collateral options. Large HE remains deliberate siege artillery.

CBC block destruction must be tested before production. The desired result is that artillery matters without making a single accidental shot capable of casually deleting a carefully built settlement.

### CBC: Firepower Components

Selected role: make CBC practical in compact fortifications and vehicles.

Key value:

- compact cannon mounts;
- compact autocannon mounts;
- ammunition feeds;
- magazine loaders;
- pitch/yaw limiters.

This is especially useful for castles, bunkers, ships, and eventual airships where the full-size default machinery may be awkward.

### Create: Gunsmithing

Selected role: handheld firearms.

It is preferred over a generic modern-gun ecosystem because its animated steampunk/Create visual language fits DrewCraft's industry and world aesthetic.

The handheld/heavy split is intentional:

- **Create: Gunsmithing** = weapons carried by players;
- **Create Big Cannons** = artillery, autocannons, emplacements and siege weapons.

### Create Aeronautics

Selected role: player-engineered block-built moving contraptions.

Aeronautics is **not** a replacement for MTS.

Transport ownership is:

- **MTS / Immersive Vehicles** — practical prefab cars, trucks and conventional aircraft;
- **Create trains** — repeated heavy overland freight and infrastructure;
- **Create Aeronautics** — block-built experimental vehicles, airships, custom aircraft and moving machines;
- **Create: High Seas** — large block-built ships using Aeronautics/Sable physics.

The distinction is valuable because MTS provides immediate reliable transport while Aeronautics provides a late-game engineering sandbox.

### Create: High Seas

Selected role: physically simulated large ships built block by block.

Desired behavior includes:

- displacement-based buoyancy;
- material density;
- watertight compartments;
- progressive flooding;
- floodwater weight;
- drainage;
- pressure-driven water propagation;
- changing trim/list as a ship floods.

This makes naval damage and ship design structural rather than an abstract HP bar.

A mature ship should be able to contain Create machinery, cargo systems, magazines, and Create Big Cannons if compatibility testing proves that combination stable.

## Horde warfare loop

Large hostile forces should create a logistics problem before they create a combat problem.

Example defensive sequence:

1. DrewCraft strategic simulation reports an approaching hostile army.
2. Players determine likely route/ETA.
3. Factories manufacture ammunition.
4. Trains/trucks move shells and supplies to the threatened settlement.
5. Wall autocannons and artillery positions are stocked.
6. Gates, roads, bridges, trenches and fallback positions are prepared.
7. The strategic army materializes as it reaches the defended area.
8. Fortification design, ammunition supply and firing positions materially affect the fight.

The point is not simply to make mobs easier to kill. The point is to give factories, freight, roads, trains, castles and logistics a reason to exist.

## Moving-platform warfare

Moving weapons are a compatibility goal, not something to assume merely because each mod boots separately.

Acceptance order:

1. CBC works reliably on static ground.
2. Gunsmithing projectiles work reliably on ordinary terrain.
3. Sable/Aeronautics contraptions move, unload/reload and restart safely.
4. NTGL/Gunsmithing projectiles collide correctly with Sable sub-levels.
5. CBC projectiles collide correctly with Sable sub-levels.
6. Firepower Components mounts work on moving platforms.
7. High Seas ships survive damage/flooding while carrying Create systems.
8. Only then accept armed ships/airships as supported survival gameplay.

This ordering prevents an exciting combined build from hiding a corruption or persistence bug.

## Sable compatibility importance

Sable is the physics/sub-level foundation used by Aeronautics. It is intentionally treated as a high-risk compatibility dependency because it is invasive by design.

The currently selected versions line up unusually well for DrewCraft:

- Create Big Cannons 5.11.7 includes Sable 2.x compatibility work;
- NukaTeam Gun Lib 3.2.0 explicitly adds Sable support so firearm projectiles do not simply pass through moving sub-levels;
- Create Aeronautics 1.3.2 uses Sable;
- High Seas is built around the same Aeronautics/Sable physics model.

That is why this stack is tested as one dedicated compatibility profile rather than installing the mods independently and hoping their interactions work.

## Explicit non-selections

### Create Weaponry

Do not add for V1. It mainly overlaps melee/tool crafting, changes normal tool progression, and does not fill a missing DrewCraft capability.

### Create: Caliber

Do not add for V1. The chosen Gunsmithing + CBC split already covers handheld firearms and heavy weapons with more mature components.

### Clockwork / Valkyrien Skies

Do not add solely to obtain block-built vehicles. Aeronautics/Sable provides a native Minecraft 1.21.1 NeoForge path and adding a second physics authority would increase compatibility risk substantially.

### Night optics / spotlights

Deferred. No DrewCraft night-optics system is planned now, and spotlight/searchlight dependencies should not expand the V1 stack until the core combat/vehicle systems are stable.

## V1 balance policy

V1 should first prove the complete systems using upstream/default recipes where practical.

Post-V1 tuning can address:

- firearm/ammunition cost;
- artillery ammunition cost;
- HE structural damage;
- cannon production complexity;
- ship/airship progression;
- whether strategic hordes require more or less ammunition/logistics;
- late-game military economy.

Do not prematurely rewrite all recipes merely because powerful weapons exist. First establish that the systems work and produce the intended gameplay.
