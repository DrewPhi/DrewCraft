"""Idle DH catch-up, region deltas, and pause/restart behavior."""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "infra"))
spec = importlib.util.spec_from_file_location("dh_incremental", ROOT / "infra/pregen_controller.py")
pregen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pregen)


def controller(tmp_path):
    obj = pregen.Controller.__new__(pregen.Controller)
    obj.world = tmp_path / "world"
    (obj.world / "region").mkdir(parents=True)
    (obj.world / "data").mkdir()
    (obj.world / "data/DistantHorizons.sqlite").write_bytes(b"database")
    obj.args = SimpleNamespace(dh_change_check_seconds=60, maximum_radius=1_000_000,
                               idle_grace_seconds=600)
    obj.state = {"phase": "complete", "centerX": -1536, "centerZ": -1536,
                 "activeRadius": 130048, "dhRadius": 10304}
    obj.save = lambda **updates: obj.state.update(updates)
    obj.start_dh = mock.Mock(side_effect=lambda radius: obj.save(
        dhTargetRadius=radius, dhStarted=True))
    obj.health = mock.Mock()
    obj.write_boundary = mock.Mock()
    return obj


def region(obj, name, extra=b""):
    path = obj.world / "region" / name
    path.write_bytes(b"\0" * 8192 + extra)
    return path


def test_initial_catchup_uses_real_bounds_instead_of_legacy_radius(tmp_path):
    obj = controller(tmp_path)
    region(obj, "r.-25.-1.mca")
    assert obj.maintain_dh()
    job = obj.state["dhActiveJob"]
    assert job["kind"] == "catchup"
    assert job["radius"] == 11328
    obj.finish_dh_job()
    obj.state["dhLastRegionCheckEpoch"] = 0
    assert not obj.maintain_dh()  # no perpetual full-world sweep


def test_changes_during_pass_are_not_lost_and_new_regions_are_queued(tmp_path):
    obj = controller(tmp_path)
    path = region(obj, "r.0.0.mca")
    obj.maintain_dh()
    original = dict(obj.state["dhActiveJob"]["regions"])
    path.write_bytes(path.read_bytes() + b"changed while DH runs")
    region(obj, "r.-25.-1.mca")
    obj.finish_dh_job()
    assert obj.state["dhRegionBaseline"] == original
    obj.state["dhLastRegionCheckEpoch"] = 0
    assert obj.maintain_dh()
    jobs = [obj.state["dhActiveJob"], *obj.state["dhPendingJobs"]]
    assert len(jobs) == 2
    assert all(job["kind"] == "changed_regions" for job in jobs)
    assert jobs[0]["centerX"] == 1024  # nearest center first
    assert jobs[1]["centerX"] == -13312  # new terrain beyond original scan


def test_replaced_lod_database_requires_new_catchup(tmp_path):
    obj = controller(tmp_path)
    region(obj, "r.0.0.mca")
    obj.maintain_dh()
    obj.finish_dh_job()
    replacement = obj.world / "data/replacement.sqlite"
    replacement.write_bytes(b"replacement")
    replacement.replace(obj.world / "data/DistantHorizons.sqlite")
    obj.state["dhLastRegionCheckEpoch"] = 0
    assert obj.maintain_dh()
    assert obj.state["dhActiveJob"]["kind"] == "catchup"


def test_join_pauses_then_empty_server_resumes_same_job_after_grace(tmp_path):
    obj = controller(tmp_path)
    region(obj, "r.0.0.mca")
    obj.maintain_dh()
    obj.state["dhStarted"] = True
    job = obj.state["dhActiveJob"]
    obj.rcon = mock.Mock(return_value="There are 1 of a max of 10 players online")
    assert not obj.idle_window()
    assert mock.call("dh", "pregen", "stop") in obj.rcon.call_args_list
    obj.start_dh.reset_mock()
    obj.rcon.return_value = "There are 0 of a max of 10 players online"
    with mock.patch.object(pregen.time, "time", return_value=1000):
        assert not obj.idle_window()
    with mock.patch.object(pregen.time, "time", return_value=1601):
        assert obj.idle_window()
    obj.start_dh.assert_called_once_with(job["radius"])
    assert obj.state["dhActiveJob"] == job


