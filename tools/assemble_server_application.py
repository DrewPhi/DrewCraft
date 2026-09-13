#!/usr/bin/env python3
"""Assemble a complete immutable DrewCraft server application tree.

The NeoForge installer output supplies run.sh/libraries. The verified DrewCraft
server pack supplies the exact managed mods/config payload. Persistent world/logs
are intentionally absent; serverctl wires those at activation time.
"""
from __future__ import annotations

import argparse
import pathlib
import shutil

RESERVED = {"world", "logs"}


def _files(root: pathlib.Path):
    return sorted(p for p in root.rglob("*") if p.is_file())


def assemble(runtime_root: pathlib.Path, pack_root: pathlib.Path, output: pathlib.Path) -> dict[str, int]:
    if not (runtime_root / "run.sh").is_file():
        raise RuntimeError("NeoForge runtime is missing run.sh")
    if not (runtime_root / "libraries").is_dir():
        raise RuntimeError("NeoForge runtime is missing libraries/")
    if not (pack_root / "mods").is_dir():
        raise RuntimeError("verified server pack is missing mods/")
    for reserved in RESERVED:
        if (runtime_root / reserved).exists() or (pack_root / reserved).exists():
            raise RuntimeError(f"input contains reserved persistent path: {reserved}")

    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(runtime_root, output)

    # Runtime installers may leave an empty/default mods directory. The verified
    # pack is authoritative for managed mods, so replace it completely.
    target_mods = output / "mods"
    if target_mods.exists():
        shutil.rmtree(target_mods)
    shutil.copytree(pack_root / "mods", target_mods)

    # Overlay any additional verified server-managed files (configs, datapacks,
    # DrewCraft layout evidence) without allowing persistent world/log ownership.
    for source in _files(pack_root):
        rel = source.relative_to(pack_root)
        if rel.parts[0] == "mods":
            continue
        target = output / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    # The production host has 12 GB total in the initial A1 target. Keep enough
    # headroom for OS/native libraries rather than allocating the full machine.
    jvm_args = output / "user_jvm_args.txt"
    jvm_args.write_text("-Xms4G\n-Xmx8G\n", encoding="utf-8")
    (output / "eula.txt").write_text("eula=true\n", encoding="utf-8")
    (output / "server.properties").write_text(
        "white-list=true\n"
        "enforce-whitelist=true\n"
        "enforce-secure-profile=true\n"
        "online-mode=true\n",
        encoding="utf-8",
    )
    return {
        "runtimeFiles": len(_files(runtime_root)),
        "packFiles": len(_files(pack_root)),
        "applicationFiles": len(_files(output)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--pack", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    counts = assemble(pathlib.Path(args.runtime), pathlib.Path(args.pack), pathlib.Path(args.output))
    print(" ".join(f"{key}={value}" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
