# DrewCraft pack tooling

The Stage 1 resolver is fail-closed. Candidate profiles may resolve as a dependency graph while some provider identities are still incomplete, but no release lock/build may claim an artifact is exact until provider identity and SHA-256 are known.

```bash
python -m pip install -r tools/requirements-pack.txt
python tools/drewcraft_pack.py validate --profile stage2_base_performance
python tools/drewcraft_pack.py plan --profile stage2_base_performance --output build/plan.json
```

For CurseForge entries with unresolved file IDs, set `CURSEFORGE_API_KEY` and hydrate provider metadata:

```bash
python tools/drewcraft_pack.py hydrate --profile stage2_base_performance --output build/hydrated.json
```

Then fetch exact provider artifacts and compute hashes:

```bash
python tools/drewcraft_pack.py fetch --profile stage2_base_performance --hydration build/hydrated.json --output build/fetched.json
```

`fetch` exits non-zero if even one artifact cannot be acquired exactly.

Once all selected artifacts are fetched:

```bash
python tools/drewcraft_pack.py build --lock build/fetched.json --target client
python tools/drewcraft_pack.py build --lock build/fetched.json --target server
python tools/drewcraft_pack.py verify build/pack/client
python tools/drewcraft_pack.py verify build/pack/server
```

Candidate registries are not release lockfiles. Exact provider identities and hashes are promoted into future `mods.yaml` / `content-packs.yaml` only after compatibility gates pass.

## Production world

The resumable production-world driver runs generation (or accepts an already generated world),
reads Anvil region files without launching Minecraft, creates strategic source/core and terrain
indexes, stamps the world, bundles it, and proves a clean restore:

```bash
python tools/build_production_world.py --world /path/to/world --seed 12345 --radius 4096 --generation-command '/path/to/server-generation-script'
```

Progress is recorded in `build/production-world/state.json`; rerunning the same command resumes
after the last completed expensive phase. It writes a deliberately failing draft candidate report
at `build/production-world/candidate-report.json`. Fill the measured backup/restart fields, select
reviewed herd corridors and at least one explicit settlement/objective in
`world/production-world.plan.json`, then record the three human review decisions. Locking remains
fail-closed until the numeric source/class/herd/objective/terrain thresholds also pass.

For indexing alone:

```bash
python tools/extract_world_index.py --world /path/to/world --radius 4096 --output build/world-index.json
```
