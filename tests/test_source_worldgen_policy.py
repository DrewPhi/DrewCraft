from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_focused_v1_does_not_override_wda_structure_sets():
    resources = ROOT / "mods/drewcraft/src/main/resources"
    pack = resources / "data/drewcraft/datapacks/source_worldgen"
    assert not pack.exists() or not any(path.is_file() for path in pack.rglob("*"))
    main = (ROOT / "mods/drewcraft/src/main/java/dev/drewcraft/DrewCraft.java").read_text(encoding="utf-8")
    assert "DrewCraftBuiltinPacks" not in main


def test_every_shipping_and_combined_smoke_workflow_builds_the_source_profile():
    for name in ("release-candidate-build.yml", "local-dev-release.yml", "full-profile-verify.yml", "server-smoke.yml"):
        text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert "--profile v1_1_integration" in text, name


def test_focused_v1_live_release_does_not_inject_covenant_resource_pack():
    text = (ROOT / ".github/workflows/local-dev-release.yml").read_text(encoding="utf-8")
    assert "inject_resourcepack.py" not in text
    assert "PACK_VERSION: 0.1.8-dev-local" in text
    assert "--minimum-launcher-version 0.1.8" in text
    assert "--server-address 150.136.96.174:25565" in text
    assert "--health-url http://150.136.96.174:25566/health" in text


def test_ancient_city_is_not_silently_repurposed_as_an_undead_factory():
    mappings = load_json(ROOT / "world/source-mappings.json")
    assert "minecraft:ancient_city" not in {item["structureId"] for item in mappings["sources"]}


def test_sparse_dungeon_placements_ship_as_a_world_datapack():
    overlay = ROOT / "pack/overlays/source_structures_first_spike"
    datapack = overlay / "datapacks/drewcraft-structures"
    assert load_json(datapack / "pack.mcmeta")["pack"]["pack_format"] == 48
    assert not any((overlay / "data/dungeons_arise").rglob("*.json"))
    for name, spacing, separation in (("major_structures", 1500, 1350), ("minor_structures", 675, 600)):
        structure_set = load_json(datapack / f"data/dungeons_arise/worldgen/structure_set/{name}.json")
        assert structure_set["placement"]["spacing"] == spacing
        assert structure_set["placement"]["separation"] == separation
    startup = (ROOT / "infra/start-server.sh").read_text(encoding="utf-8")
    assert "world/datapacks/drewcraft-structures" in startup
    assert "refusing mixed worldgen" in startup
