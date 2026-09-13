import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
spec = importlib.util.spec_from_file_location("apply_release_acquisition", ROOT / "tools/apply_release_acquisition.py")
acquisition = importlib.util.module_from_spec(spec)
sys.modules["apply_release_acquisition"] = acquisition
spec.loader.exec_module(acquisition)


class ReleaseAcquisitionPolicyTest(unittest.TestCase):
    def manifest(self):
        return {
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
                {"path": "mods/cf.jar", "side": "common", "size": 3, "sha256": "a" * 64, "url": "https://drew.invalid/cf.jar", "managed": True},
                {"path": "mods/modrinth.jar", "side": "common", "size": 4, "sha256": "b" * 64, "url": "https://drew.invalid/modrinth.jar", "managed": True},
                {"path": "mods/drewcraft.jar", "side": "common", "size": 5, "sha256": "c" * 64, "url": "https://drew.invalid/drewcraft.jar", "managed": True},
            ],
        }

    def evidence(self):
        return {
            "schema_version": 1,
            "artifacts": {
                "curseforge_mod": {
                    "provider": "curseforge", "project_id": 123, "file_id": 456,
                    "filename": "cf.jar", "sha256": "a" * 64, "size": 3,
                },
                "modrinth_mod": {
                    "provider": "modrinth", "project_id": "project", "version_id": "version",
                    "filename": "modrinth.jar", "sha256": "b" * 64, "size": 4,
                },
            },
        }

    def test_exact_provider_hashes_use_provider_urls_while_drewcraft_file_stays_on_release_base(self):
        def fake_modrinth(item):
            self.assertEqual("version", item["version_id"])
            return "https://cdn.modrinth.com/data/project/versions/version/modrinth.jar"

        result = acquisition.apply(self.manifest(), self.evidence(), modrinth_resolver=fake_modrinth)
        files = {entry["path"]: entry for entry in result["files"]}
        self.assertEqual(
            "https://www.curseforge.com/api/v1/mods/123/files/456/download",
            files["mods/cf.jar"]["url"],
        )
        self.assertEqual("curseforge", files["mods/cf.jar"]["origin"]["provider"])
        self.assertEqual(
            "https://cdn.modrinth.com/data/project/versions/version/modrinth.jar",
            files["mods/modrinth.jar"]["url"],
        )
        self.assertEqual("https://drew.invalid/drewcraft.jar", files["mods/drewcraft.jar"]["url"])
        self.assertEqual("drewcraft_release", files["mods/drewcraft.jar"]["origin"]["type"])
        self.assertEqual(2, result["acquisitionPolicy"]["providerFiles"])

    def test_provider_identity_is_bound_by_sha_not_filename_only(self):
        manifest = self.manifest()
        manifest["files"][0]["sha256"] = "d" * 64
        result = acquisition.apply(manifest, self.evidence(), modrinth_resolver=lambda _: "https://example.invalid")
        entry = result["files"][0]
        self.assertEqual("https://drew.invalid/cf.jar", entry["url"])
        self.assertEqual("drewcraft_release", entry["origin"]["type"])


if __name__ == "__main__":
    unittest.main()
