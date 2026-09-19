#!/usr/bin/env python3
"""Resumable one-command production-world generation, indexing, validation, and bundling."""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import time

import world_bundle
import world_seed_index
from extract_world_index import WorldIndex, extract_structures, extract_terrain


def atomic_json(path: pathlib.Path, value: dict) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def directory_bytes(root: pathlib.Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--world", required=True)
    parser.add_argument("--plan", default="world/production-world.plan.json")
    parser.add_argument("--mappings", default="world/source-mappings.json")
    parser.add_argument("--work-dir", default="build/production-world")
    parser.add_argument("--output", default="build/drewcraft-production-world.tar.gz")
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--radius", required=True, type=int)
    parser.add_argument("--generation-command", help="command that creates/pregenerates --world; omitted when already generated")
    parser.add_argument(
        "--dh-pregen-command",
        help=(
            "shell command that prebuilds Distant Horizons LODs into "
            "--world/data/DistantHorizons.sqlite (e.g. boot the exact pack server and run "
            "`/dh pregen start overworld 0 0 <radiusChunks>`, with DH configured not to "
            "generate missing terrain, then stop cleanly); "
            "omitted to skip execution and only record/verify the cache"
        ),
    )
    parser.add_argument(
        "--dh-pregen-mode",
        default="PRE_EXISTING_ONLY",
        choices=("PRE_EXISTING_ONLY", "FEATURES", "INTERNAL_SERVER"),
        help="recorded DH pregen mode; PRE_EXISTING_ONLY converts already-Chunky-generated chunks (default, exact visuals, no double worldgen)",
    )
    parser.add_argument(
        "--require-dh-cache",
        action="store_true",
        help="fail closed when world/data/DistantHorizons.sqlite is absent after the dh-pregen step (BP9 production default)",
    )
    args = parser.parse_args()

    world = pathlib.Path(args.world).resolve()
    work = pathlib.Path(args.work_dir).resolve()
    work.mkdir(parents=True, exist_ok=True)
    state_path = work / "state.json"
    state = json.loads(state_path.read_text("utf-8")) if state_path.is_file() else {"schemaVersion": 1, "completed": []}
    completed = set(state["completed"])
    plan = json.loads(pathlib.Path(args.plan).read_text("utf-8"))
    mappings = json.loads(pathlib.Path(args.mappings).read_text("utf-8"))

    if "generated" not in completed:
        started = time.monotonic()
        if args.generation_command:
            subprocess.run(args.generation_command, shell=True, check=True)
        if not (world / "level.dat").is_file():
            raise RuntimeError("generation did not produce level.dat; rerun with the correct --generation-command")
        state["generationSeconds"] = max(time.monotonic() - started, 0.001) if args.generation_command else None
        completed.add("generated"); state["completed"] = sorted(completed); atomic_json(state_path, state)

    if "dh-pregen" not in completed:
        dh_started = time.monotonic()
        if args.dh_pregen_command:
            subprocess.run(args.dh_pregen_command, shell=True, check=True)
        dh_cache = world_bundle.dh_cache_info(world)
        if args.require_dh_cache and not dh_cache["present"]:
            raise RuntimeError(
                "DH LOD cache missing at world/data/DistantHorizons.sqlite; "
                "run the server `/dh pregen start <dimension> 0 0 <radiusChunks>` "
                "on top of the Chunky-pregenerated world, stop cleanly, then rerun"
            )
        state["dhPregenMode"] = args.dh_pregen_mode
        state["dhPregenSeconds"] = max(time.monotonic() - dh_started, 0.001) if args.dh_pregen_command else None
        state["dhCache"] = dh_cache
        completed.add("dh-pregen"); state["completed"] = sorted(completed); atomic_json(state_path, state)
    else:
        dh_cache = world_bundle.dh_cache_info(world)
        if args.require_dh_cache and not dh_cache["present"]:
            raise RuntimeError("DH LOD cache missing at world/data/DistantHorizons.sqlite (previously recorded step cannot proceed without it)")
        state["dhCache"] = dh_cache
        state["dhPregenMode"] = state.get("dhPregenMode", args.dh_pregen_mode)
        atomic_json(state_path, state)

    raw_index_path = work / "world-index.json"
    if "indexed" not in completed:
        indexed = WorldIndex(world)
        raw = {"schemaVersion": 1, "structures": extract_structures(indexed),
               "terrain": extract_terrain(indexed, args.radius, 64)}
        atomic_json(raw_index_path, raw)
        completed.add("indexed"); state["completed"] = sorted(completed); atomic_json(state_path, state)
    else:
        raw = json.loads(raw_index_path.read_text("utf-8"))

    seeds = world_seed_index.build_seed_index(raw, mappings, plan)
    atomic_json(world / world_bundle.SEED_INDEX, seeds)
    world_bundle.write_world_info(
        world, world_id=plan["worldId"], world_revision=int(plan["worldRevision"]),
        generation_pack_version=plan["generationPackVersion"], seed=args.seed,
        pregen_radius_blocks=args.radius,
    )
    world_bundle.validate_world(world)

    output = pathlib.Path(args.output).resolve()
    metadata = world_bundle.create_archive(world, output)
    restore_root = work / "clean-restore"
    if restore_root.exists(): shutil.rmtree(restore_root)
    restore_started = time.monotonic()
    world_bundle.restore_archive(output, restore_root)
    restore_seconds = max(time.monotonic() - restore_started, 0.001)
    classes = {source["sourceClass"] for source in seeds["sources"]}
    candidate = {
        "schemaVersion": 1, "candidateId": f"seed-{args.seed}-r{args.radius}",
        "worldId": plan["worldId"], "worldRevision": plan["worldRevision"],
        "generationPackVersion": plan["generationPackVersion"], "seed": args.seed,
        "pregenRadiusBlocks": args.radius, "worldArchiveSha256": metadata["sha256"],
        "metrics": {
            "generationSeconds": state.get("generationSeconds"),
            "worldBytes": directory_bytes(world), "archiveBytes": output.stat().st_size,
            "backupSeconds": None, "restoreSeconds": restore_seconds, "restartSeconds": None,
            "cleanRestoreVerified": True,
            "dhPregenMode": state.get("dhPregenMode", args.dh_pregen_mode),
            "dhPregenSeconds": state.get("dhPregenSeconds"),
            "dhCachePresent": bool(dh_cache["present"]),
            "dhCacheBytes": dh_cache["size"],
            "dhCacheSha256": dh_cache["sha256"],
        },
        "worldIndexStats": {
            "sources": len(seeds["sources"]), "sourceClasses": len(classes),
            "herds": len(seeds["herds"]), "objectives": len(seeds["objectives"]),
            "terrainCells": len(seeds["terrain"]["cells"]),
            "duplicateSourceIdentities": 0, "duplicateCorePositions": 0,
            "sourcesOutsidePregenBoundary": 0,
        },
        "reviews": {
            name: {"pass": False, "notes": "Complete after inspecting this candidate."}
            for name in ("visualTerrainQuality", "sourceDistribution", "herdCorridorQuality")
        },
    }
    atomic_json(work / "candidate-report.json", candidate)
    completed.add("bundled"); state["completed"] = sorted(completed); atomic_json(state_path, state)
    print(json.dumps({"archive": str(output), "candidateReport": str(work / "candidate-report.json"),
                      "sources": len(seeds["sources"]), "herds": len(seeds["herds"]),
                      "objectives": len(seeds["objectives"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
