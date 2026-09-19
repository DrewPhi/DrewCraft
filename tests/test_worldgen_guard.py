from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile

import pytest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("worldgen_guard", ROOT / "infra/worldgen_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def test_prepares_scale_three_only_for_new_world():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        world = root / "world"
        world.mkdir()
        properties = root / "server.properties"
        properties.write_text("level-type=drewcraft\\:terrain_diffusion_scale_3\n", encoding="utf-8")
        assert "prepared" in guard.verify(world, properties, prepare=True)
        assert guard.read_nbt(world / "data" / guard.SCALE_FILE)["data"]["scale"] == 3
        assert "already prepared" in guard.verify(world, properties, prepare=True)


def test_rejects_normal_world_even_when_properties_are_correct():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        world = root / "world"
        world.mkdir()
        properties = root / "server.properties"
        properties.write_text("level-type=minecraft\\:normal\n", encoding="utf-8")
        with pytest.raises(RuntimeError, match="level-type"):
            guard.verify(world, properties, prepare=True)
        properties.write_text("level-type=drewcraft\\:terrain_diffusion_scale_3\n", encoding="utf-8")
        (world / "region").mkdir()
        with pytest.raises(RuntimeError, match="generated chunks"):
            guard.verify(world, properties, prepare=True)


def test_dedicated_preset_matches_upstream_scale_three():
    preset = ROOT / "mods/drewcraft/src/main/resources/data/drewcraft/worldgen/world_preset/terrain_diffusion_scale_3.json"
    import json
    overworld = json.loads(preset.read_text("utf-8"))["dimensions"]["minecraft:overworld"]
    assert overworld["type"] == guard.DIMENSION
    assert overworld["generator"]["biome_source"]["type"] == guard.BIOME_SOURCE
