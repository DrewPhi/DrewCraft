# HPC bulk generation (Bouchet) — operations plan

Goal: pregenerate the overworld toward ~150 GB total world size on Yale HPC
GPUs, then splice new regions into production. Production stays live and
untouched until the final splice.

## Ground rules

- The generator stack must be **byte-identical to production**: same seed
  (`-6008857613538391475`), same `drewcraft:terrain_diffusion_scale_3`
  level type, same TD jar family, same Linear writer, same mod set.
  Only the inference backend may differ (CUDA vs CPU), and only if the
  determinism gate below passes for it.
- Code/scripts/configs live in this repo; multi-GB binaries (JDK, app,
  model weights) travel by direct copy, never git.
- One writer per world directory, always. Parallelism comes from many
  small world copies (one per tile), merged at file granularity at the end.
- Scavenge partitions are fine: Chunky checkpoints per region on the shared
  filesystem, so a preempted tile job simply reruns its own tile.

## Staged layout on Bouchet (`~/diffusion_model_infinite_test`)

- `jdk/` — Temurin 21 (same build everywhere; no module dependency).
- `app/` — exact production release tree (mods/config/libraries/run.sh).
  Exactly one `terrain-diffusion-*-cpu/cuda.jar` sits in `app/mods`.
- `models/` — production's own Terrain Diffusion weights (identical by copy).
- `hpc/` — `hpc_chunky_tile.py` plus per-tile job files.
- `work-<tile>/` — disposable per-tile worlds (seed-identical, offline mode).
- `out/` — finished region files staged for transfer back.

## Gate 0 — determinism + throughput probe (required before bulk)

Slurm job `hpc-tile-test.sbatch` generates production region `r.-16.-1`
(x −8192…−7681, z −512…−1; fully generated, no player builds) and times it.
The region ships back; every one of its 1,024 chunk payloads is byte-compared
against production (`verify_region_conversion` tooling). PASS on all payloads
plus recorded seconds-per-region unlocks bulk and sizes it honestly.

## Bulk — tile fleet with chained dependencies

- Tile = N regions sized to fit a 6–12 h scavenge walltime (from Gate 0 timing).
- One Slurm array (or batched jobs) per tile set; each runs
  `hpc_chunky_tile.py` on its own world copy.
- Merge job with `--dependency=afterok:<array>` collects region files that
  production lacks (inventory diff), validates headers/slots, and stages
  `out/` for transfer. Nothing built-up is ever overwritten: missing-only.
- Transfer: compressed resumable rsync of `out/` (tens of GB), per-file
  hash check on arrival.

## Production splice (only downtime in the whole plan)

1. Confirm empty server, save, stop Minecraft + pregen.
2. Copy staged regions into `persistent/world/region/` (new files only).
3. Validate (`linear_slots` on every new file), boot, RCON readiness,
   `save-all`, health check, resume pregen.
4. Rollback = delete the staged files (world otherwise untouched) or full
   pinned-snapshot recovery; the hold is never lifted for this.

## Sizing note (150 GB target)

Current regions ≈ 11.8 GB over ≈ 300 km² of coverage. Bulk tiles are sized
from measured Gate-0 throughput, not estimates; the tile count for ~150 GB
is set after that measurement lands.
