# AOT / Paradis integration

Updated: 2026-09-26. Release: **0.1.10-dev-local**, owner-authorized rollout.
The owner explicitly elected to perform remaining gameplay acceptance on the
real server instead of continuing automated/interactive development testing.
Check the live health endpoint/channel for deployment completion; this document
does not by itself prove the rollout completed.

## Release evidence and owner test handoff

Deployment completed at 2026-09-27 03:15 UTC (September 26 local time):
Oracle reported `Done`, the AOT isolation hook active, RCON ready, and
`joinable=true` on 0.1.10-dev-local. The existing pregen controller restarted;
its retained checkpoint is `safety_paused` at the existing 125-expansion cap,
with 18,232,998,067 world bytes. No new terrain generation is running and this
release did not raise that cap. The health message "Pregeneration active" is
generic controller status, not evidence that Chunky currently has a task.
Pre-update Restic snapshot: `d0305258`; receipt
`20260927T031440722159Z.restic.json` (23,317,238 added bytes).
Immutable manifest SHA-256:
`405825d26ab5db2267ee4b88878eac450f3cc0f834b01bb10ebf5e776145344f`.
Release source commit: `357b19d2633a0e234e3c0afa5ddc47febeb471ae`.
No dock was placed during deployment; the owner placed one afterward (below).
No local test processes remain running.
The initial Pack manifests CI failure was a stale test requiring the old V1.1
profile name in the live-release workflow; its expectation is updated to the
approved Paradis profile. No shipped artifact changed for that test correction.

- Full dedicated-server mod stack booted; a development client joined the local
  multiplayer server and completed AOT configuration and Sable authentication.
- Dimension-scoped selectors confirmed Titans absent in Overworld/Nether/End
  and present in Paradis. The automatic dock-registration hook was active.
- The Java suite passed before the final dock helper; the final helper compiled.
  The complete release resolves 55 dependencies and both sides passed exact
  artifact-hash verification. No further interactive tests were run after the
  owner requested they stop.
- **Not verified:** portal round trip, successful return registration, actual ODM use,
  shifting/travel/reconnect edge cases, special-UUID command interception in a
  live player session, and gameplay performance. These are not passed gates.
- Production world revision 3 and Terrain Diffusion scale 3 are retained.
  Back up before activation. No dock is automatically placed by this release.

### Actual production dock — owner placed

- Logged placement: **2026-09-27 03:30:44 UTC** (September 26 local time).
- Dimension: `minecraft:overworld`, existing world revision 3.
- **Foundation origin: X -736, Y 57, Z -180; facing south.** This is the
  actual logged position, not the earlier suggested (-736,56,-179) command.
- Owner's shoreline reference: **(-713,63,-180)**, ocean directly south.
- Template footprint: X -736 through -689, Z -180 through -146;
  deck/portal block layer Y 64. Portal markers are approximately X -713/-712,
  Z -153/-152 (template-derived coordinates, not separately surveyed).
- The server logged successful upstream placement, immediately followed by
  DrewCraft's **`IllegalStateException: Dock return registration failed`**.
  The owner sees the dock and portal. A subsequent read-only check found no
  saved `world/data/dannys_aot_portals.dat` yet; that alone does not establish
  whether in-memory registration exists or will persist.
- Owner entered in Creative and reported **"return works all good"**. This is
  owner-confirmed round-trip evidence, not proof of registration persistence
  after restart. The command's registration warning still needs investigation.
- Do not place a duplicate dock. Investigate/repair registration for this dock.
- Supersedes the provisional (-2104,64,-1976) site, which the owner identified
  as a narrow river-like waterway despite its saved ocean biome label.

### ODM flight-kick setting

The owner reported Minecraft's flying-disabled kick while using ODM. The
repository template already had `allow-flight=true`, but the persistent live
`server.properties` retained `false`. On 2026-09-27 UTC this persistent setting
was changed to `true` and the server restarted. The setting disables vanilla's
flight kick; it does not grant players Creative flight. No client update is
needed. The preceding properties file was retained server-side as a private
settings backup; do not commit its contents (it includes the RCON credential).

### One-time dock guide

