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
