"""BP9: DH LOD pregen is part of the production-world pipeline by default.

Chunky pregenerates the bounded world offline; DH PRE_EXISTING_ONLY then converts
those exact chunks to LODs (no double worldgen, visuals match the indexed
source/structure geography). The resulting world/data/DistantHorizons.sqlite
travels inside the world archive, so first-join clients pull ready-made LODs
instead of triggering server-side generation.
"""
import hashlib
import importlib.util
import json
import pathlib
import sys
import tarfile
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


world_bundle = load_module("world_bundle_under_test", "tools/world_bundle.py")


def minimal_world(path: pathlib.Path) -> pathlib.Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "level.dat").write_bytes(b"level")
    world_bundle.write_world_info(
        path,
        world_id="drewcraft-production",
        world_revision=1,
        generation_pack_version="drewcraft-worldgen-1",
        seed=123,
        pregen_radius_blocks=4096,
    )
    (path / world_bundle.SEED_INDEX).write_text(
        json.dumps({
            "schemaVersion": 1,
            "worldId": "drewcraft-production",
            "worldRevision": 1,
            "sources": [],
            "objectives": [{"id": "obj-1"}],
            "herds": [],
            "terrain": {"cellSizeBlocks": 64, "cells": []},
        }),
        encoding="utf-8",
    )
    return path


class DhCacheInfoTest(unittest.TestCase):
    def test_missing_cache_is_explicit_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            world = minimal_world(pathlib.Path(tmp) / "world")
            info = world_bundle.dh_cache_info(world)
            self.assertEqual({"present": False, "size": None, "sha256": None}, info)

    def test_present_cache_reports_size_and_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            world = minimal_world(pathlib.Path(tmp) / "world")
            payload = b"fake-dh-sqlite" * 100
            target = world / "data" / "DistantHorizons.sqlite"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            info = world_bundle.dh_cache_info(world)
            self.assertTrue(info["present"])
            self.assertEqual(len(payload), info["size"])
            self.assertEqual(hashlib.sha256(payload).hexdigest(), info["sha256"])

    def test_archive_carries_dh_cache_and_records_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            world = minimal_world(tmp_path / "world")
            payload = b"fake-dh-sqlite" * 100
            (world / "data").mkdir(parents=True, exist_ok=True)
            (world / "data" / "DistantHorizons.sqlite").write_bytes(payload)
            output = tmp_path / "world.tar.gz"
            metadata = world_bundle.create_archive(world, output)
            self.assertTrue(metadata["dhCache"]["present"])
            self.assertEqual(len(payload), metadata["dhCache"]["size"])
            with tarfile.open(output, "r:gz") as tf:
                names = tf.getnames()
            self.assertIn("world/data/DistantHorizons.sqlite", names)

    def test_archive_without_cache_records_absence(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            world = minimal_world(tmp_path / "world")
            output = tmp_path / "world.tar.gz"
            metadata = world_bundle.create_archive(world, output)
            self.assertFalse(metadata["dhCache"]["present"])
            self.assertIsNone(metadata["dhCache"]["sha256"])


class DhPipelineWiringTest(unittest.TestCase):
    def test_production_driver_exposes_dh_pregen_step(self):
        text = (ROOT / "tools/build_production_world.py").read_text("utf-8")
        self.assertIn("--dh-pregen-command", text)
        self.assertIn("--dh-pregen-mode", text)
        self.assertIn("PRE_EXISTING_ONLY", text)
        self.assertIn("--require-dh-cache", text)
        self.assertIn("dh_cache_info", text)
        self.assertIn("dhCachePresent", text)


if __name__ == "__main__":
    unittest.main()
