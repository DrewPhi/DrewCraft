"""Cross-file Covenant consistency: site IDs, lore registry, faction roster,
endgame manifest and synthetic plan must agree. Objective pass/fail, no human needed."""
from __future__ import annotations

import json
import pathlib
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


class CovenantConsistencyTest(unittest.TestCase):
    def test_site_ids_match_lore_and_synthetic_plan(self):
        sites = json.loads((ROOT / "pack/content/sites/sites.json").read_text(encoding="utf-8"))
        lore = json.loads((ROOT / "pack/content/lore/config.json").read_text(encoding="utf-8"))
        lore_ids = {s["id"] for s in lore["sites"]}
        site_ids = {s["id"] for s in sites["sites"]}
        self.assertEqual(site_ids, lore_ids)
        plan = json.loads((ROOT / "build/synthetic-world.json").read_text(encoding="utf-8"))
        self.assertIn(plan["site_id"] if "site_id" in plan else plan["source_core"]["site_id"], site_ids)

    def test_covenant_faction_uses_confirmed_illager_ids(self):
        factions = json.loads((ROOT / "mods/drewcraft/src/main/resources/data/drewcraft/strategic/factions.json").read_text(encoding="utf-8"))
        covenant = next(f for f in factions["factions"] if f["id"] == "drewcraft:covenant")
        templates = {t["id"]: t for t in covenant["templates"]}
        self.assertEqual(set(templates), {"drewcraft:covenant_patrol", "drewcraft:covenant_horde",
                                          "drewcraft:covenant_raid", "drewcraft:covenant_army",
                                          "drewcraft:covenant_reinforcement"})
        army = templates["drewcraft:covenant_army"]["composition"]
        self.assertIn("illagerinvasion:invoker", army)
        self.assertAlmostEqual(sum(army.values()), 1.0)
        # illusioner is vanilla, never an illagerinvasion: ID.
        blob = json.dumps(covenant)
        self.assertNotIn("illagerinvasion:illusioner", blob)

    def test_endgame_manifest_matches_locked_hashes(self):
        endgame = yaml.safe_load((ROOT / "pack/manifest/endgame_content.yaml").read_text(encoding="utf-8"))
        mob = endgame["cult_mobs"]["foundation"]
        self.assertEqual(mob["provider"]["candidate_version"], "v21.1.6")
        self.assertEqual(mob["provider"]["file_id"], 6492670)
        mob_struct = (ROOT / "pack/manifest/mob_structure_candidates.yaml").read_text(encoding="utf-8")
        self.assertIn("5adfdd0df0c5dbe81e4458da50442b58863f9db9f22abc182f81e487eef0e6db", mob_struct)
        self.assertIn("3719344055f3409756f0cde6eab3d18e65cf1236029bbe1aa8284369554e4ce8", mob_struct)


if __name__ == "__main__":
    unittest.main()
