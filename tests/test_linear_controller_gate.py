"""Controller checkpoint and player-pause contracts used by the Linear gate."""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "infra"))
spec = importlib.util.spec_from_file_location("pregen_controller_gate", ROOT / "infra/pregen_controller.py")
controller_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = controller_module
spec.loader.exec_module(controller_module)


def make_controller(tmp_path, state):
    world = tmp_path / "world"
    world.mkdir()
    state_path = tmp_path / "pregen.json"
    state_path.write_text(json.dumps(state))
    args = SimpleNamespace(world=str(world), state_file=str(state_path),
                           health_file=str(tmp_path / "health.json"),
                           password_file=str(tmp_path / "password"), rcon_port=25586,
                           center_x=0, center_z=0, benchmark_radius=1024,
                           idle_grace_seconds=600)
    return controller_module.Controller(args), state_path


def test_player_join_pauses_both_generators_and_persists_checkpoint(tmp_path):
    state = {"schemaVersion": 2, "phase": "dh", "dhStarted": True,
             "dhTargetRadius": 4096, "dhRadius": 3584, "chunkyRadius": 4096,
             "maintenancePaused": False}
    controller, state_path = make_controller(tmp_path, state)
    calls = []

    def rcon(*command):
        calls.append(command)
        return "There are 1 of a max of 10 players online" if command == ("list",) else "stopped"

    with patch.object(controller, "rcon", side_effect=rcon):
        assert controller.idle_window() is False

    saved = json.loads(state_path.read_text())
    assert calls == [("list",), ("chunky", "pause"), ("dh", "pregen", "stop")]
    assert saved["maintenancePaused"] is True
    assert saved["phase"] == "dh"
    assert saved["dhStarted"] is True
    assert saved["dhTargetRadius"] == 4096
    assert saved["chunkyRadius"] == 4096


def test_empty_server_resumes_saved_dh_target_after_idle_grace(tmp_path):
    state = {"schemaVersion": 2, "phase": "dh", "dhStarted": True,
             "dhTargetRadius": 4096, "dhRadius": 3584,
             "maintenancePaused": True, "idleSince": 1}
    controller, state_path = make_controller(tmp_path, state)
    with (patch.object(controller, "rcon", return_value="There are 0 of a max of 10 players online"),
          patch.object(controller, "start_dh") as start_dh,
          patch.object(controller_module.time, "time", return_value=1000)):
        assert controller.idle_window() is True

    start_dh.assert_called_once_with(4096)
    saved = json.loads(state_path.read_text())
    assert saved["maintenancePaused"] is False
    assert saved["dhTargetRadius"] == 4096


def test_controller_reloads_inflight_checkpoint_without_resetting_frontier(tmp_path):
    state = {"schemaVersion": 2, "phase": "continuous_chunky",
             "continuousChunky": True, "continuousCompletedRadius": 6144,
             "continuousTargetRadius": 7168, "chunkyRadius": 7168,
             "dhRadius": 6656, "dhStarted": False}
    first, state_path = make_controller(tmp_path, state)
    second = controller_module.Controller(first.args)
    assert second.state["phase"] == "continuous_chunky"
    assert second.state["continuousCompletedRadius"] == 6144
    assert second.state["continuousTargetRadius"] == 7168
    assert second.state["chunkyRadius"] == 7168
    assert second.state["dhRadius"] == 6656
    assert state_path.is_file()
