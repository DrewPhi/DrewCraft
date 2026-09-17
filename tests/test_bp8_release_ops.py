import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
import unittest
import struct
from unittest import mock

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
# drewcraft_entry.py imports its sibling drewcraft_client_defaults module.
# Pre-register it so this module also passes in isolation instead of only
# when another test file happens to import first alphabetically.
load_module("drewcraft_client_defaults", "launcher/drewcraft_client_defaults.py")
launcher_entry = load_module("drewcraft_entry", "launcher/drewcraft_entry.py")
world_index = load_module("world_seed_index", "tools/world_seed_index.py")
world_bundle = load_module("world_bundle", "tools/world_bundle.py")
world_extract = load_module("extract_world_index", "tools/extract_world_index.py")
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

    def test_layout_files_are_builder_metadata_not_managed_paths(self):
        # Regression: client/ and server/ pack trees each carry their own
        # drewcraft-layout.json. The release manifest must list neither, or
        # Windows launchers fail with "duplicate managed path: drewcraft-layout.json".
        publish = self.tmp / "publish-dup"
        layout = publish / "0.8.0-dup"
        (layout / "client").mkdir(parents=True)
        (layout / "server").mkdir(parents=True)
        (layout / "client" / "drewcraft-layout.json").write_text('{"target": "client"}\n', encoding="utf-8")
        (layout / "server" / "drewcraft-layout.json").write_text('{"target": "server"}\n', encoding="utf-8")
        (layout / "client" / "mods").mkdir(parents=True)
        (layout / "client" / "mods" / "a.jar").write_bytes(b"a")
        manifest = release_contract.build_manifest_from_layout(
            layout,
            pack_version="0.8.0-dup",
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
        paths = [e["path"] for e in manifest["files"]]
        self.assertNotIn("drewcraft-layout.json", paths)
        self.assertEqual(len(paths), len(set(paths)))
        launcher.validate_manifest(manifest)

    def test_launcher_https_context_verifies(self):
        # Regression: macOS-bundled Python cannot see the system keychain, so
        # bare urlopen() dies with CERTIFICATE_VERIFY_FAILED on first launch.
        import ssl
        context = launcher._https_context()
        self.assertIsInstance(context, ssl.SSLContext)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertGreater(len(context.get_ca_certs()), 0)

    def test_archived_covenant_resource_pack_can_still_be_built_explicitly(self):
        inject_pack = load_module("inject_resourcepack", "tools/inject_resourcepack.py")
        client = self.tmp / "client-tree"
        client.mkdir(parents=True)
        (client / "drewcraft-layout.json").write_text(
            json.dumps({"schema_version": 1, "target": "client", "files": []}), encoding="utf-8")
        entries = inject_pack.inject(client)
        self.assertEqual(len(entries), 7)
        self.assertTrue((client / "resourcepacks/drewcraft_cult_first_pass/assets/illagerinvasion/textures/entity/basher.png").is_file())
        layout = json.loads((client / "drewcraft-layout.json").read_text(encoding="utf-8"))
        self.assertEqual(len(layout["files"]), 7)

    def test_focused_v1_removes_only_deprecated_managed_resource_pack(self):
        minecraft = self.tmp / "minecraft-focused-v1"
        old_pack = minecraft / "resourcepacks/drewcraft_cult_first_pass"
        user_pack = minecraft / "resourcepacks/my-pack"
        old_pack.mkdir(parents=True)
        user_pack.mkdir(parents=True)
        (old_pack / "pack.mcmeta").write_text("{}\n", encoding="utf-8")
        (user_pack / "pack.mcmeta").write_text("{}\n", encoding="utf-8")
        (minecraft / "options.txt").write_text(
            'resourcePacks:["vanilla","file/drewcraft_cult_first_pass","file/my-pack"]\n',
            encoding="utf-8",
        )

        launcher._remove_deprecated_managed_resource_packs(minecraft)

        self.assertFalse(old_pack.exists())
        self.assertTrue(user_pack.is_dir())
        active = json.loads((minecraft / "options.txt").read_text("utf-8").split(":", 1)[1])
        self.assertEqual(active, ["vanilla", "file/my-pack"])

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
            "objectives": [],
            "terrain": {"cellSizeBlocks": 64, "cells": []},
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

    def test_one_manifest_drives_client_server_real_prism_instance_and_repairs_drift(self):
        manifest, _, live_path = self.build_release()
        app = self.tmp / "client-app"
        state = launcher.converge(live_path.as_uri(), app)
        self.assertEqual("0.8.0-test", state["packVersion"])
        client_root = app / "releases" / "0.8.0-test" / "instance"
        self.assertTrue((client_root / "mods" / "shared.jar").is_file())
        self.assertTrue((client_root / "config" / "client.txt").is_file())
        self.assertFalse((client_root / "config" / "server.txt").exists())

        prism_instance = pathlib.Path(state["prismRoot"]) / "instances" / state["instanceId"]
        mmc = json.loads((prism_instance / "mmc-pack.json").read_text("utf-8"))
        self.assertEqual("1.21.1", mmc["components"][0]["version"])
        self.assertEqual("net.neoforged", mmc["components"][1]["uid"])
        self.assertEqual("21.1.250", mmc["components"][1]["version"])
        self.assertTrue((prism_instance / "instance.cfg").is_file())
        instance_cfg = (prism_instance / "instance.cfg").read_text(encoding="utf-8")
        self.assertIn("OverrideMemory=true", instance_cfg)
        self.assertIn("MinMemAlloc=8192", instance_cfg)
        self.assertIn("MaxMemAlloc=8192", instance_cfg)
        self.assertEqual([], launcher.verify_local(app))

        # Corruption in either the immutable local release cache or the actual Prism
        # instance must be detected and a normal converge/repair must restore it.
        (client_root / "mods" / "shared.jar").write_bytes(b"corrupt")
        self.assertEqual(["mods/shared.jar"], launcher.verify_local(app))
        launcher.converge(live_path.as_uri(), app)
        self.assertEqual([], launcher.verify_local(app))
        state = json.loads((app / "state.json").read_text("utf-8"))
        prism_instance = pathlib.Path(state["prismRoot"]) / "instances" / state["instanceId"]
        (prism_instance / "minecraft" / "mods" / "shared.jar").write_bytes(b"corrupt-prism")
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

    def test_up_to_date_converge_repairs_legacy_memory_settings(self):
        manifest, _, live_path = self.build_release()
        app = self.tmp / "client-app-mem"
        state = launcher.converge(live_path.as_uri(), app)
        prism_instance = pathlib.Path(state["prismRoot"]) / "instances" / state["instanceId"]
        # Simulate an instance created before managed memory: 4G cap, no override flag.
        cfg = prism_instance / "instance.cfg"
        legacy = cfg.read_text(encoding="utf-8")
        legacy = "\n".join(
            line for line in legacy.splitlines()
            if not line.startswith(("OverrideMemory=", "MinMemAlloc=", "MaxMemAlloc=", "MinMem=", "MaxMem="))
        ) + "\nMaxMemAlloc=4096\nMinMem=4096\n"
        cfg.write_text(legacy, encoding="utf-8")
        launcher.converge(live_path.as_uri(), app)
        repaired = cfg.read_text(encoding="utf-8")
        self.assertIn("OverrideMemory=true", repaired)
        self.assertIn("MinMemAlloc=8192", repaired)
        self.assertIn("MaxMemAlloc=8192", repaired)
        self.assertNotIn("MaxMemAlloc=4096", repaired)
        self.assertNotIn("MinMem=4096", repaired)

    def test_unchanged_launcher_converge_does_not_rebuild_prism_instance(self):
        _, _, live_path = self.build_release()
        app = self.tmp / "client-app"
        state = launcher.converge(live_path.as_uri(), app)
        marker = pathlib.Path(state["prismRoot"]) / "instances" / state["instanceId"] / "minecraft" / "user-marker.txt"
        marker.write_text("keep me\n", encoding="utf-8")
        with mock.patch.object(launcher, "install_pack", wraps=launcher.install_pack) as install:
            again = launcher.converge(live_path.as_uri(), app)
        self.assertEqual(state["instanceId"], again["instanceId"])
        self.assertEqual("keep me\n", marker.read_text("utf-8"))
        install.assert_not_called()

    def test_client_update_preserves_user_owned_data_between_atomic_version_instances(self):
        _, _, live_a = self.build_release("0.8.0-a")
        app = self.tmp / "client-app"
        state_a = launcher.converge(live_a.as_uri(), app)
        old_mc = pathlib.Path(state_a["prismRoot"]) / "instances" / state_a["instanceId"] / "minecraft"
        (old_mc / "screenshots").mkdir(parents=True)
        (old_mc / "screenshots" / "castle.png").write_bytes(b"player screenshot")
        (old_mc / "resourcepacks").mkdir(parents=True)
        (old_mc / "resourcepacks" / "mine.zip").write_bytes(b"resourcepack")
        (old_mc / "terrain-diffusion-models").mkdir(parents=True)
        (old_mc / "terrain-diffusion-models" / "base_model.onnx").write_bytes(b"cached model")
        (old_mc / "mods").mkdir(exist_ok=True)
        (old_mc / "mods" / "removed-from-manifest.jar").write_bytes(b"obsolete mod")
        (old_mc / "config").mkdir(exist_ok=True)
        (old_mc / "config" / "removed-from-manifest.toml").write_text("obsolete=true\n", encoding="utf-8")
        (old_mc / "options.txt").write_text("fov:0.5\n", encoding="utf-8")

        _, _, live_b = self.build_release("0.8.0-b")
        state_b = launcher.converge(live_b.as_uri(), app)
        self.assertNotEqual(state_a["instanceId"], state_b["instanceId"])
        new_mc = pathlib.Path(state_b["prismRoot"]) / "instances" / state_b["instanceId"] / "minecraft"
        self.assertEqual(b"player screenshot", (new_mc / "screenshots" / "castle.png").read_bytes())
        self.assertEqual(b"resourcepack", (new_mc / "resourcepacks" / "mine.zip").read_bytes())
        self.assertEqual(
            b"cached model",
            (new_mc / "terrain-diffusion-models" / "base_model.onnx").read_bytes(),
        )
        self.assertEqual("fov:0.5\n", (new_mc / "options.txt").read_text("utf-8"))
        self.assertFalse((new_mc / "mods" / "removed-from-manifest.jar").exists())
        self.assertFalse((new_mc / "config" / "removed-from-manifest.toml").exists())
        self.assertEqual([], launcher.verify_local(app))

    def test_launcher_minimum_version_is_enforced(self):
        manifest, _, _ = self.build_release()
        manifest["minimumLauncherVersion"] = "999.0.0"
        with self.assertRaisesRegex(RuntimeError, "launcher is too old"):
            launcher.validate_manifest(manifest)

    def test_interrupted_pack_install_resumes_verified_staging_files_and_reports_progress(self):
        manifest, _, _ = self.build_release()
        app = self.tmp / "client-app"
        stage = app / "staging" / "0.8.0-test.partial"
        cached = stage / "mods" / "shared.jar"
        cached.parent.mkdir(parents=True)
        cached.write_bytes(b"shared-v1")
        events = []
        with mock.patch.object(launcher, "download_verified", wraps=launcher.download_verified) as download:
            release = launcher.install_pack(manifest, app, progress=events.append)
        self.assertEqual(1, download.call_count)
        self.assertEqual(b"shared-v1", (release / "mods" / "shared.jar").read_bytes())
        self.assertTrue(any(event["phase"] == "download" for event in events))
        self.assertTrue(any(event["phase"] == "file" for event in events))

    def test_launcher_selects_supported_linux_desktop_platform(self):
        with mock.patch.object(launcher.platform, "system", return_value="Linux"), \
                mock.patch.object(launcher.platform, "machine", return_value="x86_64"):
            self.assertEqual("linux-x86_64", launcher.platform_key())

    def test_first_login_automatically_continues_into_drewcraft_instance(self):
        state = {"prismExecutable": "/managed/prism", "prismRoot": "/managed/data"}
        process = mock.Mock()
        process.poll.return_value = None
        with mock.patch.object(launcher_entry, "_message"), \
                mock.patch.object(launcher_entry, "_needs_login", side_effect=[True, False]), \
                mock.patch.object(launcher_entry.subprocess, "Popen", return_value=process) as popen, \
                mock.patch.object(launcher_entry.time, "sleep"), \
                mock.patch.object(launcher_entry, "launch", return_value=0) as launch_instance:
            self.assertEqual(0, launcher_entry._authenticate_and_launch(state, self.tmp, poll_interval=0))
        popen.assert_called_once_with(["/managed/prism", "--dir", "/managed/data"])
        launch_instance.assert_called_once_with(self.tmp)

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
        self.assertEqual({"cellSizeBlocks": 64, "cells": []}, result["terrain"])

    def test_offline_anvil_reader_decodes_nbt_palette_and_heightmap_primitives(self):
        raw = b"\x0a\x00\x00" + b"\x03\x00\x04xPos" + struct.pack(">i", 7) + b"\x00"
        self.assertEqual(7, world_extract.NbtReader(raw).root()["xPos"])
        chunk = world_extract.Chunk({
            "xPos": 0, "zPos": 0,
            "sections": [{"Y": 4, "block_states": {"palette": [{"Name": "minecraft:stone"}]}}],
            "Heightmaps": {"WORLD_SURFACE": [1]},
        })
        self.assertEqual("minecraft:stone", chunk.block(1, 64, 1))
        self.assertIsInstance(chunk.surface_y(0, 0), int)


if __name__ == "__main__":
    unittest.main()
