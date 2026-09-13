import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
spec = importlib.util.spec_from_file_location("package_release_payload", ROOT / "tools/package_release_payload.py")
packager = importlib.util.module_from_spec(spec)
sys.modules["package_release_payload"] = packager
spec.loader.exec_module(packager)


class ReleasePayloadPackagingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="drewcraft-payload-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_provider_files_are_not_rehosted_but_drewcraft_owned_files_are(self):
        layout = self.tmp / "layout"
        (layout / "common" / "mods").mkdir(parents=True)
        provider = layout / "common" / "mods" / "provider.jar"
        owned = layout / "common" / "mods" / "drewcraft.jar"
        provider.write_bytes(b"provider")
        owned.write_bytes(b"owned")

        manifest = {
            "schemaVersion": 1,
            "packVersion": "1.0.0-test",
            "channel": "test",
            "protocolVersion": 1,
            "minecraftVersion": "1.21.1",
            "loader": {"id": "neoforge", "version": "21.1.250"},
            "java": {"major": 21},
            "minimumLauncherVersion": "0.1.0",
            "world": {"worldId": "drewcraft-production", "worldRevision": 1, "generationPackVersion": "drewcraft-worldgen-1"},
            "files": [
                {"path": "mods/provider.jar", "side": "common", "size": provider.stat().st_size, "sha256": packager.sha256(provider), "url": "https://provider.invalid/mod.jar", "managed": True, "origin": {"type": "provider", "provider": "example"}},
                {"path": "mods/drewcraft.jar", "side": "common", "size": owned.stat().st_size, "sha256": packager.sha256(owned), "url": "https://drew.invalid/releases/1.0.0-test/common/mods/drewcraft.jar", "managed": True, "origin": {"type": "drewcraft_release"}},
            ],
        }
        manifest_path = self.tmp / "release-manifest.json"
        manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        live_path = self.tmp / "live.json"
        live_path.write_text(json.dumps({"packVersion": "1.0.0-test"}) + "\n", encoding="utf-8")
        output = self.tmp / "publish"

        result = packager.package(layout, manifest_path, live_path, output)
        self.assertEqual(1, result["includedDrewCraftFiles"])
        self.assertEqual(1, result["providerFilesOmitted"])
        self.assertTrue((output / "1.0.0-test" / "common" / "mods" / "drewcraft.jar").is_file())
        self.assertFalse((output / "1.0.0-test" / "common" / "mods" / "provider.jar").exists())
        self.assertTrue((output / "1.0.0-test" / "release-manifest.json").is_file())
        self.assertTrue((output / "live.json").is_file())
        sums = (output / "SHA256SUMS").read_text("ascii")
        self.assertIn("drewcraft.jar", sums)
        self.assertNotIn("provider.jar", sums)


if __name__ == "__main__":
    unittest.main()
