#!/usr/bin/env python3
"""Seed and verify the exact dedicated-server Terrain Diffusion world identity.

The upstream world-creation screen records scale in SavedData and selects a
scale-specific dimension type. A dedicated server has no such screen, so both
pieces must be prepared before its first boot. Never rewrite an existing world.
"""
from __future__ import annotations

import argparse
import gzip
import os
from pathlib import Path
import struct
import tempfile

PRESET = "drewcraft:terrain_diffusion_scale_3"
DIMENSION = "terrain-diffusion-mc:terrain_diffusion_scale_3"
BIOME_SOURCE = "terrain-diffusion-mc:terrain_diffusion"
NOISE_SETTINGS = "terrain-diffusion-mc:terrain_diffusion"
SCALE = 3
SCALE_FILE = "terrain_diffusion_world_settings.dat"


class NbtReader:
    def __init__(self, data: bytes):
        self.data = memoryview(data)
        self.pos = 0

    def take(self, count: int) -> bytes:
        if count < 0 or self.pos + count > len(self.data):
            raise ValueError("truncated or invalid NBT")
        result = self.data[self.pos:self.pos + count].tobytes()
        self.pos += count
        return result

    def number(self, fmt: str):
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))[0]

    def string(self) -> str:
        return self.take(self.number(">H")).decode("utf-8")

    def payload(self, kind: int):
        if kind == 1:
            return self.number(">b")
        if kind == 2:
            return self.number(">h")
        if kind == 3:
            return self.number(">i")
        if kind == 4:
            return self.number(">q")
        if kind == 5:
            return self.number(">f")
        if kind == 6:
            return self.number(">d")
        if kind in (7, 11, 12):
            length = self.number(">i")
            width = {7: 1, 11: 4, 12: 8}[kind]
            self.take(length * width)
            return None
        if kind == 8:
            return self.string()
        if kind == 9:
            element = self.number(">B")
            length = self.number(">i")
            if length < 0 or length > 1_000_000:
                raise ValueError("invalid NBT list length")
            return [self.payload(element) for _ in range(length)]
        if kind == 10:
            out = {}
            while True:
                child = self.number(">B")
                if child == 0:
                    return out
                name = self.string()
                out[name] = self.payload(child)
        raise ValueError(f"unsupported NBT tag {kind}")


def read_nbt(path: Path) -> dict:
    reader = NbtReader(gzip.decompress(path.read_bytes()))
    if reader.number(">B") != 10:
        raise ValueError(f"{path}: NBT root is not a compound")
    reader.string()
    result = reader.payload(10)
    if reader.pos != len(reader.data):
        raise ValueError(f"{path}: trailing NBT data")
    return result


def _name(value: str) -> bytes:
    encoded = value.encode("utf-8")
    return struct.pack(">H", len(encoded)) + encoded


def scale_nbt() -> bytes:
    # Vanilla SavedData format: unnamed root compound, nested `data` compound.
    raw = bytearray(b"\x0a\x00\x00\x0a" + _name("data"))
    raw.extend(b"\x03" + _name("scale") + struct.pack(">i", SCALE))
    for key, value in (("explicit_settings", 1), ("explicit_scale", 1),
                       ("block_sources_below_775m", 0)):
        raw.extend(b"\x01" + _name(key) + struct.pack(">b", value))
    raw.extend(b"\x00")  # end data compound
    raw.extend(b"\x03" + _name("DataVersion") + struct.pack(">i", 3955))
    raw.extend(b"\x00")  # end root compound
    return gzip.compress(raw, mtime=0)


def _preset(properties: Path) -> str:
    for line in properties.read_text("utf-8").splitlines():
        if line.startswith("level-type="):
            return line.split("=", 1)[1].replace("\\:", ":")
    return "minecraft:normal"


def verify(world: Path, properties: Path, *, prepare: bool = False) -> str:
    if _preset(properties) != PRESET:
        raise RuntimeError(f"server level-type must be {PRESET}, not {_preset(properties)}")
    level = world / "level.dat"
    scale_file = world / "data" / SCALE_FILE
    if not level.is_file():
        if not prepare:
            raise RuntimeError("world has no level.dat yet; wait for Minecraft first boot")
        if any((world / name).exists() for name in ("region", "entities", "poi")):
            raise RuntimeError("world has generated chunks but no level.dat; refusing to seed scale")
        scale_file.parent.mkdir(parents=True, exist_ok=True)
        if scale_file.exists():
            try:
                settings = read_nbt(scale_file)["data"]
            except (OSError, KeyError, ValueError) as exc:
                raise RuntimeError("existing scale SavedData is invalid") from exc
            if settings.get("scale") != SCALE or settings.get("explicit_settings") != 1:
                raise RuntimeError("existing scale SavedData does not select World Scale 3")
            return "new Terrain Diffusion scale-3 world already prepared"
        fd, temp = tempfile.mkstemp(prefix=".scale-", dir=scale_file.parent)
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(scale_nbt())
            os.replace(temp, scale_file)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
        return "new Terrain Diffusion scale-3 world prepared"

    root = read_nbt(level)
    overworld = root["Data"]["WorldGenSettings"]["dimensions"]["minecraft:overworld"]
    generator = overworld["generator"]
    if (overworld["type"] != DIMENSION
            or generator["biome_source"]["type"] != BIOME_SOURCE
            or generator["settings"] != NOISE_SETTINGS):
        raise RuntimeError("saved Overworld is not the Terrain Diffusion scale-3 preset")
    if not scale_file.is_file():
        raise RuntimeError("Terrain Diffusion world scale SavedData is missing")
    settings = read_nbt(scale_file)["data"]
    if settings.get("scale") != SCALE or settings.get("explicit_settings") != 1:
        raise RuntimeError(f"Terrain Diffusion saved scale is not {SCALE}")
    return "saved Overworld generator and World Scale 3 verified"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--world", type=Path, default=Path("/srv/drewcraft/persistent/world"))
    parser.add_argument("--properties", type=Path,
                        default=Path("/srv/drewcraft/persistent/server.properties"))
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    print(verify(args.world, args.properties, prepare=args.prepare))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
