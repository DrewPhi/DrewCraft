# Current error: duplicate managed path blocks all friend installs

## Symptom (Windows + macOS launchers)

```
duplicate managed path in release manifest: drewcraft-layout.json
```

Both the Windows and macOS launchers fail in `validate_manifest`
(`launcher/drewcraft_bootstrap.py:155`) right after fetching the dev
release manifest. (macOS first hit an unrelated TLS error, fixed in
`acafcf6`; it now reaches this same manifest error, which proves the TLS
fix works.)

## Live manifest (broken)

- Channel: <https://drewphi.github.io/DrewCraft/live.json> → `0.1.1-dev-local`
- Manifest: <https://drewphi.github.io/DrewCraft/dev/releases/0.1.1-dev-local/release-manifest.json>
- Proof: 38 files, `drewcraft-layout.json` listed **twice**
  (once with `side: client`, once with `side: server`).

## Root cause (fixed in repo, commits `9262e8a`, `acafcf6`)

`tools/assemble_release_layout.py` keeps each pack tree's own
`drewcraft-layout.json`, so the assembled layout contains
`client/drewcraft-layout.json` **and** `server/drewcraft-layout.json`.
`tools/release_contract.py::build_manifest_from_layout` listed both as
managed files under the same path. Fix: layout files are builder
metadata and are now excluded from manifests, plus a fail-closed
duplicate-path check and a regression test
(`tests/test_bp8_release_ops.py::test_layout_files_are_builder_metadata_not_managed_paths`).
Suite: 59 passed, 11 subtests.

## Fixed payload (verified, ready to publish)

- CI run `34922945519` (workflow `local-dev-release.yml`, manual dispatch
  after the fix), artifact **`DrewCraft-local-dev-publish`**: pack
  `0.1.0-dev-local`, 40 files, **zero duplicates** (checked).
- The artifact is self-consistent: its `live.json` already points at
  `dev/releases/0.1.0-dev-local/release-manifest.json` with matching
  `manifestSha256` (`bd2077a9…00fed5d`). Do not hand-edit it.

## What the Pages agent must do

Nothing in `DrewPhi/DrewCraft` deploys to the Pages site; that happens
from outside this repo. Publish the fixed payload:

1. `gh run download 34922945519 -n DrewCraft-local-dev-publish -D ./devpublish`
2. Copy `./devpublish/0.1.0-dev-local/` → `<pages-repo>/dev/releases/0.1.0-dev-local/`
3. Copy `./devpublish/live.json` → `<pages-repo>/live.json`
   (re-points the channel at the fixed manifest; also copy `SHA256SUMS`
   alongside if the site keeps them).
4. Commit + push the pages repo, wait ~1 min for Pages deploy.

Note: the channel version will read `0.1.0-dev-local` (lower than the
stale `0.1.1`), but the content is newer. No client has anything
installed yet, so no migration concern.

## Verify from anywhere

```bash
python -c "import json,urllib.request; m=json.load(urllib.request.urlopen('https://drewphi.github.io/DrewCraft/dev/releases/0.1.0-dev-local/release-manifest.json')); from collections import Counter; c=Counter(e['path'] for e in m['files']); print(len(m['files']), [k for k,v in c.items() if v>1])"
```

Expected: `40 []`. Then both friends just re-run their launchers
(no reinstall needed).
