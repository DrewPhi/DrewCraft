import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("inject_drewcraft_mod", ROOT / "tools/inject_drewcraft_mod.py")
injector = importlib.util.module_from_spec(spec)
sys.modules["inject_drewcraft_mod"] = injector
spec.loader.exec_module(injector)


class DrewCraftModInjectionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="drewcraft-bp8-inject-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def tree(self, name):
        root = self.tmp / name
        (root / "mods").mkdir(parents=True)
        (root / "mods" / "upstream.jar").write_bytes(b"upstream")
        (root / "drewcraft-layout.json").write_text(json.dumps({
            "schema_version": 1,
            "target": name,
            "profiles": ["test"],
            "files": [{"id": "upstream", "path": "mods/upstream.jar", "sha256": "x" * 64}],
        }) + "\n", encoding="utf-8")
        return root

    def test_repository_mod_is_copied_and_recorded_on_both_sides(self):
        jar = self.tmp / "drewcraft-0.1.0.jar"
        jar.write_bytes(b"compiled DrewCraft")
        client = self.tree("client")
        server = self.tree("server")
        a = injector.inject(client, jar)
        b = injector.inject(server, jar)
        self.assertEqual(a["sha256"], b["sha256"])
        self.assertEqual("repository_build", a["source"])
        for root in (client, server):
            self.assertEqual(b"compiled DrewCraft", (root / "mods" / jar.name).read_bytes())
            layout = json.loads((root / "drewcraft-layout.json").read_text("utf-8"))
            custom = [entry for entry in layout["files"] if entry["id"] == "drewcraft_mod"]
            self.assertEqual(1, len(custom))
            self.assertEqual(f"mods/{jar.name}", custom[0]["path"])

    def test_duplicate_custom_mod_identity_fails_closed(self):
        jar = self.tmp / "drewcraft.jar"
        jar.write_bytes(b"one")
        root = self.tree("client")
        injector.inject(root, jar)
        with self.assertRaisesRegex(RuntimeError, "already represented"):
            injector.inject(root, jar)


if __name__ == "__main__":
    unittest.main()
