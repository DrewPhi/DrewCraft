from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

MODULE = Path(__file__).parents[1] / "tools" / "drewcraft_pack.py"
SPEC = importlib.util.spec_from_file_location("drewcraft_pack", MODULE)
assert SPEC and SPEC.loader
pack = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pack
SPEC.loader.exec_module(pack)


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def fixture_repo(root: Path) -> Path:
    write_yaml(root / "pack/manifest/profiles.yaml", {
        "registries": {"foundation": "pack/manifest/upstreams.yaml", "performance": "pack/manifest/performance_candidates.yaml", "gameplay_spikes": "pack/manifest/mob_structure_candidates.yaml"},
        "profiles": {
            "base": {"foundation": ["a"], "performance_baseline": ["b"]},
            "hostile_a": {"extends": ["base"], "gameplay_components": ["c"], "incompatible_profiles": ["hostile_b"], "overlays": ["pack/overlays/hostile_a"]},
            "hostile_b": {"extends": ["base"], "gameplay_components": ["d"], "incompatible_profiles": ["hostile_a"]},
            "without_b": {"extends": ["base"], "exclude_dependencies": ["b"]},
            "bad_exclude": {"extends": ["base"], "exclude_dependencies": ["lib"]},
        },
    })
    write_yaml(root / "pack/manifest/upstreams.yaml", {"upstreams": {"a": {"side": "common", "artifact": {"provider": "curseforge", "project_id": 1, "file_id": 2, "candidate_version": "1", "filename": "a.jar"}}}})
    write_yaml(root / "pack/manifest/performance_candidates.yaml", {"baseline": {"b": {"side": "client", "provider": "curseforge", "project_id": 3, "file_id": 4, "candidate_version": "1", "required_dependencies": ["lib"]}}, "libraries": {"lib": {"provider": "curseforge", "project_id": 5, "file_id": 6}}, "experimental": {}})
    write_yaml(root / "pack/manifest/mob_structure_candidates.yaml", {"candidate_sets": {"hostile": {"branches": [{"id": "c", "provider": "curseforge", "project_id": 7, "file_id": 8}, {"id": "d", "provider": "curseforge", "project_id": 9, "file_id": 10}]}}})
    return root


def loaded(root: Path):
    profiles = pack.load_yaml(root / "pack/manifest/profiles.yaml")
    return profiles, pack.collect_catalog(root, profiles)


def test_profile_resolution_is_deterministic_and_transitive(tmp_path: Path):
    profiles, catalog = loaded(fixture_repo(tmp_path))
    resolved = pack.resolve(["hostile_a"], profiles, catalog)
    assert resolved["ordered_ids"] == ["a", "lib", "b", "c"]
    assert pack.make_plan(resolved, catalog)["unresolved_identity_count"] == 0


def test_profile_can_exclude_inherited_root(tmp_path: Path):
    profiles, catalog = loaded(fixture_repo(tmp_path))
    resolved = pack.resolve(["without_b"], profiles, catalog)
    assert resolved["ordered_ids"] == ["a"]
    assert resolved["excluded_ids"] == ["b"]
    assert pack.make_plan(resolved, catalog)["excluded_dependencies"] == ["b"]


def test_excluding_required_transitive_fails_closed(tmp_path: Path):
    profiles, catalog = loaded(fixture_repo(tmp_path))
    with pytest.raises(pack.PackError, match="excludes dependency lib required by b"):
        pack.resolve(["bad_exclude"], profiles, catalog)


def test_incompatible_profiles_fail_closed(tmp_path: Path):
    profiles, catalog = loaded(fixture_repo(tmp_path))
    with pytest.raises(pack.PackError, match="incompatible profiles"):
        pack.resolve(["hostile_a", "hostile_b"], profiles, catalog)


def test_unknown_dependency_fails_closed(tmp_path: Path):
    root = fixture_repo(tmp_path)
    doc = yaml.safe_load((root / "pack/manifest/performance_candidates.yaml").read_text())
    doc["baseline"]["b"]["required_dependencies"] = ["missing"]
    write_yaml(root / "pack/manifest/performance_candidates.yaml", doc)
    profiles, catalog = loaded(root)
    with pytest.raises(pack.PackError, match="unknown candidate"):
        pack.resolve(["base"], profiles, catalog)


def test_side_filtering():
    assert pack.side_allowed("client", "client")
    assert not pack.side_allowed("client", "server")
    assert pack.side_allowed("server", "server")
    assert not pack.side_allowed("server", "client")
    assert pack.side_allowed("common", "client") and pack.side_allowed("common", "server")


