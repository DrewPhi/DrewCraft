import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "infra"))
import linear_java_acceptance as acceptance


def test_loaded_chunk_probe_accepts_nested_time_command_output():
    assert acceptance.loaded_response("The time is 19779199")


def test_loaded_chunk_probe_accepts_execute_test_text():
    assert acceptance.loaded_response("Test passed")


def test_loaded_chunk_probe_rejects_unloaded_or_unexpected_output():
    assert not acceptance.loaded_response("Test failed")
    assert not acceptance.loaded_response("Unexpected output")


def test_empty_loaded_chunk_probe_response_is_pending_not_an_error():
    assert acceptance.pending_loaded_response("")
    assert acceptance.pending_loaded_response("Test failed")
    assert not acceptance.pending_loaded_response("The time is 19779199")
    assert not acceptance.pending_loaded_response("Unexpected output")


def test_forceload_ack_accepts_recorded_production_forms():
    assert acceptance.forceload_accepted(
        "Marked chunk [-177, 47] in Overworld to be force loaded")
    assert acceptance.forceload_accepted(
        "No chunks were marked for force loading")


def test_forceload_ack_rejects_errors():
    assert not acceptance.forceload_accepted("")
    assert not acceptance.forceload_accepted("Unknown command")
    assert not acceptance.forceload_accepted("An error occurred")