def test_restart_keeps_pending_jobs_and_region_baseline(tmp_path):
    obj = controller(tmp_path)
    region(obj, "r.0.0.mca")
    obj.maintain_dh()
    obj.finish_dh_job()
    region(obj, "r.1.1.mca")
    obj.state["dhLastRegionCheckEpoch"] = 0
    obj.maintain_dh()
    state_path = tmp_path / "pregen.json"
    state_path.write_text(json.dumps(obj.state))
    args = SimpleNamespace(world=str(obj.world), state_file=str(state_path),
                           health_file=str(tmp_path / "health.json"),
                           password_file=str(tmp_path / "unused"), benchmark_radius=1024)
    restarted = pregen.Controller(args)
    assert restarted.state["dhActiveJob"] == obj.state["dhActiveJob"]
    assert restarted.state["dhRegionBaseline"] == obj.state["dhRegionBaseline"]


def test_native_job_resume_uses_targeted_center_not_spawn(tmp_path):
    obj = controller(tmp_path)
    obj.state["dhActiveJob"] = {"centerX": 3072, "centerZ": -1024}
    obj.rcon = mock.Mock(side_effect=["Changed setting", "Changed setting", "Starting pregen"])
    obj.start_dh = pregen.Controller.start_dh.__get__(obj)
    with mock.patch.object(Path, "stat", return_value=SimpleNamespace(st_ino=1, st_size=0)):
        obj.start_dh(1088)
    assert obj.rcon.call_args_list[-1] == mock.call(
        "dh", "pregen", "start", "overworld", "3072", "-1024", "68")


def test_chunky_growth_queues_every_new_saved_region_beyond_first_scan(tmp_path):
    obj = controller(tmp_path)
    region(obj, "r.0.0.mca")
    obj.maintain_dh()
    obj.finish_dh_job()
    new_names = {"r.-40.-40.mca", "r.40.-40.mca",
                 "r.-40.40.mca", "r.40.40.mca"}
    for name in new_names:
        region(obj, name)
    obj.state["dhLastRegionCheckEpoch"] = 0
    assert obj.maintain_dh()
    jobs = [obj.state["dhActiveJob"], *obj.state["dhPendingJobs"]]
    assert {name for job in jobs for name in job["regions"]} == new_names
    for job in jobs:
        for name in job["regions"]:
            rx, rz = pregen.region_coordinates(name)
            for x in (rx * 512, (rx + 1) * 512):
                for z in (rz * 512, (rz + 1) * 512):
                    assert abs(x - job["centerX"]) <= job["radius"]
                    assert abs(z - job["centerZ"]) <= job["radius"]


def test_empty_chunky_region_placeholders_are_not_saved_terrain(tmp_path):
    obj = controller(tmp_path)
    saved = region(obj, "r.0.0.mca")
    (obj.world / "region/r.100.100.mca").touch()
    assert set(pregen.region_fingerprints(obj.world)) == {saved.name}


def test_continuous_expansion_waits_for_dh_and_uses_verified_frontier(tmp_path):
    obj = controller(tmp_path)
    obj.state.update(continuousCompletedRadius=6144, targetBytes=50_000)
    obj.args.generation_batch_blocks = 1024
    obj.start_continuous_chunky = mock.Mock()
    obj.maintain_dh = mock.Mock(return_value=True)
    obj.continuous_chunky_step(10_000)
    obj.start_continuous_chunky.assert_not_called()
    obj.maintain_dh.return_value = False
    obj.continuous_chunky_step(10_000)
    obj.start_continuous_chunky.assert_called_once_with(7168)


def test_continuous_size_target_keeps_dh_but_stops_expansion(tmp_path):
    obj = controller(tmp_path)
    obj.state.update(continuousCompletedRadius=6144, targetBytes=50_000)
    obj.maintain_dh = mock.Mock(return_value=False)
    obj.start_continuous_chunky = mock.Mock()
    obj.continuous_chunky_step(50_000)
    obj.maintain_dh.assert_called_once()
    obj.start_continuous_chunky.assert_not_called()


