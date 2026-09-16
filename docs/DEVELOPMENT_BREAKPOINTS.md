# DrewCraft V1 Development Breakpoints

**Rebased:** 2026-09-16

Earlier BP1-BP8 work built valuable strategic, release, server, and launcher machinery. The product scope has since been deliberately narrowed. Strategic gameplay is preserved for post-V1; release and launcher machinery remains directly applicable.

## BP-V1A — Focused profile convergence

Pass when the resolver, CI workflows, server build, launcher live release, and website all name the same `v1_survival_exploration` profile and deferred features default off.

## BP-V1B — Server and gameplay proof

Pass when the exact profile boots and restarts a server and a player can complete the focused smoke test: survival, vehicle, aircraft, Create, and an approved WDA dungeon.

## BP-V1C — Distribution and operations proof

Pass when clean Windows/macOS/Linux launcher tests, host deployment, update/repair, multiplayer soak, backup/restore, and rollback evidence are green.

## BP-V1D — Release

Pass when one exact tested candidate is promoted through the website aliases and tagged `1.0.0` with no V1-blocking issue.

At each breakpoint update `docs/CURRENT_BREAKPOINT.md` with the exact evidence and next action. Post-V1 systems do not block these breakpoints.
