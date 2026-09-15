"""Covenant endgame profile gate: Illager Invasion + Puzzles Lib resolve with
exact identity, and the suppression overlay is wired and well-formed.

Covers: promotion into the verified manifest graph + native-behavior audit
(raids off, worldgen tags emptied, patrol/mansion posture documented).
"""
from __future__ import annotations

import json
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


pack = load_module("drewcraft_pack_covenant", "tools/drewcraft_pack.py")

OVERLAY = ROOT / "pack/overlays/covenant_endgame_spike"
EXPECTED_TAGS = [
    "illager_fort",
    "illusioner_tower",
    "firecaller_hut",
    "sorcerer_hut",
    "labyrinth",
]


class CovenantEndgameProfileTest(unittest.TestCase):
    def test_profile_resolves_with_exact_covenant_identities(self):
        profiles = pack.load_yaml(ROOT / "pack/manifest/profiles.yaml")
        catalog = pack.collect_catalog(ROOT, profiles)
        for cid in ("illager_invasion", "puzzles_lib"):
            self.assertIn(cid, catalog, f"missing candidate: {cid}")
        resolved = pack.resolve(["covenant_endgame_spike"], profiles, catalog)
        plan = pack.make_plan(resolved, catalog)
        by_id = {d["id"]: d for d in plan["dependencies"]}
        for cid in ("illager_invasion", "puzzles_lib"):
            self.assertTrue(by_id[cid]["exact_identity_ready"], f"{cid} not exact: {by_id[cid]['identity_issues']}")
            self.assertEqual(by_id[cid]["side"], "common")
        self.assertIn("pack/overlays/covenant_endgame_spike", plan["overlays"])
        self.assertEqual(by_id["illager_invasion"]["required_dependencies"], ["puzzles_lib"])

    def test_raid_suppression_config_disables_all_waves(self):
        cfg = (OVERLAY / "config/illagerinvasion-server.toml").read_text(encoding="utf-8")
        for mob in ("basher", "provoker", "necromancer", "sorcerer", "illusioner",
                    "archivist", "marauder", "inquisitor", "alchemist", "invoker"):
            self.assertIn(f"[{mob}]", cfg)
        self.assertNotIn("participateInRaids = true", cfg)
        self.assertGreaterEqual(cfg.count("participateInRaids = false"), 10)

    def test_worldgen_suppression_tags_are_empty(self):
        for tag in EXPECTED_TAGS:
            path = OVERLAY / f"data/illagerinvasion/tags/worldgen/biome/has_structure/{tag}.json"
            with self.subTest(tag=tag):
                self.assertTrue(path.is_file(), f"missing suppression tag: {tag}")
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.assertTrue(payload.get("replace"))
                self.assertEqual(payload.get("values"), [])


if __name__ == "__main__":
    unittest.main()
