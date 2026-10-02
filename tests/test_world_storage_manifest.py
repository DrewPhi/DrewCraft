import importlib.util
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_contract", ROOT / "tools/release_contract.py")
release_contract = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = release_contract
spec.loader.exec_module(release_contract)


class WorldStorageManifestTest(unittest.TestCase):
    def base(self, storage=None):
        manifest = release_contract.build_manifest_from_layout(
            self.layout,
            pack_version="test-linear-rc",
            channel="candidate",
            protocol_version=1,
            minecraft_version="1.21.1",
            loader_id="neoforge",
            loader_version="21.1.250",
            minimum_launcher_version="0.1.0",
            world_id="drewcraft-production",
            world_revision=1,
            generation_pack_version="drewcraft-worldgen-1",
            base_url="https://example.invalid/releases",
        )
        if storage is not None:
            manifest["worldStorage"] = storage
        return manifest

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.layout = pathlib.Path(self.temp.name)
        server = self.layout / "server" / "mods"
        server.mkdir(parents=True)
        (server / "linear-1.21.1-1.3.3+legacy.jar").write_bytes(b"linear")

    def tearDown(self):
        self.temp.cleanup()

    def test_linear_storage_requires_server_artifact_and_exact_version(self):
        manifest = self.base({"format": "linear-v1", "version": "1.3.3"})
        self.assertIs(release_contract.validate_manifest(manifest), manifest)
        manifest["files"].clear()
        with self.assertRaisesRegex(ValueError, "lacks its exact Linear server mod"):
            release_contract.validate_manifest(manifest)

    def test_anvil_compatibility_omits_optional_storage_lock(self):
        manifest = self.base()
        self.assertNotIn("worldStorage", manifest)
        release_contract.validate_manifest(manifest)

    def test_storage_lock_rejects_unknown_fields_and_versions(self):
        with self.assertRaisesRegex(ValueError, "exact version"):
            release_contract.validate_manifest(self.base({"format": "linear-v1"}))
        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            release_contract.validate_manifest(self.base({"format": "linear-v1", "version": "1.3.3", "mode": "fast"}))


if __name__ == "__main__":
    unittest.main()