Installed on the live world on 2026-09-27 UTC: server-only datapack
`pack/world_datapacks/drewcraft-welcome`. A hidden vanilla advancement grants
each player one **A Passage to Paradis** written book with the dock entrance
coordinates X -713, Z -180 and deck Y 64. Existing players receive it after
installation; new players receive it on first join. Vanilla advancement records
prevent repeat grants after death, reconnect or restart (unless an administrator
resets those records). Full inventories drop the reward beside the player.
No client/application release change or terrain regeneration is required.

Operational evidence: `/reload` completed, `/datapack list enabled` listed
`file/drewcraft-welcome`, and the online player's `drewcraft_welcome:dock_guide`
completion selector matched. The new datapack had no reported parsing errors;
the reload also reported unrelated upstream optional Railways/WDA data errors.
See the datapack README for deliberate replacement-book administration.

### Dock placement command reference (do not place another production dock)

Administrator permission level 4 (or server console) is required:

`/drewcraft aot dock <foundation-x> <foundation-y> <foundation-z> <south|west|north|east>`

The coordinates identify the template foundation corner, **not the portal**.
The template is 48×20×35; its deck/portal is seven blocks above the foundation.
Facing south extends +X/+Z; west rotates clockwise, north 180°, east
counterclockwise. The provisional (-2104,64,-1976) location is a scouting point,
not a validated placement command: inspect local water height and the footprint.
Load the footprint by visiting it first. The helper refuses unloaded chunks,
out-of-bounds placement, existing solid blocks/block entities, or any already
registered dock. It invokes upstream placement, which skips template air,
activates portal markers and persists the return registration. A failed
post-placement check is logged; inspect the world before retrying.
Do not use vanilla `/place template`: that omits AOT's additional setup.

After placement, check both portal directions, gear in the Overworld, Titan
shifting only in Paradis, and reconnecting. Report coordinates and symptoms if
anything fails; do not remove AOT jars from a world containing AOT saved data.

## Approved experience

One manually placed Overworld dock at the actual location recorded above.
Access is immediately available to all players. No
additional natural AOT docks/structures in existing or future Overworld chunks.
ODM and ordinary AOT equipment work everywhere. Titans, transformations, AOT
mobs and events belong only in Paradis. Preserve the existing Overworld and its
Terrain Diffusion settings; do not reset it or target Paradis with idle pregen.
The provisional site, shore and spawn are recorded in `FURTHER_IDEAS.md`.

## Exact isolated test inputs

Minecraft 1.21.1 / NeoForge 21.1.250 / Java 21. Official Modrinth version IDs:

| Component | Version ID | Artifact version |
| --- | --- | --- |
| Danny's AOT | `p2GQ0M4J` | 2.4.3 |
| Sinytra Connector | `IITF0PRC` | 2.0.0-beta.17+1.21.1 |
| Forgified Fabric API | `V9WdDUTx` | 0.116.15+2.3.5+1.21.1 |
| Connector Extras | `dgLCqZyo` | 1.12.1+1.21.1 |
| GeckoLib (NeoForge) | `lWsXauBN` | 4.8.3 |
| AAA Particles (NeoForge) | `jeuOZqpO` | 1.21-1.4.7 |
| Player Animation Library (NeoForge) | `yjxtkvnD` | 1.1.6+mc.1.21.1 |

Downloaded artifacts were checked against their provider SHA-512 values during
the investigation. Before promotion, put these identities and hashes into the
normal resolver/lock machinery, not a separately maintained live mod directory.
AOT jar SHA-256:
`7f858305c996cbc2c2bd5c43e614e15b7187b29baf3f3591860c73bf5ac842b5`.
The official 2.4.3 artifact reports 2.4.1 internally in `fabric.mod.json`;
do not silently replace the artifact or edit its metadata to hide this.

GeckoLib must move from the shipping 4.8.2 to at least 4.8.3 for this candidate.
Player Animation Library is distinct from the existing KosmX playeranimator;
do not remove the latter as an assumed duplicate.

## Evidence and findings

- The minimal seven-artifact test server reached `Done (0.679s)` on a disposable
  flat world and initialized Paradis. This proves basic dedicated-server loading
  through Connector, **not** full DrewCraft compatibility, client rendering,
  multiplayer joining or containment. Test log: locally under
  `/tmp/drewcraft-aot-audit/server/logs/latest.log` (temporary, not tracked).
