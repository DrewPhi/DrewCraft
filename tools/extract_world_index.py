#!/usr/bin/env python3
"""Extract structures, safe Source Core candidates, and coarse terrain from a pregenerated world.

This is an offline Anvil/NBT reader. It never starts Minecraft or loads chunks and uses only the
Python standard library, so a finished Chunky world can be indexed on any build machine.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import math
import pathlib
import struct
import zlib


class NbtReader:
    def __init__(self, payload: bytes):
        self.stream = io.BytesIO(payload)

    def read(self, fmt: str):
        size = struct.calcsize(">" + fmt)
        data = self.stream.read(size)
        if len(data) != size:
            raise ValueError("truncated NBT")
        return struct.unpack(">" + fmt, data)[0]

    def string(self) -> str:
        return self.stream.read(self.read("H")).decode("utf-8")

    def payload(self, tag: int):
        if tag == 1: return self.read("b")
        if tag == 2: return self.read("h")
        if tag == 3: return self.read("i")
        if tag == 4: return self.read("q")
        if tag == 5: return self.read("f")
        if tag == 6: return self.read("d")
        if tag == 7: return [self.read("b") for _ in range(self.read("i"))]
        if tag == 8: return self.string()
        if tag == 9:
            item_tag, size = self.read("b"), self.read("i")
            return [self.payload(item_tag) for _ in range(size)]
        if tag == 10:
            value = {}
            while True:
                child = self.read("b")
                if child == 0: return value
                name = self.string()
                value[name] = self.payload(child)
        if tag == 11: return [self.read("i") for _ in range(self.read("i"))]
        if tag == 12: return [self.read("q") for _ in range(self.read("i"))]
        raise ValueError(f"unsupported NBT tag {tag}")

    def root(self) -> dict:
        if self.read("b") != 10:
            raise ValueError("NBT root is not a compound")
        self.string()
        return self.payload(10)


def read_region(path: pathlib.Path):
    with path.open("rb") as stream:
        locations = stream.read(4096)
        for slot in range(1024):
            location = int.from_bytes(locations[slot * 4:slot * 4 + 3], "big")
            if not location:
                continue
            stream.seek(location * 4096)
            length = int.from_bytes(stream.read(4), "big")
            compression = stream.read(1)[0]
            external = bool(compression & 0x80)
            compression &= 0x7f
            if external:
                raise ValueError(f"external Anvil chunks are not supported: {path} slot {slot}")
            payload = stream.read(length - 1)
            if compression == 1: payload = gzip.decompress(payload)
            elif compression == 2: payload = zlib.decompress(payload)
            elif compression != 3: raise ValueError(f"unknown Anvil compression {compression}")
            root = NbtReader(payload).root()
            yield root.get("Level", root)


def _palette_name(entry) -> str:
    return str(entry.get("Name", "minecraft:air")) if isinstance(entry, dict) else "minecraft:air"


class Chunk:
    def __init__(self, nbt: dict):
        self.x = int(nbt["xPos"])
        self.z = int(nbt["zPos"])
        self.sections = {int(s["Y"]): s for s in nbt.get("sections", []) if isinstance(s, dict) and "Y" in s}
        self.heightmaps = nbt.get("Heightmaps", {})
        self.structures = nbt.get("structures", nbt.get("Structures", {}))

    def block(self, x: int, y: int, z: int) -> str:
        section = self.sections.get(y // 16)
        states = section.get("block_states", section.get("BlockStates", {})) if section else {}
        palette = states.get("palette", section.get("Palette", [])) if section else []
        if not palette: return "minecraft:air"
        if len(palette) == 1: return _palette_name(palette[0])
        data = states.get("data", section.get("BlockStates", []))
        bits = max(4, (len(palette) - 1).bit_length())
        per_long = 64 // bits
        index = ((y & 15) * 16 + (z & 15)) * 16 + (x & 15)
        word = int(data[index // per_long]) & ((1 << 64) - 1)
        palette_index = (word >> ((index % per_long) * bits)) & ((1 << bits) - 1)
        return _palette_name(palette[palette_index]) if palette_index < len(palette) else "minecraft:air"

    def surface_y(self, x: int, z: int) -> int | None:
        data = self.heightmaps.get("WORLD_SURFACE", self.heightmaps.get("WORLD_SURFACE_WG"))
        if not data: return None
        min_y = min(self.sections, default=-4) * 16
        max_y = (max(self.sections, default=19) + 1) * 16
        bits = max(1, (max_y - min_y + 1).bit_length())
        index = (z & 15) * 16 + (x & 15)
        bit = index * bits
        word_index, shift = divmod(bit, 64)
        value = (int(data[word_index]) & ((1 << 64) - 1)) >> shift
        if shift + bits > 64 and word_index + 1 < len(data):
            value |= (int(data[word_index + 1]) & ((1 << 64) - 1)) << (64 - shift)
        return min_y + (value & ((1 << bits) - 1)) - 1


class WorldIndex:
    def __init__(self, world: pathlib.Path):
        self.chunks: dict[tuple[str, int, int], Chunk] = {}
        roots = {
            "minecraft:overworld": world / "region",
            "minecraft:the_nether": world / "DIM-1" / "region",
            "minecraft:the_end": world / "DIM1" / "region",
        }
        for dimension, region in roots.items():
            if not region.is_dir(): continue
            for path in sorted(region.glob("r.*.*.mca")):
                for nbt in read_region(path):
                    chunk = Chunk(nbt)
                    self.chunks[(dimension, chunk.x, chunk.z)] = chunk

    def chunk(self, dimension: str, x: int, z: int) -> Chunk | None:
        return self.chunks.get((dimension, x // 16, z // 16))

    def block(self, dimension: str, x: int, y: int, z: int) -> str:
        chunk = self.chunk(dimension, x, z)
        return chunk.block(x, y, z) if chunk else "minecraft:air"


PASSABLE_BLOCKS = {
    "minecraft:air", "minecraft:cave_air", "minecraft:void_air", "minecraft:short_grass",
    "minecraft:tall_grass", "minecraft:fern", "minecraft:large_fern", "minecraft:vine",
    "minecraft:snow", "minecraft:dead_bush",
}
NON_FLOOR_FRAGMENTS = ("water", "lava", "torch", "rail")


def _is_passable(name: str) -> bool:
    return name in PASSABLE_BLOCKS


def _is_floor(name: str) -> bool:
    return not _is_passable(name) and not any(token in name for token in NON_FLOOR_FRAGMENTS)


def floor_candidates(world: WorldIndex, dimension: str, box: list[int], limit: int = 96) -> list[dict]:
    min_x, min_y, min_z, max_x, max_y, max_z = map(int, box)
    cx, cz = (min_x + max_x) / 2, (min_z + max_z) / 2
    columns = sorted(((x, z) for x in range(min_x, max_x + 1) for z in range(min_z, max_z + 1)),
                     key=lambda p: ((p[0] - cx) ** 2 + (p[1] - cz) ** 2, p[0], p[1]))
    result = []
    for x, z in columns:
        for y in range(max_y, min_y - 1, -1):
            floor = world.block(dimension, x, y, z)
            if not _is_floor(floor): continue
            if _is_passable(world.block(dimension, x, y + 1, z)) and _is_passable(world.block(dimension, x, y + 2, z)):
                result.append({"x": x, "y": y, "z": z, "solidFloor": True, "airAbove": 2,
                               "exposed": _is_passable(world.block(dimension, x, y + 3, z))})
                break
        if len(result) >= limit: break
    return result


def extract_structures(world: WorldIndex) -> list[dict]:
    result = []
    for (dimension, _, _), chunk in sorted(world.chunks.items()):
        starts = chunk.structures.get("starts", chunk.structures.get("Starts", {}))
        if not isinstance(starts, dict): continue
        for key, start in sorted(starts.items()):
            if not isinstance(start, dict) or str(start.get("id", key)).upper() == "INVALID": continue
            box = start.get("BB", start.get("bb"))
            if not isinstance(box, list) or len(box) != 6: continue
            # The map key is the configured structure ID. For jigsaw structures the
            # start's own id is merely "minecraft:jigsaw" and is not useful here.
            structure_id = str(key)
            result.append({
                "dimension": dimension,
                "structureId": structure_id,
                "anchor": {"x": chunk.x * 16, "y": int(box[1]), "z": chunk.z * 16},
                "boundingBox": {"minX": int(box[0]), "minY": int(box[1]), "minZ": int(box[2]),
                                "maxX": int(box[3]), "maxY": int(box[4]), "maxZ": int(box[5])},
                "floorCandidates": floor_candidates(world, dimension, box),
            })
    return result


def extract_terrain(world: WorldIndex, radius: int, cell_size: int) -> dict:
    cells = []
    lower, upper = math.floor(-radius / cell_size), math.floor(radius / cell_size)
    for cell_x in range(lower, upper + 1):
        for cell_z in range(lower, upper + 1):
            center_x, center_z = cell_x * cell_size + cell_size // 2, cell_z * cell_size + cell_size // 2
            points = [(center_x, center_z), (center_x - cell_size // 3, center_z),
                      (center_x + cell_size // 3, center_z), (center_x, center_z - cell_size // 3),
                      (center_x, center_z + cell_size // 3)]
            heights, blocks = [], []
            for x, z in points:
                chunk = world.chunk("minecraft:overworld", x, z)
                y = chunk.surface_y(x, z) if chunk else None
                if y is not None:
                    heights.append(y)
                    blocks.append(chunk.block(x, y, z))
            if not heights: terrain_class = "UNKNOWN"
            elif sum("water" in block for block in blocks) >= 3: terrain_class = "WATER"
            elif max(heights) - min(heights) >= 24: terrain_class = "DIFFICULT"
            else: terrain_class = "NORMAL"
            cells.append({"dimension": "minecraft:overworld", "x": cell_x, "z": cell_z,
                          "terrainClass": terrain_class})
    return {"cellSizeBlocks": cell_size, "cells": cells}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--world", required=True)
    parser.add_argument("--radius", required=True, type=int)
    parser.add_argument("--cell-size", type=int, default=64)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    world = WorldIndex(pathlib.Path(args.world))
    result = {"schemaVersion": 1, "structures": extract_structures(world),
              "terrain": extract_terrain(world, args.radius, args.cell_size)}
    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"chunks={len(world.chunks)} structures={len(result['structures'])} terrainCells={len(result['terrain']['cells'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
