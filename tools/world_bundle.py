#!/usr/bin/env python3
"""Create and verify immutable DrewCraft production-world archives."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import tarfile
import tempfile

WORLD_INFO = "drewcraft-world.json"
SEED_INDEX = "drewcraft-strategic-seeds.json"


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_world_info(world: pathlib.Path, *, world_id: str, world_revision: int,
                     generation_pack_version: str, seed: int, pregen_radius_blocks: int) -> dict:
    if world_revision < 1:
        raise ValueError("worldRevision must be positive")
    if pregen_radius_blocks < 1:
        raise ValueError("pregenRadiusBlocks must be positive")
    info = {
        "schemaVersion": 1,
        "worldId": world_id,
        "worldRevision": world_revision,
        "generationPackVersion": generation_pack_version,
        "seed": seed,
        "pregenRadiusBlocks": pregen_radius_blocks,
    }
    (world / WORLD_INFO).write_text(json.dumps(info, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return info


def validate_world(world: pathlib.Path) -> dict:
    if not (world / "level.dat").is_file():
        raise RuntimeError("world is missing level.dat")
    info_path = world / WORLD_INFO
    seed_path = world / SEED_INDEX
    if not info_path.is_file() or not seed_path.is_file():
        raise RuntimeError(f"world must contain {WORLD_INFO} and {SEED_INDEX}")
    info = json.loads(info_path.read_text("utf-8"))
    seeds = json.loads(seed_path.read_text("utf-8"))
    if info.get("schemaVersion") != 1 or seeds.get("schemaVersion") != 1:
        raise RuntimeError("unsupported world/seed schema")
    if info.get("worldId") != seeds.get("worldId") or info.get("worldRevision") != seeds.get("worldRevision"):
        raise RuntimeError("world identity and strategic seed identity disagree")
    return info


def create_archive(world: pathlib.Path, output: pathlib.Path) -> dict:
    info = validate_world(world)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as tf:
        tf.add(world, arcname="world")
    digest = sha256_file(output)
    metadata = {
        "schemaVersion": 1,
        "world": info,
        "archive": output.name,
        "size": output.stat().st_size,
        "sha256": digest,
    }
    output.with_suffix(output.suffix + ".sha256").write_text(digest + "\n", encoding="ascii")
    output.with_suffix(output.suffix + ".json").write_text(
        json.dumps(metadata, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def restore_archive(archive: pathlib.Path, destination: pathlib.Path) -> pathlib.Path:
    checksum = archive.with_suffix(archive.suffix + ".sha256")
    if not checksum.is_file():
        raise RuntimeError("world archive checksum is missing")
    expected = checksum.read_text("ascii").strip()
    got = sha256_file(archive)
    if got != expected:
        raise RuntimeError(f"world archive hash mismatch expected={expected} got={got}")
    if destination.exists() and any(destination.iterdir()):
        raise RuntimeError("restore destination must be empty")
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tf:
        base = destination.resolve()
        for member in tf.getmembers():
            resolved = (destination / member.name).resolve()
            if base not in resolved.parents and resolved != base:
                raise RuntimeError("unsafe path in world archive")
        tf.extractall(destination)
    world = destination / "world"
    validate_world(world)
    return world


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    stamp = sub.add_parser("stamp")
    stamp.add_argument("world")
    stamp.add_argument("--world-id", required=True)
    stamp.add_argument("--world-revision", type=int, required=True)
    stamp.add_argument("--generation-pack-version", required=True)
    stamp.add_argument("--seed", type=int, required=True)
    stamp.add_argument("--pregen-radius-blocks", type=int, required=True)
    bundle = sub.add_parser("bundle")
    bundle.add_argument("world")
    bundle.add_argument("--output", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("world")
    restore = sub.add_parser("restore")
    restore.add_argument("archive")
    restore.add_argument("--destination", required=True)
    args = p.parse_args()

    if args.command == "stamp":
        print(json.dumps(write_world_info(
            pathlib.Path(args.world), world_id=args.world_id,
            world_revision=args.world_revision, generation_pack_version=args.generation_pack_version,
            seed=args.seed, pregen_radius_blocks=args.pregen_radius_blocks,
        ), sort_keys=True))
    elif args.command == "bundle":
        print(json.dumps(create_archive(pathlib.Path(args.world), pathlib.Path(args.output)), sort_keys=True))
    elif args.command == "verify":
        print(json.dumps(validate_world(pathlib.Path(args.world)), sort_keys=True))
    elif args.command == "restore":
        print(restore_archive(pathlib.Path(args.archive), pathlib.Path(args.destination)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
