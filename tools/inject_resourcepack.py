#!/usr/bin/env python3
"""Inject the repository-authored Covenant resource pack into the verified
client pack tree.

The art source of truth is assets/resourcepacks/drewcraft_cult_first_pass.
The six PNGs must ship at their exact Illager Invasion override paths, or
cult mobs render in upstream skins. Recorded into the client layout before
release-layout assembly so it cannot be omitted silently.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import struct

PACK_ID = "drewcraft_cult_first_pass"
SOURCE = pathlib.Path(__file__).resolve().parents[1] / "assets" / "resourcepacks" / PACK_ID

EXPECTED_SKINS = [
    "assets/illagerinvasion/textures/entity/archivist.png",
    "assets/illagerinvasion/textures/entity/basher.png",
    "assets/illagerinvasion/textures/entity/firecaller.png",
    "assets/illagerinvasion/textures/entity/inquisitor.png",
    "assets/illagerinvasion/textures/entity/invoker.png",
    "assets/illagerinvasion/textures/entity/necromancer.png",
]


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def png_size(path: pathlib.Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) < 33:
        raise RuntimeError(f"not a valid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def inject(client_root: pathlib.Path, source: pathlib.Path = SOURCE) -> list[dict]:
    if not (source / "pack.mcmeta").is_file():
        raise RuntimeError(f"resource pack source is missing pack.mcmeta: {source}")
    layout_path = client_root / "drewcraft-layout.json"
    if not layout_path.is_file():
        raise RuntimeError(f"verified pack layout is missing: {layout_path}")
    layout = json.loads(layout_path.read_text("utf-8"))
    if layout.get("schema_version") != 1:
        raise RuntimeError("unsupported verified-pack layout schema")

    entries = []
    for rel in ["pack.mcmeta", *EXPECTED_SKINS]:
        src = source / rel
        if not src.is_file():
            raise RuntimeError(f"Covenant skin missing from source pack: {rel}")
        if src.suffix == ".png" and png_size(src) != (64, 64):
            raise RuntimeError(f"Covenant skin must stay 64x64: {rel}")
        dest_rel = f"resourcepacks/{PACK_ID}/{rel}"
        if any(e.get("path") == dest_rel for e in layout.get("files", [])):
            raise RuntimeError(f"resource pack already represented in {layout_path}: {dest_rel}")
        dest = client_root / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        entries.append({
            "id": f"covenant_resourcepack:{rel}",
            "path": dest_rel,
            "sha256": sha256(dest),
            "size": dest.stat().st_size,
            "source": "repository_art",
        })
    files = layout.setdefault("files", [])
    files.extend(entries)
    files.sort(key=lambda item: (item.get("path", ""), item.get("id", "")))
    layout_path.write_text(json.dumps(layout, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", default="build/verified-pack/client")
    parser.add_argument("--source", default=str(SOURCE))
    args = parser.parse_args()
    entries = inject(pathlib.Path(args.client), pathlib.Path(args.source))
    print(json.dumps({"injected": len(entries), "pack": PACK_ID}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
