"""DH pyramid backfill: holes under unchanged chunks get their own gate."""
import importlib.util
import sqlite3
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "infra"))
spec = importlib.util.spec_from_file_location("pregen_controller_gate", ROOT / "infra/pregen_controller.py")
controller_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = controller_module
spec.loader.exec_module(controller_module)


def database(path, rows):
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE FullData(DetailLevel,PosX,PosZ,MinY,Data)")
        conn.executemany("INSERT INTO FullData VALUES(?,?,?,0,x'00')", rows)


def test_pyramid_gap_lists_only_missing_children_finest_first(tmp_path):
    database(tmp_path / "dh.sqlite", [(1, 0, 0), (0, 0, 0), (0, 1, 0), (0, 0, 1)])
    assert controller_module.dh_pyramid_gaps(tmp_path / "dh.sqlite") == [(0, 1, 1)]


def test_complete_pyramid_and_missing_database_are_clean(tmp_path):
    rows = [(1, 5, 5)] + [(0, 10 + dx, 10 + dz) for dx in (0, 1) for dz in (0, 1)]
    database(tmp_path / "dh.sqlite", rows)
    assert controller_module.dh_pyramid_gaps(tmp_path / "dh.sqlite") == []
    assert controller_module.dh_pyramid_gaps(tmp_path / "absent.sqlite") == []


def test_frontier_is_ignored_but_saved_terrain_gap_is_retained(tmp_path):
    db = tmp_path / "dh.sqlite"
    database(db, [(1, 0, 0), (0, 0, 0), (0, 1, 0), (0, 0, 1)])
    world = tmp_path / "world"
    (world / "region").mkdir(parents=True)
    assert controller_module.dh_pyramid_gaps(db, saved_world=world) == []
    header = bytearray(4096)
    slot = 4 * 32 + 4  # A saved chunk beneath the missing 64-block cell.
    header[slot*4:slot*4+4] = bytes([0, 0, 2, 1])
    (world / "region/r.0.0.mca").write_bytes(header)
    assert controller_module.dh_pyramid_gaps(db, saved_world=world) == [(0, 1, 1)]


def test_coarse_frontier_is_ignored_without_base_lods_beneath_it(tmp_path):
    db = tmp_path / "dh.sqlite"
    database(db, [(2, 0, 0), (1, 0, 0), (0, 0, 0)])
    world = tmp_path / "world"
    (world / "region").mkdir(parents=True)
    assert controller_module.dh_pyramid_gaps(db, saved_world=world) == []


def make_controller(tmp_path, state):
    world = tmp_path / "world"
    (world / "data").mkdir(parents=True, exist_ok=True)
    state_path = tmp_path / "pregen.json"
    import json
    state_path.write_text(json.dumps(state))
    args = SimpleNamespace(world=str(world), state_file=str(state_path),
                           health_file=str(tmp_path / "health.json"),
                           password_file=str(tmp_path / "password"), rcon_port=25586,
                           center_x=0, center_z=0, benchmark_radius=1024,
                           idle_grace_seconds=600)
    return controller_module.Controller(args)


def test_backfill_queues_before_chunky_expansion(tmp_path):
    state = {"schemaVersion": 2, "phase": "complete", "centerX": 0, "centerZ": 0}
    controller = make_controller(tmp_path, state)
    with (patch.object(controller_module, "dh_pyramid_gaps", return_value=[(0, 1, 1)]),
          patch.object(controller_module, "region_fingerprints",
                       return_value={"r.0.0.linear": [1, 2]}),
          patch.object(controller_module, "existing_world_radius", return_value=1024)):
        assert controller.maintain_dh_backfill() is True
    assert controller.state["dhPendingJobs"][0]["kind"] == "backfill"


def test_backfill_skips_clean_or_busy_controller(tmp_path):
    state = {"schemaVersion": 2, "phase": "complete", "centerX": 0, "centerZ": 0}
    controller = make_controller(tmp_path, state)
    with patch.object(controller_module, "dh_pyramid_gaps", return_value=[]):
        assert controller.maintain_dh_backfill() is False
    assert "dhPendingJobs" not in controller.state
    busy = make_controller(tmp_path, {"schemaVersion": 2, "centerX": 0, "centerZ": 0, "dhActiveJob": {"kind": "x"}})
    with patch.object(controller_module, "dh_pyramid_gaps",
                      side_effect=AssertionError("must not scan while busy")):
        assert busy.maintain_dh_backfill() is False
