#!/usr/bin/env python3
"""Inject the repository-built DrewCraft mod into verified client/server pack trees.

The external pack lock intentionally describes upstream dependencies. DrewCraft's
own integration jar is built from this repository and then recorded into each
verified layout before release-layout assembly so it cannot be omitted silently.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import zipfile

NON_PRODUCTION_SUFFIXES = (
    "-sources.jar",
    "-source.jar",
    "-javadoc.jar",
    "-tests.jar",
    "-test.jar",
)


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inject(pack_root: pathlib.Path, jar: pathlib.Path, *, strip_worldgen: bool = False) -> dict:
    if not jar.is_file() or jar.suffix.lower() != ".jar":
        raise RuntimeError(f"DrewCraft production jar is missing: {jar}")
    layout_path = pack_root / "drewcraft-layout.json"
    if not layout_path.is_file():
        raise RuntimeError(f"verified pack layout is missing: {layout_path}")
    layout = json.loads(layout_path.read_text("utf-8"))
    if layout.get("schema_version") != 1:
        raise RuntimeError("unsupported verified-pack layout schema")

    rel = f"mods/{jar.name}"
    files = layout.setdefault("files", [])
    existing = [entry for entry in files if entry.get("path") == rel or entry.get("id") == "drewcraft_mod"]
    if existing:
        raise RuntimeError(f"DrewCraft mod is already represented in {layout_path}")

    destination = pack_root / rel
    destination.parent.mkdir(parents=True, exist_ok=True)
    if strip_worldgen:
        # The fast integration smoke intentionally omits Terrain Diffusion. A
        # production DrewCraft jar still contains the TD world presets, which
        # would make that CI-only profile fail registry loading before it can
        # test the integration migration itself.
        with zipfile.ZipFile(jar) as source, zipfile.ZipFile(destination, "w") as target:
            for info in source.infolist():
                if info.filename.startswith("data/drewcraft/worldgen/"):
                    continue
                target.writestr(info, source.read(info.filename))
    else:
        shutil.copy2(jar, destination)
    digest = sha256(destination)
    entry = {
        "id": "drewcraft_mod",
        "path": rel,
        "sha256": digest,
        "size": destination.stat().st_size,
        "source": "repository_build",
    }
    files.append(entry)
    files.sort(key=lambda item: (item.get("path", ""), item.get("id", "")))
    layout_path.write_text(json.dumps(layout, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return entry


def production_jar(libs: pathlib.Path) -> pathlib.Path:
    jars = [
        path for path in sorted(libs.glob("*.jar"))
        if not path.name.lower().endswith(NON_PRODUCTION_SUFFIXES)
    ]
    if len(jars) != 1:
        raise RuntimeError(f"expected exactly one DrewCraft production jar, got {[p.name for p in jars]}")
    return jars[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar")
    parser.add_argument("--libs", default="mods/drewcraft/build/libs")
    parser.add_argument("--client", default="build/verified-pack/client")
    parser.add_argument("--server", default="build/verified-pack/server")
    parser.add_argument(
        "--strip-worldgen",
        action="store_true",
        help="Remove DrewCraft Terrain Diffusion worldgen presets for CI-only no-TD smoke profiles.",
    )
    args = parser.parse_args()
    jar = pathlib.Path(args.jar) if args.jar else production_jar(pathlib.Path(args.libs))
    results = {
        "client": inject(pathlib.Path(args.client), jar, strip_worldgen=args.strip_worldgen),
        "server": inject(pathlib.Path(args.server), jar, strip_worldgen=args.strip_worldgen),
    }
    print(json.dumps(results, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
