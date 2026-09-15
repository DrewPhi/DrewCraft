"""Tests for tools/site_placement.py — geometry fit without visual judgment."""
from __future__ import annotations

import pathlib
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


placement = load_module("site_placement", "tools/site_placement.py")


def flat(h=64.0, n=4):
    return [[h] * n for _ in range(n)]


class SitePlacementTest(unittest.TestCase):
    def test_flat_open_ground_accepts_outpost(self):
        result = placement.score_site(archetype="roadside shrine / patrol outpost",
                                      heights=flat(), near_water=False,
                                      distance_from_spawn=4096, nearest_site_distance=8192)
        self.assertTrue(result["accepted"])
        self.assertGreaterEqual(result["score"], 60.0)

    def test_cliff_rejects_non_mountain_archetype(self):
        heights = [[64.0, 64.0, 96.0, 64.0] for _ in range(4)]
        result = placement.score_site(archetype="walled cult town", heights=heights,
                                      near_water=False, distance_from_spawn=4096,
                                      nearest_site_distance=8192)
        self.assertFalse(result["accepted"])
        self.assertTrue(any("slope" in r for r in result["reasons"]))

    def test_spawn_and_site_spacing_enforced(self):
        result = placement.score_site(archetype="temple archive", heights=flat(),
                                      near_water=False, distance_from_spawn=100,
                                      nearest_site_distance=100)
        self.assertFalse(result["accepted"])

    def test_river_archetype_requires_water(self):
        result = placement.score_site(archetype="river/bridge stronghold", heights=flat(),
                                      near_water=False, distance_from_spawn=4096,
                                      nearest_site_distance=8192)
        self.assertFalse(result["accepted"])

    def test_ranking_is_deterministic(self):
        a = {"id": "a", "distance_from_spawn": 5000,
             "result": placement.score_site(archetype="temple archive", heights=flat(),
                                            near_water=False, distance_from_spawn=5000,
                                            nearest_site_distance=8192)}
        b = {"id": "b", "distance_from_spawn": 9000,
             "result": placement.score_site(archetype="temple archive", heights=flat(),
                                            near_water=False, distance_from_spawn=9000,
                                            nearest_site_distance=8192)}
        self.assertEqual([c["id"] for c in placement.rank([a, b])], ["b", "a"])


if __name__ == "__main__":
    unittest.main()
