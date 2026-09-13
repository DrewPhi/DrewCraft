#!/usr/bin/env python3
"""Build DrewCraft production strategic seeds from an offline pregeneration index.

Input is generated during world-build tooling, never on the live server. Each
structure record contains a bounding box and floor candidates collected while
the world is already being inspected. Core rule: horizontal center -> nearest
accessible interior floor candidate.
"""
from __future__ import annotations

import argparse
import json
import pathlib


def choose_core(structure: dict) -> dict:
    box = structure["boundingBox"]
    cx = (int(box["minX"]) + int(box["maxX"])) / 2.0
    cz = (int(box["minZ"]) + int(box["maxZ"])) / 2.0
    candidates = []
    for c in structure.get("floorCandidates", []):
        if not c.get("solidFloor", True) or int(c.get("airAbove", 2)) < 2:
            continue
        exposed = 1 if c.get("exposed", False) else 0
        distance2 = (float(c["x"]) - cx) ** 2 + (float(c["z"]) - cz) ** 2
        candidates.append((
            exposed,
            distance2,
            abs(float(c["y"]) - (box["minY"] + box["maxY"]) / 2.0),
            int(c["y"]), int(c["x"]), int(c["z"]), c,
        ))
    if not candidates:
        raise ValueError(f"{structure['structureId']}@{structure.get('anchor')} has no accessible core candidate")
    return min(candidates)[-1]


def build_seed_index(index: dict, mappings: dict, world_plan: dict) -> dict:
    mapping_by_id = {m["structureId"]: m for m in mappings["sources"]}
    sources = []
    for structure in index.get("structures", []):
        mapping = mapping_by_id.get(structure["structureId"])
        if not mapping:
            continue
        core = choose_core(structure)
        anchor = structure["anchor"]
        sources.append({
            "dimension": structure["dimension"],
            "structureId": structure["structureId"],
            "anchor": {"x": int(anchor["x"]), "y": int(anchor["y"]), "z": int(anchor["z"])},
            "core": {"x": int(core["x"]), "y": int(core["y"]) + 1, "z": int(core["z"])},
            "sourceClass": mapping["sourceClass"],
            "factionId": mapping["factionId"],
        })
    sources.sort(key=lambda s: (s["dimension"], s["structureId"], s["anchor"]["x"], s["anchor"]["z"]))
    identities = set()
    cores = set()
    for source in sources:
        identity = (source["dimension"], source["structureId"], source["anchor"]["x"], source["anchor"]["y"], source["anchor"]["z"])
        core = (source["dimension"], source["core"]["x"], source["core"]["y"], source["core"]["z"])
        if identity in identities:
            raise ValueError(f"duplicate source identity: {identity}")
        if core in cores:
            raise ValueError(f"duplicate source core: {core}")
        identities.add(identity)
        cores.add(core)

    herds = []
    for h in world_plan.get("strategicHerds", []):
        herds.append({
            "dimension": h["dimension"],
            "species": h["species"],
            "origin": h["origin"],
            "destination": h["destination"],
            "count": int(h["count"]),
            "speedBlocksPerSecond": float(h["speedBlocksPerSecond"]),
        })
    objectives = []
    for objective in world_plan.get("strategicObjectives", []):
        objectives.append({
            "id": objective["id"],
            "kind": objective["kind"],
            "dimension": objective["dimension"],
            "position": {"x": int(objective["position"]["x"]), "z": int(objective["position"]["z"])},
        })
    objectives.sort(key=lambda value: value["id"])

    terrain = index.get("terrain", {"cellSizeBlocks": 64, "cells": []})
    return {
        "schemaVersion": 1,
        "worldId": world_plan["worldId"],
        "worldRevision": int(world_plan["worldRevision"]),
        "sources": sources,
        "herds": herds,
        "objectives": objectives,
        "terrain": terrain,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--structure-index", required=True)
    p.add_argument("--mappings", required=True)
    p.add_argument("--world-plan", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    load = lambda path: json.loads(pathlib.Path(path).read_text("utf-8"))
    result = build_seed_index(load(args.structure_index), load(args.mappings), load(args.world_plan))
    pathlib.Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(
        f"sources={len(result['sources'])} herds={len(result['herds'])} "
        f"objectives={len(result['objectives'])} terrainCells={len(result['terrain']['cells'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
