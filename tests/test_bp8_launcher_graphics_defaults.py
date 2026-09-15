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


client_defaults = load_module(
    "drewcraft_client_defaults", "launcher/drewcraft_client_defaults.py"
)


class LauncherGraphicsDefaultsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="drewcraft-potato-"))
        self.app = self.tmp / "app"
        self.prism = self.app / "prism-data"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def state(self, version="1.0.0", instance="DrewCraft-1.0.0"):
        minecraft = self.prism / "instances" / instance / "minecraft"
        minecraft.mkdir(parents=True, exist_ok=True)
        return {
            "packVersion": version,
            "prismRoot": str(self.prism),
            "instanceId": instance,
        }, minecraft

    def test_fresh_install_seeds_potato_without_touching_gameplay_config(self):
        state, minecraft = self.state()
        self.assertTrue(client_defaults.apply_client_defaults(self.app, state))

        options = (minecraft / "options.txt").read_text("utf-8")
        self.assertIn("renderDistance:8", options)
        self.assertIn("simulationDistance:6", options)
        self.assertIn("particles:1", options)
        self.assertIn("maxFps:60", options)

        clouds = (minecraft / "config/simpleclouds-client.toml").read_text("utf-8")
        self.assertIn('levelOfDetail = "LOW"', clouds)
        self.assertIn('generationInterval = "DYNAMIC"', clouds)
        self.assertIn("framesToGenerateMesh = 20", clouds)
        self.assertIn("transparency = false", clouds)
        self.assertIn("renderStormFog = false", clouds)
        self.assertIn("atmosphericClouds = false", clouds)
        self.assertIn("distantShadows = false", clouds)
        self.assertIn("shadowDistance = 1000", clouds)
        self.assertNotIn("renderClouds = false", clouds)
        self.assertNotIn("generateMesh = false", clouds)

        dh = (minecraft / "configs/DistantHorizons.toml").read_text("utf-8")
        self.assertIn("[client.advanced.graphics.quality]", dh)
        self.assertIn("lodChunkRenderDistanceRadius = 128", dh)

        marker = json.loads(
            (self.app / "user-data/client-defaults.json").read_text("utf-8")
        )
        self.assertEqual(marker["graphicsPreset"], "potato")

        # Client defaults must not create or alter gameplay-authority configs.
        self.assertFalse((minecraft / "serverconfig").exists())
        self.assertFalse((minecraft / "config/projectatmosphere-common.toml").exists())

    def test_existing_user_settings_win_and_are_never_reseeded(self):
        state, minecraft = self.state()
        options = minecraft / "options.txt"
        clouds = minecraft / "config/simpleclouds-client.toml"
        dh = minecraft / "configs/DistantHorizons.toml"
        clouds.parent.mkdir(parents=True, exist_ok=True)
        dh.parent.mkdir(parents=True, exist_ok=True)
        options.write_text("renderDistance:24\nmaxFps:165\n", encoding="utf-8")
        clouds.write_text("# custom\n[visual]\ntransparency = true\n", encoding="utf-8")
        dh.write_text("# custom\n[client.advanced.graphics.quality]\nlodChunkRenderDistanceRadius = 512\n", encoding="utf-8")

        self.assertTrue(client_defaults.apply_client_defaults(self.app, state))
        self.assertEqual(options.read_text("utf-8"), "renderDistance:24\nmaxFps:165\n")
        self.assertIn("transparency = true", clouds.read_text("utf-8"))
        self.assertIn("lodChunkRenderDistanceRadius = 512", dh.read_text("utf-8"))

        options.write_text("renderDistance:32\n", encoding="utf-8")
        self.assertFalse(client_defaults.apply_client_defaults(self.app, state))
        self.assertEqual(options.read_text("utf-8"), "renderDistance:32\n")

    def test_mod_graphics_choices_survive_versioned_instance_update(self):
        state1, minecraft1 = self.state("1.0.0", "DrewCraft-1.0.0")
        client_defaults.apply_client_defaults(self.app, state1)

        clouds1 = minecraft1 / "config/simpleclouds-client.toml"
        dh1 = minecraft1 / "configs/DistantHorizons.toml"
        clouds1.write_text("# user chose Beautiful clouds\n", encoding="utf-8")
        dh1.write_text("# user chose 384 chunks\n", encoding="utf-8")
        (self.app / "state.json").write_text(json.dumps(state1), encoding="utf-8")

        client_defaults.snapshot_user_graphics(self.app)

        state2, minecraft2 = self.state("1.0.1", "DrewCraft-1.0.1")
        self.assertFalse(client_defaults.apply_client_defaults(self.app, state2))
        self.assertEqual(
            (minecraft2 / "config/simpleclouds-client.toml").read_text("utf-8"),
            "# user chose Beautiful clouds\n",
        )
        self.assertEqual(
            (minecraft2 / "configs/DistantHorizons.toml").read_text("utf-8"),
            "# user chose 384 chunks\n",
        )

    def test_deleted_config_does_not_resurrect_stale_cached_copy(self):
        state, minecraft = self.state()
        client_defaults.apply_client_defaults(self.app, state)
        (self.app / "state.json").write_text(json.dumps(state), encoding="utf-8")
        client_defaults.snapshot_user_graphics(self.app)

        source = minecraft / "config/simpleclouds-client.toml"
        cached = self.app / "user-data/graphics/config/simpleclouds-client.toml"
        self.assertTrue(cached.is_file())
        source.unlink()
        client_defaults.snapshot_user_graphics(self.app)
        self.assertFalse(cached.exists())


if __name__ == "__main__":
    unittest.main()
