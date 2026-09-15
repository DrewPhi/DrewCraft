# Covenant pre-playtest checklist (first human session)

Exact build: record `playtest-0.1` manifest SHA + server artifact SHA here before inviting anyone.
Test world: 1000x1000-block border on the test server (owner C10); production size stays TBD in `world/production-world.plan.json`.
Artifacts: draft GitHub release, no public live.json (owner C11). Test-server address: TBD.
Client matrix: friends cover Windows + Apple Silicon Mac + Ubuntu/Linux (owner C12).
macOS signing: ad-hoc for playtest-0.1, paid Apple signing at RC (owner C14 confirmed).

## 1. Fresh install
- [ ] Windows clean install via DrewCraft bootstrapper, no manual Java/Prism/mods/configs
- [ ] Apple Silicon clean install; Ubuntu/Linux x86-64 clean install
- [ ] Microsoft login through Prism once; relaunch converges with no changes
- [ ] Corrupt one managed file; repair restores exact hash; incompatible server/client combo is refused

## 2. Join + fly + weather + radar
- [ ] Join server; TPS stable at spawn with Flightstone visible
- [ ] Drive a road vehicle, ride a Create train segment, fly a supported aircraft
- [ ] Enter a Project Atmosphere storm; handheld weather radar shows it; Create: Radars weather overlay agrees
- [ ] Ground radar needs real dish/controller + kinetic power + antenna height; coverage changes with terrain/site
- [ ] Cut radar power; clean loss; restore; clean recovery

## 3. Covenant loop
- [ ] Encounter Covenant patrol (skins visible); kill mobs; scripture fragment drops with named site + partial coordinates
- [ ] Combine X-only + Z-only fragments for one named site; rare full-coordinate drop accelerates but is never required
- [ ] Trigger army behavior; bounded waves; unload area; restart server; strength/casualties persist, never duplicate
- [ ] Clear a Source Core; site stays CLEARED after restart; deployed forces remain; no new launches; Flightstone marker activates; archive clue guaranteed
- [ ] Siege: open gate used first; sealed wall triggers bounded corridor breach; decorative/protected blocks survive

## 4. Herds + ecology
- [ ] Encounter wild herd at strategic location; interaction changes persistent herd state across restart
- [ ] Named/tamed/leashed/penned/farmed animals never absorbed; ordinary night/cave spawning, farms and spawners intact

## 5. Flak
- [ ] Fly over intact AA site: visible bursts near predicted track, altitude-sensitive, avoidable, bounded damage, zero block damage
- [ ] Destroy AA tower/controller or clear the site Source Core: coverage stops per site rules

## 6. Ops
- [ ] Restart server mid-combat; no duplicated groups, no resurrected sources, no restored casualties
- [ ] Install release A, create state, upgrade to B, force failure: application rolls back, world NOT rolled back
- [ ] Backup/restore to clean root; manifest mismatch rejected
- [ ] Record server MSPT p50/p95/p99, long ticks, CPU, heap/GC, disk I/O, network, save/backup duration, entity counts, scheduler/routing/materialization/siege/radar costs; client FPS/frame-time/memory per OS

## 7. Evidence to capture
- [ ] Server log with zero unexplained fatal registry/mixin/network/serialization errors
- [ ] Diagnostics snapshot: TPS, tick time, strategic groups, materialized mobs, routing work, herd/source counts, flak events, radar scans, chunk activity, memory, persistence ops
- [ ] Player notes on what felt wrong (feel/balance only — correctness issues go to the bug list, not the checklist)
