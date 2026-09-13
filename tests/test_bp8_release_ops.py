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


release_contract = load_module("release_contract", "tools/release_contract.py")
serverctl = load_module("serverctl", "infra/serverctl.py")
launcher = load_module("drewcraft_bootstrap", "launcher/drewcraft_bootstrap.py")
world_index = load_module("world_seed_index", "tools/world_seed_index.py")
world_bundle = load_module("world_bundle", "tools/world_bundle.py")
release_layout = load_module("assemble_release_layout", "tools/assemble_release_layout.py")


class Bp8ReleaseOperationsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="drewcraft-bp8-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def build_release(self, version="0.8.0-test", generation_pack_version="worldgen-v1"):
        publish = self.tmp / "publish"
        layout = publish / version
        (layout / "common" / "mods").mkdir(parents=True)
        (layout / "client" / "config").mkdir(parents=True)
        (layout / "server" / "config").mkdir(parents=True)
        (layout / "common" / "mods" / "shared.jar").write_bytes(b"shared-v1")
        (layout / "client" / "config" / "client.txt").write_text("client\n", encoding="utf-8")
        (layout / "server" / "config" / "server.txt").write_text("server\n", encoding="utf-8")
        manifest = release_contract.build_manifest_from_layout(
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
            generation_pack_version=generation_pack_version,
            base_url=publish.as_uri(),
            server={"address": "example.invalid:25565"},
        )
        manifest_path = publish / version / "release-manifest.json"
        release_contract.write_manifest(manifest_path, manifest)
        live = release_contract.make_live_pointer("test", manifest_path.as_uri(), manifest)
        live_path = publish / "live.json"
        live_path.write_bytes(release_contract.canonical_json_bytes(live))
        return manifest, manifest_path, live_path

    def stamp_server_world(self, server_root, generation_pack_version="worldgen-v1", body=b"world-state"):
        world = server_root / "persistent" / "world"
        world.mkdir(parents=True, exist_ok=True)
        (world / "level.dat").write_bytes(body)
        (world / "drewcraft-world.json").write_text(json.dumps({
            "schemaVersion": 1,
            "worldId": "drewcraft-production",
            "worldRevision": 1,
            "generationPackVersion": generation_pack_version,
            "seed": 12345,
            "pregenRadiusBlocks": 4096,
        }, sort_keys=True) + "\n", encoding="utf-8")
        (world / "drewcraft-strategic-seeds.json").write_text(json.dumps({
            "schemaVersion": 1,
            "worldId": "drewcraft-production",
            "worldRevision": 1,
            "sources": [],
            "herds": [],
        }) + "\n", encoding="utf-8")
        return world

    def test_verified_client_server_trees_collapse_identical_files_to_common(self):
        client = self.tmp / "verified-client"
        server = self.tmp / "verified-server"
        for root in (client, server):
            (root / "mods").mkdir(parents=True)
            (root / "config").mkdir(parents=True)
            (root / "mods" / "shared.jar").write_bytes(b"same")
        (client / "config" / "side.txt").write_text("client\n", encoding="utf-8")
        (server / "config" / "side.txt").write_text("server\n", encoding="utf-8")
        (client / "client-only.txt").write_text("client only\n", encoding="utf-8")
        (server / "server-only.txt").write_text("server only\n", encoding="utf-8")

        output = self.tmp / "release-layout"
        counts = release_layout.assemble(client, server, output)
        self.assertEqual(b"same", (output / "common" / "mods" / "shared.jar").read_bytes())
        self.assertEqual("client\n", (output / "client" / "config" / "side.txt").read_text())
        self.assertEqual("server\n", (output / "server" / "config" / "side.txt").read_text())
        self.assertTrue((output / "client" / "client-only.txt").is_file())
        self.assertTrue((output / "server" / "server-only.txt").is_file())
        self.assertEqual({"common": 1, "client": 2, "server": 2}, counts)

    def test_one_manifest_drives_client_and_server_and_repairs_drift(self):
        manifest, _, live_path = self.build_release()
        app = self.tmp / "client-app"
        state = launcher.converge(live_path.as_uri(), app)
        self.assertEqual("0.8.0-test", state["packVersion"])
        client_root = app / "releases" / "0.8.0-test" / "instance"
        self.assertTrue((client_root / "mods" / "shared.jar").is_file())
        self.assertTrue((client_root / "config" / "client.txt").is_file())
        self.assertFalse((client_root / "config" / "server.txt").exists())
        self.assertEqual([], launcher.verify_local(app))

        (client_root / "mods" / "shared.jar").write_bytes(b"corrupt")
        self.assertEqual(["mods/shared.jar"], launcher.verify_local(app))
        launcher.converge(live_path.as_uri(), app)
        self.assertEqual([], launcher.verify_local(app))

        server_root = self.tmp / "server"
        self.stamp_server_world(server_root)
        result = serverctl.update_transaction(server_root, manifest)
        active = pathlib.Path(result["release"])
        self.assertTrue((active / "mods" / "shared.jar").is_file())
        self.assertTrue((active / "config" / "server.txt").is_file())
        self.assertFalse((active / "config" / "client.txt").exists())
        self.assertEqual([], release_contract.verify_tree(active, manifest, "server"))
        self.assertEqual(b"world-state", (server_root / "persistent" / "world" / "level.dat").read_bytes())

    def test_backup_checksum_clean_offhost_restore_and_world_bundle(self):
        manifest, _, _ = self.build_release()
        server_root = self.tmp / "server"
        world = self.stamp_server_world(server_root, body=b"abc123")
        (server_root / "persistent" / "strategic.marker").write_text("63 survivors\n", encoding="utf-8")
        archive = serverctl.backup(server_root, manifest, label="proof")
        self.assertTrue(archive.is_file())
        self.assertEqual(release_contract.sha256_file(archive), archive.with_suffix(archive.suffix + ".sha256").read_text("ascii").strip())
        offhost = self.tmp / "offhost-clean"
        serverctl.restore_backup(archive, offhost)
        self.assertEqual(b"abc123", (offhost / "persistent" / "world" / "level.dat").read_bytes())
        self.assertEqual("63 survivors\n", (offhost / "persistent" / "strategic.marker").read_text("utf-8"))

        world_archive = self.tmp / "world.tar.gz"
        world_bundle.create_archive(world, world_archive)
        restored = world_bundle.restore_archive(world_archive, self.tmp / "world-clean-restore")
        self.assertEqual(b"abc123", (restored / "level.dat").read_bytes())
        self.assertEqual("drewcraft-production", world_bundle.validate_world(restored)["worldId"])

    def test_failed_application_health_rolls_back_only_release_pointer(self):
        manifest1, _, _ = self.build_release("0.8.0-a")
        root = self.tmp / "server"
        self.stamp_server_world(root, body=b"irreversible-world")
        release1 = serverctl.stage_release(root, manifest1)
        serverctl.activate(root, release1, manifest1)

        manifest2, _, _ = self.build_release("0.8.0-b")
        with self.assertRaises(Exception):
            serverctl.update_transaction(root, manifest2, health_command="false")
        self.assertEqual(release1.resolve(), (root / "current").resolve())
        self.assertEqual(b"irreversible-world", (root / "persistent" / "world" / "level.dat").read_bytes())

    def test_incompatible_world_generation_is_rejected_before_activation(self):
        manifest, _, _ = self.build_release("0.8.0-b", generation_pack_version="worldgen-v2")
        root = self.tmp / "server"
        self.stamp_server_world(root, generation_pack_version="worldgen-v1")
        with self.assertRaisesRegex(RuntimeError, "world/release mismatch"):
            serverctl.update_transaction(root, manifest)
        self.assertFalse((root / "current").exists())

    def test_offline_structure_index_uses_center_nearest_interior_candidate(self):
        plan = {
            "worldId": "drewcraft-production",
            "worldRevision": 1,
            "strategicHerds": [{
                "dimension": "minecraft:overworld", "species": "minecraft:cow",
                "origin": {"x": 0, "z": 0}, "destination": {"x": 2048, "z": 0},
                "count": 80, "speedBlocksPerSecond": 1.25,
            }],
        }
        mappings = {"sources": [{"structureId": "minecraft:pillager_outpost", "sourceClass": "CAMP", "factionId": "drewcraft:raiders"}]}
        index = {"structures": [{
            "dimension": "minecraft:overworld", "structureId": "minecraft:pillager_outpost",
            "anchor": {"x": 100, "y": 64, "z": 100},
            "boundingBox": {"minX": 90, "maxX": 110, "minY": 60, "maxY": 85, "minZ": 90, "maxZ": 110},
            "floorCandidates": [
                {"x": 100, "y": 84, "z": 100, "solidFloor": True, "airAbove": 2, "exposed": True},
                {"x": 101, "y": 65, "z": 100, "solidFloor": True, "airAbove": 2, "exposed": False},
                {"x": 95, "y": 65, "z": 95, "solidFloor": True, "airAbove": 2, "exposed": False},
            ],
        }]}
        result = world_index.build_seed_index(index, mappings, plan)
        self.assertEqual(1, len(result["sources"]))
        self.assertEqual({"x": 101, "y": 66, "z": 100}, result["sources"][0]["core"])
        self.assertEqual(1, len(result["herds"]))


if __name__ == "__main__":
    unittest.main()
