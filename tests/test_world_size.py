import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'infra'))
spec = importlib.util.spec_from_file_location("world_size", ROOT / "infra/world_size.py")
world_size = importlib.util.module_from_spec(spec)
spec.loader.exec_module(world_size)


def fixture(tmp_path, state):
    world = tmp_path / "world"
    (world / "region").mkdir(parents=True)
    state_path = tmp_path / "pregen.json"
    state_path.write_text(json.dumps(state))
    return world, state_path


def test_disk_usage_includes_all_dimensions_and_dh(tmp_path):
    world, state = fixture(tmp_path, {})
    (world / "DIM-1").mkdir()
    (world / "DIM-1/nether.dat").write_bytes(b"123")
    (world / "DistantHorizons.sqlite-wal").write_bytes(b"12345")
    report = world_size.measure(world, state)
    assert report["worldSizeBytes"] == 8
    assert report["dhSizeBytes"] == 5


def test_empty_placeholders_never_count_as_chunks_or_expand_bounds(tmp_path):
    world, state = fixture(tmp_path, {})
    (world / "region/r.100.100.mca").touch()
    header = bytearray(8192)
    header[:4] = bytes([0, 0, 2, 1])
    (world / "region/r.-1.2.mca").write_bytes(header)
    report = world_size.measure(world, state)
    assert report["storedOverworldChunkEntries"] == 1
    assert report["savedOverworldBoundsBlocks"] == [-512, -497, 1024, 1039]
    assert report["emptyOrShortRegionPlaceholders"] == 1


def test_completed_and_in_progress_are_distinct(tmp_path):
    world, state = fixture(tmp_path, {"continuousChunky": True, "continuousCompletedRadius": 6144,
        "continuousTargetRadius": 7168, "phase": "continuous_chunky", "activeRadius": 130048,
        "enforcePregenBoundary": True, "boundaryBufferBlocks": 320})
    report = world_size.measure(world, state)
    assert report["chunkyCompletedRadiusBlocks"] == 6144
    assert report["chunkyCompletedDiameterBlocks"] == 12288
    assert report["chunkyInProgressTargetRadiusBlocks"] == 7168
    assert report["playableRadiusBlocks"] == 5824
    assert "NOT completed" in world_size.render(report)


def test_legacy_counters_are_never_reported_as_completed(tmp_path):
    world, state = fixture(tmp_path, {"activeRadius": 130048, "chunkyRadius": 130048})
    report = world_size.measure(world, state)
    assert report["chunkyCompletedRadiusBlocks"] is None
    assert "unknown (legacy counters ignored)" in world_size.render(report)


def test_missing_checkpoint_still_measures_live_files(tmp_path):
    world, state = fixture(tmp_path, {})
    state.unlink()
    assert world_size.measure(world, state)["worldSizeBytes"] == 0
