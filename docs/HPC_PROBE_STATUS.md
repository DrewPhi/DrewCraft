# Bouchet GPU probe — 2026-10-05

Owner authorized repairing the small GPU determinism/throughput probe before
considering bulk world/DH generation. Defective pending job 28421985 cancelled;
corrected replacement submitted as **28423266**, same scavenge/L40S allocation,
pi_sk2433 account, normal QoS, 16 CPUs, 64 GB, 12-hour limit.

Remote root: `~/diffusion_model_infinite_test/`. Runner
`hpc/hpc_chunky_tile.py`, submission `hpc-tile-w1.sbatch`, output
`work-tile-w1/runner.log` and `work-tile-w1/result.json`. Original scripts retained
under `before-fix-28421985` names. Existing work directories are never overwritten.

Probe center changed to -7936,-256, square radius 800. This encloses production
region `r.-16.-1.linear`, independently confirmed present with 1024 occupied
slots; the previous center targeted absent region r.-26.-1. Seed matches live
level.dat: -6008857613538391475, DrewCraft scale-3 preset. All 53 non-Terrain
Diffusion mod hashes match live rc.2; only CPU/CUDA TD artifact differs.

Runner now copies accepted EULA, pinned models, defaultconfigs, integration
files and all bundled world datapacks. Explorer binds locally. Boot/generation
fail promptly on process exit; forced shutdown rejects output. Results appear
in both Slurm stdout and runner.log, and explicitly mark comparison NOT_RUN.
Local Python compilation, shell syntax and remote dependency/preflight checks
passed. Production has no world/serverconfig overrides beyond readme.txt;
production/bundle TD overlap settings agree (`inference.window_overlap=full`).

Next: require successful clean generation, verify actual saved world seed,
generator and FULL chunk coverage, confirm CUDA use, then compare decoded
chunk NBT/payloads with production region. Raw region bytes may differ from
compression, timestamps and ordinary server ticking; report exact differences
and never claim bitwise equality from matching seeds alone. GPU/CPU output
parity is unproven. No native DH pregen or 150/200 GB loop is configured yet.
Bulk generation/import must preserve existing production/player/world state,
avoid overwriting existing regions and budget combined world+DH+backup storage.
