import importlib.util
import pathlib
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("assemble_server_application", ROOT / "tools/assemble_server_application.py")
server_app = importlib.util.module_from_spec(spec)
sys.modules["assemble_server_application"] = server_app
spec.loader.exec_module(server_app)


class ServerApplicationAssemblyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="drewcraft-server-app-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_neoforge_runtime_and_verified_pack_become_one_immutable_application(self):
        runtime = self.tmp / "runtime"
        (runtime / "libraries" / "net" / "neoforged").mkdir(parents=True)
        (runtime / "libraries" / "net" / "neoforged" / "loader.jar").write_bytes(b"loader")
        (runtime / "mods").mkdir()
        (runtime / "mods" / "runtime-placeholder.jar").write_bytes(b"remove me")
        (runtime / "run.sh").write_text("#!/bin/sh\n", encoding="utf-8")

        pack = self.tmp / "pack"
        (pack / "mods").mkdir(parents=True)
        (pack / "mods" / "drewcraft.jar").write_bytes(b"verified")
        (pack / "config").mkdir()
        (pack / "config" / "server.toml").write_text("managed=true\n", encoding="utf-8")
        (pack / "drewcraft-layout.json").write_text("{}\n", encoding="utf-8")

        output = self.tmp / "application"
        counts = server_app.assemble(runtime, pack, output)
        self.assertTrue((output / "run.sh").is_file())
        self.assertTrue((output / "libraries" / "net" / "neoforged" / "loader.jar").is_file())
        self.assertEqual(b"verified", (output / "mods" / "drewcraft.jar").read_bytes())
        self.assertFalse((output / "mods" / "runtime-placeholder.jar").exists())
        self.assertEqual("managed=true\n", (output / "config" / "server.toml").read_text("utf-8"))
        self.assertIn("-Xmx8G", (output / "user_jvm_args.txt").read_text("utf-8"))
        self.assertEqual("eula=true\n", (output / "eula.txt").read_text("utf-8"))
        properties = (output / "server.properties").read_text("utf-8")
        self.assertIn("white-list=true", properties)
        self.assertIn("enforce-whitelist=true", properties)
        self.assertIn("online-mode=true", properties)
        self.assertFalse((output / "world").exists())
        self.assertFalse((output / "logs").exists())
        self.assertGreater(counts["applicationFiles"], 0)

    def test_persistent_paths_are_rejected_from_release_inputs(self):
        runtime = self.tmp / "runtime"
        (runtime / "libraries").mkdir(parents=True)
        (runtime / "run.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        (runtime / "world").mkdir()
        pack = self.tmp / "pack"
        (pack / "mods").mkdir(parents=True)
        with self.assertRaisesRegex(RuntimeError, "reserved persistent path"):
            server_app.assemble(runtime, pack, self.tmp / "out")


if __name__ == "__main__":
    unittest.main()
