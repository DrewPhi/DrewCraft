# DrewCraft Pack Manifests

This directory is the machine-readable dependency source of truth for DrewCraft.

## Files

- `upstreams.yaml` — discovery/ownership registry. Records official source repositories, current 1.21.1/NeoForge candidates, provider IDs, licensing notes, dependencies, and fork policy. **Candidates here are not automatically approved pack versions.**
- `mods.yaml` — future authoritative locked mod set produced after the compatibility gate.
- `content-packs.yaml` — future authoritative locked content-pack set produced after the compatibility gate.
- `pack.yaml` — future pack identity/platform/schema/version definition.
- `java.yaml` — future managed Java runtime definitions for launcher/server packaging.

## Promotion flow

```text
research/discover upstream
        ↓
upstreams.yaml candidate
        ↓
allowed-provider download
        ↓
SHA-256 + dependency resolution
        ↓
Stage 2 compatibility matrix
        ↓
license/acquisition validation
        ↓
mods.yaml / content-packs.yaml lock
        ↓
client + server pack build
```

Do not manually copy a jar into a release and treat it as locked.

Do not create a DrewCraft fork merely to simplify downloading or packaging. Forks are for maintained source changes; see `docs/UPSTREAM_DEPENDENCIES.md`.

The eventual resolver must fail closed if an acquired artifact does not match the locked SHA-256.
