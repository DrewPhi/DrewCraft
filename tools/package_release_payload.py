#!/usr/bin/env python3
"""Create a publishable DrewCraft release tree without rehosting provider files."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil

from release_contract import validate_manifest


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def package(layout: pathlib.Path, manifest_path: pathlib.Path, live_path: pathlib.Path,
            output: pathlib.Path, evidence_path: pathlib.Path | None = None) -> dict:
    manifest = validate_manifest(json.loads(manifest_path.read_text("utf-8")))
    live = json.loads(live_path.read_text("utf-8"))
    if live.get("packVersion") != manifest["packVersion"]:
        raise RuntimeError("live pointer and manifest packVersion disagree")
    if output.exists():
        shutil.rmtree(output)
    version_root = output / manifest["packVersion"]
    version_root.mkdir(parents=True)

    included = 0
    provider_omitted = 0
    for entry in manifest["files"]:
        origin = entry.get("origin", {}).get("type", "drewcraft_release")
        if origin == "provider":
            provider_omitted += 1
            continue
        if origin != "drewcraft_release":
            raise RuntimeError(f"unknown release origin for {entry['path']}: {origin}")
        source = layout / entry["side"] / entry["path"]
        if not source.is_file():
            raise RuntimeError(f"release layout missing DrewCraft-owned file: {entry['side']}:{entry['path']}")
        if source.stat().st_size != entry["size"] or sha256(source) != entry["sha256"]:
            raise RuntimeError(f"release layout hash mismatch: {entry['side']}:{entry['path']}")
        target = version_root / entry["side"] / entry["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        included += 1

    shutil.copy2(manifest_path, version_root / "release-manifest.json")
    shutil.copy2(live_path, output / "live.json")
    if evidence_path is not None:
        if not evidence_path.is_file():
            raise RuntimeError(f"release evidence missing: {evidence_path}")
        shutil.copy2(evidence_path, version_root / evidence_path.name)

    checksum_lines = []
    for path in sorted(p for p in output.rglob("*") if p.is_file() and p.name != "SHA256SUMS"):
        checksum_lines.append(f"{sha256(path)}  {path.relative_to(output).as_posix()}")
    (output / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="ascii")
    return {
        "packVersion": manifest["packVersion"],
        "includedDrewCraftFiles": included,
        "providerFilesOmitted": provider_omitted,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layout", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--live", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--evidence")
    args = parser.parse_args()
    result = package(
        pathlib.Path(args.layout), pathlib.Path(args.manifest), pathlib.Path(args.live),
        pathlib.Path(args.output), pathlib.Path(args.evidence) if args.evidence else None,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