def test_missing_chunky_task_never_counts_as_completed_radius(tmp_path):
    obj = controller(tmp_path)
    obj.state.update(phase="continuous_chunky", continuousCompletedRadius=6144,
                     continuousTargetRadius=7168, chunkyLogInode=1, chunkyLogOffset=0)
    obj.rcon = mock.Mock(side_effect=["No tasks running.", "No tasks to continue."])
    obj.start_continuous_chunky = mock.Mock()
    with mock.patch.object(Path, "stat", return_value=SimpleNamespace(st_ino=2, st_size=0)):
        obj.continuous_chunky_step(10_000)
    assert obj.state["continuousCompletedRadius"] == 6144
    obj.start_continuous_chunky.assert_called_once_with(7168)


def test_chunky_real_completion_advances_then_requests_dh(tmp_path):
    import io
    obj = controller(tmp_path)
    obj.state.update(phase="continuous_chunky", continuousCompletedRadius=6144,
                     continuousTargetRadius=7168, chunkyLogInode=1, chunkyLogOffset=0)
    obj.rcon = mock.Mock(return_value="No tasks running.")
    with mock.patch.object(Path, "stat", return_value=SimpleNamespace(st_ino=1, st_size=100)), \
            mock.patch.object(Path, "open", return_value=io.BytesIO(
                b"[Chunky] Task finished for minecraft:overworld. Processed: 600000 chunks (100.00%), Total time: 1:00:00")):
        obj.continuous_chunky_step(10_000)
    assert obj.state["continuousCompletedRadius"] == 7168
    assert obj.state["phase"] == "complete"
    assert obj.state["dhLastRegionCheckEpoch"] == 0


def test_boundary_uses_completed_circle_not_active_target_and_keeps_buffer(tmp_path):
    obj = controller(tmp_path)
    obj.boundary_path = tmp_path / "boundary.json"
    obj.state.update(enforcePregenBoundary=True, continuousCompletedRadius=6144,
                     activeRadius=7168, boundaryBufferBlocks=320)
    pregen.Controller.write_boundary(obj, 7168)
    result = json.loads(obj.boundary_path.read_text())
    assert result["enabled"] is True
    assert result["dimension"] == "minecraft:overworld"
    assert result["radiusBlocks"] == 5824
    assert result["generatedRadiusBlocks"] == 6144


def test_disabled_boundary_remains_telemetry_only(tmp_path):
    obj = controller(tmp_path)
    obj.boundary_path = tmp_path / "boundary.json"
    pregen.Controller.write_boundary(obj, 7168)
    result = json.loads(obj.boundary_path.read_text())
    assert result["enabled"] is False
    assert result["radiusBlocks"] == 7168


def test_size_target_pauses_active_batch_without_marking_it_complete(tmp_path):
    obj = controller(tmp_path)
    obj.state.update(continuousChunky=True, targetBytes=150_000,
                     phase="continuous_chunky", continuousCompletedRadius=6144)
    obj.rcon = mock.Mock(return_value="Paused")
    assert not obj.pause_at_size_target(149_999)
    obj.rcon.assert_not_called()
    assert obj.pause_at_size_target(150_000)
    assert obj.state["phase"] == "size_paused"
    assert obj.state["sizePausedFromPhase"] == "continuous_chunky"
    assert obj.state["continuousCompletedRadius"] == 6144
    assert obj.rcon.call_args_list == [mock.call("chunky", "pause"), mock.call("dh", "pregen", "stop")]
    assert obj.pause_at_size_target(150_001)
    assert obj.rcon.call_count == 2


def test_size_target_also_pauses_dh_and_higher_budget_allows_resume(tmp_path):
    obj = controller(tmp_path)
    obj.state.update(continuousChunky=True, targetBytes=150_000, phase="dh", dhStarted=True)
    obj.rcon = mock.Mock(return_value="Paused")
    assert obj.pause_at_size_target(150_000)
    assert obj.state["sizePausedFromPhase"] == "dh"
    assert obj.state["dhStarted"] is False
    obj.state["targetBytes"] = 200_000
    assert not obj.pause_at_size_target(150_000)
