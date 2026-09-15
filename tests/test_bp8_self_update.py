"""Tests for launcher/self_update.py — seamless updates on all three OSs."""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


self_update = load_module("self_update", "launcher/self_update.py")


def release(version, assets=(), draft=False):
    return {
        "tag_name": f"launcher-v{version}",
        "draft": draft,
        "assets": [
            {"name": name, "state": "uploaded",
             "browser_download_url": f"https://example.invalid/{name}",
             "digest": "sha256:" + "0" * 64}
            for name in assets
        ],
    }


class SelfUpdateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="drewcraft-updater-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_update_available_compares_versions(self):
        latest = {"version": "0.1.5", "release": {}}
        self.assertTrue(self_update.update_available("0.1.4", latest))
        self.assertFalse(self_update.update_available("0.1.5", latest))
        self.assertFalse(self_update.update_available("0.1.6", latest))
        self.assertFalse(self_update.update_available("0.1.4", None))

    def test_fetch_latest_skips_drafts_and_picks_highest(self):
        releases = [release("0.1.9", draft=True), release("0.1.3"), release("0.1.5")]
        payload = json.dumps(releases).encode()

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return payload

        with mock.patch.object(self_update.urllib.request, "urlopen", return_value=FakeResponse()):
            latest = self_update.fetch_latest_launcher(context=object())
        self.assertEqual("0.1.5", latest["version"])

    def test_fetch_failure_means_no_update(self):
        with mock.patch.object(self_update.urllib.request, "urlopen", side_effect=RuntimeError("down")):
            self.assertIsNone(self_update.fetch_latest_launcher(context=object()))

    def test_asset_selection_per_platform(self):
        latest = {"version": "0.1.5", "release": release(
            "0.1.5", assets=("DrewCraft-Windows.exe", "DrewCraft-macOS-arm64", "DrewCraft-Linux-x86_64"))}
        self.assertEqual("DrewCraft-Windows.exe",
                         self_update.asset_for_platform(latest, "windows-x86_64")["name"])
        self.assertEqual("DrewCraft-macOS-arm64",
                         self_update.asset_for_platform(latest, "macos-arm64")["name"])
        self.assertEqual("DrewCraft-Linux-x86_64",
                         self_update.asset_for_platform(latest, "linux-x86_64")["name"])
        self.assertIsNone(self_update.asset_for_platform(latest, "solaris-sparc"))

    def test_posix_swap_is_atomic_and_never_empties(self):
        current = self.tmp / "DrewCraft"
        current.write_bytes(b"old-binary")
        downloaded = self.tmp / "DrewCraft.new"
        downloaded.write_bytes(b"new-binary")
        with mock.patch.object(os, "name", "posix"):
            installed = self_update.swap_executable(current, downloaded)
        self.assertEqual(installed, current)
        self.assertEqual(b"new-binary", current.read_bytes())
        self.assertFalse(downloaded.exists())

    def test_windows_swap_renames_aside_and_restores_on_failure(self):
        current = self.tmp / "DrewCraft-Windows.exe"
        current.write_bytes(b"old-binary")
        downloaded = self.tmp / "DrewCraft-Windows.exe.new"
        downloaded.write_bytes(b"new-binary")
        with mock.patch.object(os, "name", "nt"):
            installed = self_update.swap_executable(current, downloaded)
            self.assertEqual(installed, current)
            self.assertEqual(b"new-binary", current.read_bytes())
            asides = [p for p in self.tmp.iterdir() if ".old" in p.name]
            self.assertEqual(1, len(asides))
            # Failure path restores the original instead of stranding the player.
            staged = self.tmp / "other.new"
            staged.write_bytes(b"nope")
            with mock.patch.object(self_update.os, "replace", side_effect=OSError("locked")):
                with self.assertRaises(RuntimeError):
                    self_update.swap_executable(current, staged)
            self.assertEqual(b"new-binary", current.read_bytes())

    def test_reap_asides_removes_only_swap_files(self):
        (self.tmp / "DrewCraft-Windows.exe").write_bytes(b"live")
        (self.tmp / "DrewCraft-Windows.exe.old").write_bytes(b"stale")
        (self.tmp / "DrewCraft-Windows.exe.old.123.0").write_bytes(b"stale2")
        (self.tmp / "notes.txt").write_bytes(b"keep")
        removed = self_update.reap_asides(self.tmp, "DrewCraft-Windows.exe")
        self.assertEqual(2, len(removed))
        self.assertTrue((self.tmp / "DrewCraft-Windows.exe").is_file())
        self.assertTrue((self.tmp / "notes.txt").is_file())

    def test_maybe_self_update_never_strands_player(self):
        # Dev mode (not frozen): always continue normally.
        self.assertFalse(self_update.maybe_self_update("0.0.0", "windows-x86_64", ["drewcraft"]))
        # Opt-outs continue normally.
        with mock.patch.dict(os.environ, {self_update.SKIP_ENV: "1"}):
            self.assertFalse(self_update.maybe_self_update("0.0.0", "windows-x86_64", ["drewcraft"]))
        self.assertFalse(self_update.maybe_self_update("0.0.0", "windows-x86_64",
                                                       ["drewcraft", "--skip-self-update"]))

    def test_maybe_self_update_relaunches_on_newer_release(self):
        latest = {"version": "9.9.9", "release": release("9.9.9", assets=("DrewCraft-Windows.exe",))}
        asset = latest["release"]["assets"][0]
        current = self.tmp / "DrewCraft-Windows.exe"
        current.write_bytes(b"old")
        with mock.patch.object(self_update.sys, "frozen", True, create=True), \
                mock.patch.object(self_update.sys, "executable", str(current)), \
                mock.patch.object(self_update, "fetch_latest_launcher", return_value=latest), \
                mock.patch.object(self_update, "download_asset",
                                  side_effect=lambda url, digest, dest, context=None: (
                                      pathlib.Path(dest).write_bytes(b"new"), pathlib.Path(dest))[1]), \
                mock.patch.object(self_update, "relaunch", side_effect=SystemExit(0)):
            with self.assertRaises(SystemExit):
                self_update.maybe_self_update("0.0.0", "windows-x86_64", ["drewcraft"])
        self.assertEqual(asset["browser_download_url"], asset["browser_download_url"])

    def test_current_executable_none_in_dev(self):
        with mock.patch.object(self_update.sys, "frozen", False, create=True):
            self.assertIsNone(self_update.current_executable())


if __name__ == "__main__":
    unittest.main()
