"""Tests for tools/covenant_lore.py — clue mechanics without gameplay feel."""
from __future__ import annotations

import pathlib
import random
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(name, path):
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lore = load_module("covenant_lore", "tools/covenant_lore.py")


class CovenantLoreTest(unittest.TestCase):
    def test_distribution_matches_frozen_config(self):
        dist = lore.distribution()
        self.assertAlmostEqual(sum(dist.values()), 1.0)
        self.assertAlmostEqual(dist["x_y_z_full"], 0.015)
        self.assertAlmostEqual(dist["x_z"], 0.045)

    def test_full_coordinates_are_rare(self):
        rng = random.Random(1234)
        modes = [lore.roll_mode(rng) for _ in range(4000)]
        full = sum(1 for m in modes if m == "x_y_z_full")
        # Expect ~60 at p=0.015; allow wide tolerance so the test is stable.
        self.assertLess(full, 200)

    def test_waymark_withholds_missing_axes_and_keeps_name(self):
        lines = lore.render_waymark("Ashen Gate", {"x": -8421, "y": 72, "z": 3910}, "x_only")
        text = "\n".join(lines)
        self.assertIn("Ashen Gate", text)
        self.assertIn("X: -8421", text)
        self.assertIn("Y: [withheld]", text)
        self.assertIn("Z: [withheld]", text)

    def test_waymark_full_mode_shows_everything(self):
        lines = lore.render_waymark("Cairnwatch", {"x": 100, "y": 64, "z": -200}, "x_y_z_full")
        text = "\n".join(lines)
        self.assertIn("X: 100", text)
        self.assertIn("Y: 64", text)
        self.assertIn("Z: -200", text)

    def test_field_books_bias_home_site(self):
        rng = random.Random(7)
        picks = [lore.choose_field_book_site(rng, "ashen_gate", ["cairnwatch", "red_reliquary"]) for _ in range(1000)]
        home = sum(1 for p in picks if p == "ashen_gate")
        self.assertGreater(home, 600)

    def test_cleared_sites_fall_to_residue(self):
        self.assertEqual(lore.site_weight("ashen_gate", set()), 1.0)
        self.assertAlmostEqual(lore.site_weight("ashen_gate", {"ashen_gate"}), 0.05)

    def test_two_fragments_can_combine(self):
        # X-only + Z-only for the same named site reconstructs horizontal position.
        x_lines = lore.render_waymark("Ashen Gate", {"x": -8421, "y": 0, "z": 0}, "x_only")
        z_lines = lore.render_waymark("Ashen Gate", {"x": 0, "y": 0, "z": 3910}, "z_only")
        self.assertIn("X: -8421", "\n".join(x_lines))
        self.assertIn("Z: 3910", "\n".join(z_lines))


if __name__ == "__main__":
    unittest.main()
