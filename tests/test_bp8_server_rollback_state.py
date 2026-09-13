import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


release_contract = load_module("release_contract_rollback", "tools/release_contract.py")
sys.modules["release_contract"] = release_contract
serverctl = load_module("serverctl_rollback", "infra/serverctl.py")


class ServerRollbackStateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="drewcraft-bp8-rollback-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def manifest(self, version):
        publish = self.tmp / "publish"
        layout = publish / version
        (layout / "server").mkdir(parents=True)
        (layout / "server" / "run.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        return release_contract.build_manifest_from_layout(
            layout,
            pack_version=version,
            channel="test",
            protocol_version=7,
            minecraft_version="1.21.1",
            loader_id="neoforge",
            loader_version="21.1.250",
            minimum_launcher_version="0.1.0",
            world_id="drewcraft-production",
            world_revision=1,
            generation_pack_version="worldgen-v1",
            base_url=publish.as_uri(),
        )

    def world(self, root):
        world = root / "persistent" / "world"
        world.mkdir(parents=True, exist_ok=True)
        (world / "level.dat").write_bytes(b"authoritative-world")
        (world / "drewcraft-world.json").write_text(json.dumps({
            "schemaVersion": 1,
            "worldId": "drewcraft-production",
            "worldRevision": 1,
            "generationPackVersion": "worldgen-v1",
        }) + "\n", encoding="utf-8")

    def test_failed_upgrade_restores_pointer_active_metadata_and_health(self):
        root = self.tmp / "server"
        self.world(root)
        old = self.manifest("0.8.0-a")
        old_release = serverctl.stage_release(root, old)
        serverctl.activate(root, old_release, old)
        serverctl.write_health(root, "ready", old)

        new = self.manifest("0.8.0-b")
        with self.assertRaises(Exception):
            serverctl.update_transaction(root, new, health_command="false")

        self.assertEqual(old_release.resolve(), (root / "current").resolve())
        self.assertEqual(b"authoritative-world", (root / "persistent" / "world" / "level.dat").read_bytes())
        active = json.loads((root / "state" / "active-release.json").read_text("utf-8"))
        health = json.loads((root / "state" / "health.json").read_text("utf-8"))
        self.assertEqual("0.8.0-a", active["packVersion"])
        self.assertEqual(str(old_release.resolve()), active["releasePath"])
        self.assertEqual("ready", health["status"])
        self.assertEqual("0.8.0-a", health["packVersion"])
        self.assertIn("rolled back", health["message"])

    def test_failed_first_deployment_leaves_no_active_application(self):
        root = self.tmp / "server"
        self.world(root)
        new = self.manifest("0.8.0-first")
        with self.assertRaises(Exception):
            serverctl.update_transaction(root, new, health_command="false")

        self.assertFalse((root / "current").exists())
        self.assertFalse((root / "current").is_symlink())
        self.assertFalse((root / "state" / "active-release.json").exists())
        self.assertEqual(b"authoritative-world", (root / "persistent" / "world" / "level.dat").read_bytes())
        health = json.loads((root / "state" / "health.json").read_text("utf-8"))
        self.assertEqual("failed", health["status"])
        self.assertEqual("0.8.0-first", health["packVersion"])
        self.assertIn("no prior release", health["message"])


if __name__ == "__main__":
    unittest.main()
