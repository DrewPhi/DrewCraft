# First-join mismatch evidence — 2026-09-15

Client: DrewCraft 0.1.0-dev-local (base dev release, no playtest_01 mods).
Server: Oracle A1 test server, 46-mod playtest set, online-mode=true.
Result: kicked at handshake, `Incompatible client! Please use NeoForge 21.1.250`.

## Missing server channels by mod (91 total)
- ?: 91

## Client mod list at join time
- All The Leaks 1.1.12+1.21.1-neoforge (alltheleaks)
- Architectury 13.0.11 (architectury)
- Cloth Config v15 API 15.0.140 (cloth_config)
- conditional mixin 0.6.3 (conditional_mixin)
- Connectivity Mod 7.6 (connectivity)
- CrackersLib 1.21.1-0.4.6 (crackerslib)
- Create 6.0.10 (create)
- Create Big Cannons 5.11.7 (createbigcannons)
- Create: Radars 0.4.9.4-1.21.1 (create_radar)
- Cristel Lib 3.1.7 (cristellib)
- Cupboard mod 4.1 (cupboard)
- Distant Horizons 3.2.0-b (distanthorizons)
- DrewCraft 0.1.0-dev.1 (drewcraft)
- Embeddium 1.0.15+mc1.21.1 (embeddium)
- EntityCulling 1.10.5 (entityculling)
- Fast Suite 6.0.7 (fastsuite)
- Fast Workbench 9.1.3 (fastbench)
- FastFurnace 9.0.1 (fastfurnace)
- Ferrite Core 7.0.3 (ferritecore)
- Flywheel 1.0.6 (flywheel)
- gaboulibs 1.9 (gaboulibs)
- GlitchCore 2.1.0.2 (glitchcore)
- ImmediatelyFast 1.6.13+1.21.1 (immediatelyfast)
- Immersive Vehicles (formerly MTS) 24.0.0 (mts)
- Immersive Vehicles (MTS/IV) - Official Content Pack 29 (mtsofficialpack)
- Lithium 0.15.4+mc1.21.1 (lithium)
- Minecraft 1.21.1 (minecraft)
- ModernFix 5.27.24+mc1.21.1 (modernfix)
- More Culling 1.0.10 (moreculling)
- NeoForge 21.1.250 (neoforge)
- Placebo 9.9.2 (placebo)
- Ponder 1.0.82+mc1.21.1 (ponder)
- Project Atmosphere 0.9.1.2 (projectatmosphere)
- Ritchie's Projectile Library 2.1.2 (ritchiesprojectilelib)
- Sable Companion 1.5.0 (sablecompanion)
- ScalableLux 0.1.0.1+neoforge.1cb1e91 (scalablelux)
- Serene Seasons 10.1.0.3 (sereneseasons)
- Simple Clouds 0.7.3+1.21.1 (simpleclouds)
- terrain-diffusion-mc 2.3.0-cpu (terrain_diffusion_mc)
- Towns and Towers 1.13.11 (t_and_t)
- TRansition 1.0.21 (transition)
- TRender 1.0.15 (trender)
- When Dungeons Arise 2.1.68 (dungeons_arise)
- YUNG's API 1.21.1-NeoForge-5.1.6 (yungsapi)
- YUNG's Better Caves 1.21.1-NeoForge-3.1.4 (bettercaves)

## Resolution
Client file ops (remove ScalableLux, Embeddium, WDA trio; add the 9 combat/Covenant jars + current DrewCraft jar), then Prism-direct launch. Long-term fix: ship playtest_01 as the dev release so the launcher converges everything (in progress).
