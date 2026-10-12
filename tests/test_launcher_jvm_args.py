import importlib.util
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


load_module("drewcraft_server_list", "launcher/drewcraft_server_list.py")
bootstrap = load_module("drewcraft_bootstrap_jvm", "launcher/drewcraft_bootstrap.py")


class LauncherJvmArgsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="drewcraft-jvm-"))
        self.instance = self.tmp / "instances" / "DrewCraft-1.0.0"
        self.instance.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cfg_text(self):
        return (self.instance / "instance.cfg").read_text("utf-8")

    def test_fresh_instance_gets_zgc_flag(self):
        bootstrap._apply_managed_jvm_args(self.instance)
        text = self.cfg_text()
        self.assertIn("JvmArgs=-XX:+UseZGC", text)
        self.assertEqual(text.count("-XX:+UseZGC"), 1)

    def test_existing_user_flags_are_preserved_and_extended(self):
        cfg = self.instance / "instance.cfg"
        cfg.write_text("OverrideMemory=true\nJvmArgs=-Xss4M -Dfoo=bar\n", encoding="utf-8")
        bootstrap._apply_managed_jvm_args(self.instance)
        text = self.cfg_text()
        self.assertIn("-Xss4M", text)
        self.assertIn("-Dfoo=bar", text)
        self.assertIn("-XX:+UseZGC", text)
        self.assertEqual(text.count("-XX:+UseZGC"), 1)
        # Second converge must not duplicate the flag.
        bootstrap._apply_managed_jvm_args(self.instance)
        self.assertEqual(self.cfg_text().count("-XX:+UseZGC"), 1)

    def test_memory_settings_still_enforced_alongside(self):
        bootstrap._apply_memory_settings(self.instance)
        bootstrap._apply_managed_jvm_args(self.instance)
        text = self.cfg_text()
        self.assertIn("MaxMemAlloc=8192", text)
        self.assertIn("JvmArgs=-XX:+UseZGC", text)


if __name__ == "__main__":
    unittest.main()
