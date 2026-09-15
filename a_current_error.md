# Current error status: RESOLVED — duplicate managed path

The friend-install blocker

```
duplicate managed path in release manifest: drewcraft-layout.json
```

has been resolved in both the DrewCraft release tooling and the published Pages development channel.

## Resolution

- Root-cause tooling fix: `drewcraft-layout.json` is builder metadata and is excluded from release manifests; duplicate managed paths fail closed.
- Verified source artifact: DrewCraft CI run `34922945519`, artifact `DrewCraft-local-dev-publish`.
- Pages publish: `DrewPhi/drewphi.github.io` workflow run `34924029764` completed successfully.
- Published development channel now points to `0.1.0-dev-local`.
- Published manifest SHA-256: `bd2077a94eb4f9107b07242aee0fd6309cf14f5ea16261e4f7ff2456e00fed5d`.
- Published manifest contains 40 managed files and no duplicate managed paths; `drewcraft-layout.json` is absent from the managed file list.

## Current live pointer

`https://drewphi.github.io/DrewCraft/live.json`

points to:

`https://drewphi.github.io/DrewCraft/dev/releases/0.1.0-dev-local/release-manifest.json`

Friends can re-run the current launcher; no reinstall is required for this particular error.

If another launcher/install failure appears, replace this file with the new current error rather than treating this resolved issue as active.
