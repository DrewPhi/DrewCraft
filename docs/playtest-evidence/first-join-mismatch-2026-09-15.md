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

## Resolution
Client file ops (remove ScalableLux, Embeddium, WDA trio; add the 9 combat/Covenant jars + current DrewCraft jar), then Prism-direct launch. Long-term fix: ship playtest_01 as the dev release so the launcher converges everything (in progress).