- `OverworldDocksGenerator.register()` subscribes to chunk-load and server-tick
  events. It can place docks retroactively in already-generated terrain. A
  normal structure-set datapack alone does not disable this. Prevent the
  registration before any production world loads, with a tested fail-closed
  compatibility hook for this exact artifact.
- Upstream template `dannys-aot:docks1` is not the whole placement operation.
  Upstream placement converts a template marker to a portal and registers the
  dock in `PortalLocationTracker`. Plain `/place template` is not yet a verified
  substitute. Check template dimensions, orientation, portal position, return
  destination and persisted registration before live placement.
- Paradis also has an upstream companion `dannys-aot:paths` dimension. Retain
  its registry while evaluating progression; do not delete it as an assumed
  unused dimension. The agreed Titan restriction still allows only Paradis.
- Natural Titan spawning being dimension-limited is insufficient. Audit direct
  shift packets, creative/operator paths, forced shifts, syringe injection,
  pending transformations, explosion effects, entity transfers and reconnects.
  A gamerule check alone does not cover all of these paths.
- This artifact also contains non-AOT superhero powers and `/daot danny`
  commands. `DannyAccess` grants access to specific hard-coded player UUIDs
  independently of normal operator permission. This is a concrete permission
  policy concern on an open server, not evidence of a compromised host or
  remote code execution. The owner approved blocking these privileges.

## Approved additional permission policy

Keep the ordinary survival AOT experience, but deny the special `/daot danny`
command group on DrewCraft and do not enable its superhero powers. No operator,
console or hard-coded UUID exemption. `AotCommandRuntime` cancels commands using
the NeoForge server event; a required vanilla `ExecuteCommand` mixin also checks
queued/function execution, which does not always pass through that event.
`AotCommandPolicy` examines parsed Brigadier nodes, including nested/redirected
and flattened execution contexts. Normal `/daot shifter` and bloodline
commands retain their upstream permission checks. This does not modify the
transformation keybind or upstream integrity/protected classes. Unit coverage
includes direct, namespaced, alias and nested execute paths, ordinary commands,
chat text and absence of AOT. All four focused JUnit tests and the complete
108-test Java suite passed with pinned Gradle 9.2.1. The minimal AOT server booted
with the compiled restriction and successfully ran ordinary and nested commands
and `/daot shifter check`. Console `/daot danny vanish` was rejected by upstream
permissions; that is **not** proof of interception for a hard-coded privileged
player. Testing that account-permission scenario and function execution in the
actual candidate runtime remains a release gate;
command denial alone does not prove dimension containment or disable powers
already granted through other mechanisms.

The bundled license permits good-faith non-commercial compatibility add-ons,
but prohibits circumventing its integrity measures. Do not redistribute the
decompiled source or a modified upstream jar. Confirm the official modpack
distribution route and attribution before packaging.

## Original acceptance checklist (remaining gameplay checks delegated to owner)

1. Permission policy approved; verify the implemented command restriction in
   the actual candidate runtime, including function execution.
2. Implement automatic-dock suppression and dimension containment with focused
   tests; failure to attach a required protection must prevent the candidate
   server from starting rather than silently permitting uncontrolled behavior.
3. Build an isolated full DrewCraft candidate with exact hashes and compiled
   DrewCraft integration on both client and server. Test Xaero, Create/Sable,
   GeckoLib-dependent content and the Connector compatibility bridges.
4. Prove no AOT mobs or transformations in Overworld/Nether/End, equipment use
   everywhere, pending-shift travel safety, Paradis gameplay, portal round-trip,
   logout/login and save/restart. Measure resource impact.
5. Validate the single dock footprint in saved chunks without overwriting
   player work. Back up before live placement; preserve return registration.
6. Publish a new immutable pack version only after the gates pass. Stage,
   verify, back up and activate the same manifest on the server; publish the
   client channel only once its referenced artifacts exist. Plan rollback for
   players and items saved in AOT dimensions; never blindly remove the mod from
   a world that has started using its registries.

Official project references:
[Danny's AOT](https://modrinth.com/mod/dannys-aot),
[CurseForge project](https://www.curseforge.com/minecraft/mc-mods/dannys-aot),
[Sinytra Connector](https://github.com/Sinytra/Connector).
