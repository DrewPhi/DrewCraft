# V1 hardening audit disposition

**Updated:** 2026-09-13

This records the implementation pass approved before production-world generation. It does not
claim evidence that can only come from generating and playing the final world.

## Completed in code

- Shipping, local-development, full-profile, and dedicated-server workflows now build the combined
  `source_structures_first_spike` profile, not the base-only profile.
- The built-in source-worldgen datapack remains the sole WDA allow-list: five retained structures
  keep their original dungeon mobs/loot while every other WDA structure set is disabled.
- Ancient cities are no longer silently repurposed as undead factories.
- A standard-library Anvil/NBT indexer now produces generated structure bounds, accessible interior
  Source Core candidates, and a 64-block coarse terrain-cost grid.
- A resumable production-world driver indexes, stamps, validates, archives, hashes, and clean-restores
  a generated world and emits a candidate report.
- Candidate locking now enforces numeric source, source-class, herd, explicit-objective, terrain-cell,
  duplicate, and boundary gates in addition to measured operations and human review.
- Production seed import validates the complete document before mutation, loads terrain costs before
  routing, imports explicit objectives, rejects duplicate records, and clears process-local state
  between integrated/dedicated server lifecycles.
- Patrols, hordes, and herds repeat their known route. Raids and armies stop at their destination.
  Scouted raids/armies require a reviewed production objective and never query or randomly discover a
  player location.
- Strategic, materialization, source, and siege schedulers rotate bounded work fairly. Source route
  planning also has a wall-clock budget.
- Tactical spawns require collision clearance and are persistence-protected. Siege classification
  refuses to tunnel common natural hillside materials.
- MTS wind-frame mutation restores original motion if the pre-force bridge fails and reports a
  compatibility failure once instead of silently swallowing it.
- Launcher downloads stream to disk, retain resumable partials, expose aggregate progress, support
  cancellation, validate runtime markers/executables, and skip all pack/Prism rebuilding when an
  installed manifest is already exact.
- Server application defaults to online mode with an enforced whitelist. Health `ready` now requires
  the Minecraft TCP listener. Updates stop Minecraft before backup; disk headroom, retention, and an
  optional second backup destination are supported.

## Still requires real-world evidence

- Generate candidate worlds and choose the final seed/radius.
- After visual inspection, enter at least four herd corridors and one explicit settlement/objective;
  empty lists intentionally cannot pass the candidate gate.
- Measure genuine generation, backup, restart, restore, disk, and archive values. The driver never
  fabricates missing measurements.
- Run the combined gameplay scenarios on the OCI A1 2 OCPU / 12 GB host and record `PASS` or
  `MIGRATE`.
- Perform an actual off-host recovery drill and friend-machine Windows/macOS/Linux launch tests.

No post-V1 endgame systems or additional gameplay/performance mods were added in this pass.

## Verification at handoff

- `python3 -m pytest -q`: **39 passed**.
- Python `compileall`: passed.
- Pinned Gradle 9.2.1: dependency/Minecraft preparation reached `transformSources`, then the run was
  intentionally interrupted before Java compile/JUnit. Resume command and exact next work are in
  `docs/CURRENT_BREAKPOINT.md`; this document does not claim that gate passed.
