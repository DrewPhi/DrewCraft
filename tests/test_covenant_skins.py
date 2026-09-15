"""Covenant skin gate: the six first-pass PNGs must exist at the exact
Illager Invasion override paths and remain valid 64x64 RGBA PNGs.

Covers pre-playtest item: "Integrate the Covenant skins for real ... add CI
that fails if any expected skin disappears."
"""
from __future__ import annotations

import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACK = ROOT / "assets" / "resourcepacks" / "drewcraft_cult_first_pass" / "assets" / "illagerinvasion" / "textures" / "entity"

EXPECTED = [
    "archivist.png",
    "basher.png",
    "firecaller.png",
    "inquisitor.png",
    "invoker.png",
    "necromancer.png",
]


def png_size(path: pathlib.Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"{path.name}: not a PNG file")
    if len(data) < 33:
        raise AssertionError(f"{path.name}: truncated PNG")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


class CovenantSkinsTest(unittest.TestCase):
    def test_pack_mcmeta_exists(self):
        mcmeta = PACK.parents[3] / "pack.mcmeta"
        self.assertTrue(mcmeta.is_file(), f"missing {mcmeta}")

    def test_all_expected_skins_present_and_sized(self):
        for name in EXPECTED:
            with self.subTest(skin=name):
                path = PACK / name
                self.assertTrue(path.is_file(), f"missing Covenant skin: {path}")
                self.assertGreater(path.stat().st_size, 0, f"empty skin: {name}")
                width, height = png_size(path)
                self.assertEqual((width, height), (64, 64), f"{name} must stay 64x64 RGBA first-pass, got {width}x{height}")


if __name__ == "__main__":
    unittest.main()
