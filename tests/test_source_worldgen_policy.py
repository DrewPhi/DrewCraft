from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
PACK_ROOT = ROOT / "mods/drewcraft/src/main/resources/data/drewcraft/datapacks/source_worldgen"

WDA_ALLOW_LIST = {
    "dungeons_arise:illager_campsite",
    "dungeons_arise:illager_fort",
    "dungeons_arise:bandit_towers",
    "dungeons_arise:plague_asylum",
    "dungeons_arise:shiraz_palace",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_builtin_pack_is_1_21_1_and_disables_all_unlisted_wda_generation():
    metadata = load_json(PACK_ROOT / "pack.mcmeta")
    assert metadata["pack"]["pack_format"] == 48
    sets = PACK_ROOT / "data/dungeons_arise/worldgen/structure_set"
    major = load_json(sets / "major_structures.json")
    assert {entry["structure"] for entry in major["structures"]} == WDA_ALLOW_LIST
    assert major["placement"]["spacing"] == 128
    assert major["placement"]["separation"] == 96
    assert major["neoforge:conditions"] == [{"type": "neoforge:mod_loaded", "modid": "dungeons_arise"}]
    minor = load_json(sets / "minor_structures.json")
    assert minor == {"neoforge:conditions": [{"type": "neoforge:false"}]}


def test_every_allowlisted_wda_structure_is_a_strategic_source():
    mappings = load_json(ROOT / "world/source-mappings.json")
    mapped = {item["structureId"]: item for item in mappings["sources"]}
    assert WDA_ALLOW_LIST <= mapped.keys()
    assert mapped["dungeons_arise:illager_campsite"]["sourceClass"] == "CAMP"
    assert mapped["dungeons_arise:illager_fort"]["sourceClass"] == "FORT"
    assert mapped["dungeons_arise:bandit_towers"]["sourceClass"] == "FORT"
    assert mapped["dungeons_arise:plague_asylum"]["sourceClass"] == "RUIN"
    assert mapped["dungeons_arise:shiraz_palace"]["sourceClass"] == "CITY"


def test_towns_and_towers_outposts_are_sources_but_villages_are_not():
    mappings = load_json(ROOT / "world/source-mappings.json")
    t_and_t = [item for item in mappings["sources"] if item["structureId"].startswith("towns_and_towers:")]
    assert len(t_and_t) == 31
    assert all("pillager_outpost" in item["structureId"] for item in t_and_t)
    assert all(item["sourceClass"] == "CAMP" for item in t_and_t)
    assert all(item["factionId"] == "drewcraft:raiders" for item in t_and_t)


def test_every_shipping_and_combined_smoke_workflow_builds_the_source_profile():
    for name in ("release-candidate-build.yml", "local-dev-release.yml", "full-profile-verify.yml", "server-smoke.yml"):
        text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert "--profile v1_survival_exploration" in text, name


def test_focused_v1_live_release_does_not_inject_covenant_resource_pack():
    text = (ROOT / ".github/workflows/local-dev-release.yml").read_text(encoding="utf-8")
    assert "inject_resourcepack.py" not in text


def test_ancient_city_is_not_silently_repurposed_as_an_undead_factory():
    mappings = load_json(ROOT / "world/source-mappings.json")
    assert "minecraft:ancient_city" not in {item["structureId"] for item in mappings["sources"]}
