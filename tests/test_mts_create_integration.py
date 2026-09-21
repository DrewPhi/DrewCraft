from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path

MODULE = Path(__file__).parents[1] / "tools" / "generate_mts_create_integration.py"
SPEC = importlib.util.spec_from_file_location("generate_mts_create_integration", MODULE)
assert SPEC and SPEC.loader
integration = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = integration
SPEC.loader.exec_module(integration)


def test_material_transform_removes_legacy_generic_stock_and_conserves_iron():
    old = [
        "mts:mtsofficialpack.plating:42",
        "mts:mtsofficialpack.screws:48",
        "mts:mtsofficialpack.metaltube:24",
        "mts:mtsofficialpack.copperwire:16",
        "minecraft:glass_pane:4",
    ]
    new, audit = integration.transform_material_list(old)
    joined = "\n".join(new)
    assert "mtsofficialpack.plating" not in joined
    assert "mtsofficialpack.screws" not in joined
    assert "mtsofficialpack.metaltube" not in joined
    assert "mtsofficialpack.copperwire" not in joined
    assert "create:iron_sheet:" in joined
    assert "createaddition:iron_rod:" in joined
    assert "minecraft:iron_nugget:" in joined
    assert "createaddition:copper_wire:16" in joined
    assert abs(audit["generic_iron_delta_percent"]) <= 5.0


def test_generator_uses_exact_pack_material_lists_and_keeps_mts_functional_parts(tmp_path: Path):
    mts = tmp_path / "mts.jar"
    vehicle = {
        "general": {
            "materialLists": [[
                "mts:mtsofficialpack.plating:24",
                "mts:mtsofficialpack.screws:24",
                "mts:mtsofficialpack.circuit:2",
                "minecraft:glass_pane:4",
            ]]
        }
    }
    with zipfile.ZipFile(mts, "w") as z:
        z.writestr("assets/mtsofficialpack/jsondefs/vehicles/testplane.json", json.dumps(vehicle))

    overrides, report = integration.build_mts_overrides(mts)
    mats = overrides["overrides"]["mtsofficialpack"]["testplane"]["commonMaterialLists"][0]
    text = "\n".join(mats)
    assert "mts:mtsofficialpack.circuit:2" in text
    assert "create:iron_sheet:" in text
    assert "createaddition:iron_rod:" in text
    assert report["overridden_item_count"] == 1


def test_wda_loot_is_appended_without_removing_upstream_pools(tmp_path: Path):
    wda = tmp_path / "wda.jar"
    original = {
        "type": "minecraft:chest",
        "pools": [{"name": "upstream", "rolls": 1, "entries": []}],
    }
    path = "data/dungeons_arise/loot_table/chests/test.json"
    with zipfile.ZipFile(wda, "w") as z:
        z.writestr(path, json.dumps(original))

    datapack = tmp_path / "datapack"
    report = integration.write_wda_overrides(wda, datapack)
    result = json.loads((datapack / path).read_text())
    assert report["modified_wda_loot_tables"] == 1
    assert result["pools"][0]["name"] == "upstream"
    assert result["pools"][-1]["name"] == "drewcraft:industrial_salvage"


def test_tiny_fastener_recipe_does_not_get_rod_rounding_inflation():
    new, audit = integration.transform_material_list([
        "mts:mtsofficialpack.screws:2",
    ])
    assert new == ["minecraft:iron_nugget:2"]
    assert audit["old_generic_iron_equivalent"] == audit["new_generic_iron_equivalent"]
    assert audit["generic_iron_delta_percent"] == 0.0


def test_single_plate_or_tube_stays_within_global_ten_percent_gate():
    for legacy in ("mts:mtsofficialpack.plating:1", "mts:mtsofficialpack.metaltube:1"):
        _, audit = integration.transform_material_list([legacy])
        assert abs(audit["generic_iron_delta_percent"]) <= 10.0
