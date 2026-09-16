# DrewCraft Systems

## Active V1 systems

- **Release convergence:** one exact, side-aware manifest drives launcher and server content.
- **Launcher:** managed Java and Prism, authentication handoff, automatic instance launch, staged updates, repair, progress/rate/ETA, and user-data preservation.
- **Server operations:** immutable applications, persistent world/log separation, backups, health checks, atomic activation, and application rollback.
- **World stack:** Terrain Diffusion, Distant Horizons, controlled Chunky tooling, vanilla survival, and the WDA allow-list.
- **Mobility and engineering:** MTS vehicles/aircraft and the selected compatible Create family.
- **Diagnostics/performance:** conservative optimization stack plus Spark.

## Dormant post-V1 systems

The DrewCraft mod contains implemented adapters and strategic machinery for weather, radar coupling, strategic groups, sources, materialization, armies, sieges, and herds. These systems default off and are not required or activated by the V1 profile.

Their detailed contracts remain in the strategic/weather design documents linked from `docs/FURTHER_IDEAS.md`. Future activation requires a named release goal, compatibility/performance evidence, migration behavior, and explicit configuration.

## Failure isolation

- Missing deferred providers must fail closed, not prevent V1 boot.
- Deferred systems must perform no active simulation when disabled.
- A failed client update leaves the last verified installation usable.
- A failed server application update restores application identity without blindly restoring the world.
- World-generation identity changes require explicit compatibility handling.
