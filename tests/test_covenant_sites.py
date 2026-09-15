"""Gates for frozen site data + palette tooling (no final placements needed)."""
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


palette = load_module("palette_normalize", "tools/palette_normalize.py")

LORE_IDS = {"ashen_gate", "first_stone_abbey", "red_reliquary", "low_bell_monastery",
            "closed_wing_bastion", "saint_orun_scriptorium", "cairnwatch", "eighth_chain_citadel"}


class CovenantSitesTest(unittest.TestCase):
    def test_eight_sites_match_lore_registry(self):
        data = json.loads((ROOT / "pack/content/sites/sites.json").read_text(encoding="utf-8"))
        ids = [s["id"] for s in data["sites"]]
        self.assertEqual(len(ids), 8)
        self.assertEqual(set(ids), LORE_IDS)
        for site in data["sites"]:
            for key in ("tier", "required_defenders", "source_core_type", "clue_pool",
                        "aa_capability", "archive_contents", "structural_archetype",
                        "strategic_production_strength", "capital_prerequisite"):
                self.assertIn(key, site, f"{site['id']} missing {key}")
            self.assertEqual(site["archive_contents"].count("—"), 1)
        self.assertEqual(data["capital"]["id"], "vespera")

    def test_palette_preserves_orientation_states(self):
        mapping = {"minecraft:oak_stairs": "minecraft:deepslate_brick_stairs"}
        new_id, props = palette.normalize_block(
            "minecraft:oak_stairs", {"facing": "north", "half": "top", "custom": "x"}, mapping)
        self.assertEqual(new_id, "minecraft:deepslate_brick_stairs")
        self.assertEqual(props, {"facing": "north", "half": "top"})

    def test_palette_reports_unmapped_without_dropping(self):
        blocks = [{"id": "minecraft:stone", "properties": {}},
                  {"id": "unknownmod:glyph", "properties": {"facing": "south"}}]
        out, unmapped = palette.normalize_palette(blocks, {"minecraft:stone": "minecraft:tuff"})
        self.assertEqual(out[0]["id"], "minecraft:tuff")
        self.assertEqual(out[1]["id"], "unknownmod:glyph")
        self.assertEqual(unmapped, ["unknownmod:glyph"])


if __name__ == "__main__":
    unittest.main()
