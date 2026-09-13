#!/usr/bin/env python3
"""Convert verified client/server pack trees into common/client/server release layout."""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import shutil


def digest(path: pathlib.Path) -> tuple[int, str]:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return path.stat().st_size, h.hexdigest()


def files(root: pathlib.Path) -> dict[str, pathlib.Path]:
    if not root.is_dir():
        raise RuntimeError(f"pack tree missing: {root}")
    return {p.relative_to(root).as_posix(): p for p in root.rglob("*") if p.is_file()}


def assemble(client_root: pathlib.Path, server_root: pathlib.Path, output: pathlib.Path) -> dict[str, int]:
    client = files(client_root)
    server = files(server_root)
    if output.exists():
        shutil.rmtree(output)
    for side in ("common", "client", "server"):
        (output / side).mkdir(parents=True, exist_ok=True)

    counts = {"common": 0, "client": 0, "server": 0}
    for rel in sorted(set(client) | set(server)):
        cp = client.get(rel)
        sp = server.get(rel)
        if cp is not None and sp is not None and digest(cp) == digest(sp):
            side, source = "common", cp
        else:
            if cp is not None:
                target = output / "client" / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(cp, target)
                counts["client"] += 1
            if sp is not None:
                target = output / "server" / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(sp, target)
                counts["server"] += 1
            continue
        target = output / side / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        counts[side] += 1
    return counts


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--client", default="build/pack/client")
    p.add_argument("--server", default="build/pack/server")
    p.add_argument("--output", default="build/release-layout")
    args = p.parse_args()
    counts = assemble(pathlib.Path(args.client), pathlib.Path(args.server), pathlib.Path(args.output))
    print(" ".join(f"{key}={value}" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