def test_layout_hash_verification(tmp_path: Path):
    root = tmp_path / "layout"; mods = root / "mods"; mods.mkdir(parents=True)
    jar = mods / "x.jar"; jar.write_bytes(b"good")
    (root / "drewcraft-layout.json").write_text(json.dumps({"files": [{"id": "x", "path": "mods/x.jar", "sha256": pack.sha256(jar)}]}))
    pack.verify(root)
    jar.write_bytes(b"changed")
    with pytest.raises(pack.PackError, match="bad_hash"):
        pack.verify(root)


def test_profile_overlay_is_resolved_built_and_hash_verified(tmp_path: Path):
    root = fixture_repo(tmp_path)
    overlay = root / "pack/overlays/hostile_a/config/fml.toml"
    overlay.parent.mkdir(parents=True)
    overlay.write_text('dependencyOverrides.c = ["-minecraft"]\n', encoding="utf-8")
    profiles, catalog = loaded(root)
    resolved = pack.resolve(["hostile_a"], profiles, catalog)
    plan = pack.make_plan(resolved, catalog)
    assert plan["overlays"] == ["pack/overlays/hostile_a"]
    for dep in plan["dependencies"]:
        artifact = tmp_path / f"{dep['id']}.jar"
        artifact.write_bytes(dep["id"].encode())
        dep["fetch"] = {
            "status": "ok", "path": str(artifact), "filename": artifact.name,
            "sha256": pack.sha256(artifact),
        }
    output = tmp_path / "output"
    pack.build(plan, output, "client", root)
    assert (output / "client/config/fml.toml").read_text(encoding="utf-8") == overlay.read_text(encoding="utf-8")
    pack.verify(output / "client")
    (output / "client/config/fml.toml").write_text("changed\n", encoding="utf-8")
    with pytest.raises(pack.PackError, match="bad_hash"):
        pack.verify(output / "client")


def test_source_structure_profile_has_exact_worldgen_policy():
    root = MODULE.parents[1]
    profiles = pack.load_yaml(root / "pack/manifest/profiles.yaml")
    catalog = pack.collect_catalog(root, profiles)
    resolved = pack.resolve(["source_structures_first_spike"], profiles, catalog)
    plan = pack.make_plan(resolved, catalog)
    ids = {dep["id"] for dep in plan["dependencies"]}
    assert {"towns_and_towers", "cristel_lib", "when_dungeons_arise"} <= ids
    assert plan["overlays"] == ["pack/overlays/source_structures_first_spike"]


def test_production_profile_resolves_moreculling_cloth_config_dependency():
    root = MODULE.parents[1]
    profiles = pack.load_yaml(root / "pack/manifest/profiles.yaml")
    catalog = pack.collect_catalog(root, profiles)
    resolved = pack.resolve(["stage2_base_performance"], profiles, catalog)
    moreculling = resolved["ordered_ids"].index("moreculling")
    cloth = resolved["ordered_ids"].index("cloth_config")
    assert cloth < moreculling
    assert catalog["cloth_config"]["side"] == "client"


def test_playtest_01_excludes_sable_incompatible_optimizers():
    root = MODULE.parents[1]
    profiles = pack.load_yaml(root / "pack/manifest/profiles.yaml")
    catalog = pack.collect_catalog(root, profiles)
    resolved = pack.resolve(["playtest_01"], profiles, catalog)
    assert {"embeddium", "scalablelux"} <= set(resolved["excluded_ids"])
    assert "embeddium" not in resolved["ordered_ids"]
    assert "scalablelux" not in resolved["ordered_ids"]
    assert "sable" in resolved["ordered_ids"]


def test_v1_shipping_profile_is_focused_and_complete():
    root = MODULE.parents[1]
    profiles = pack.load_yaml(root / "pack/manifest/profiles.yaml")
    catalog = pack.collect_catalog(root, profiles)
    resolved = pack.resolve(["v1_survival_exploration"], profiles, catalog)
    ids = set(resolved["ordered_ids"])

    assert {
        "terrain_diffusion_plus", "distant_horizons", "create", "create_radars",
        "immersive_vehicles", "mts_official_pack", "create_big_cannons",
        "create_gunsmithing", "create_aeronautics", "create_high_seas",
        "when_dungeons_arise", "sable", "ntgl", "cloth_config",
    } <= ids
    assert {
        "project_atmosphere", "simple_clouds", "serene_seasons",
        "illager_invasion", "towns_and_towers", "embeddium", "scalablelux",
        "cbc_firepower_components",
    }.isdisjoint(ids)
    assert resolved["overlays"] == ["pack/overlays/source_structures_first_spike"]
