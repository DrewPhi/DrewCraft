import importlib.util
from pathlib import Path
import struct
import zlib

import pytest

spec = importlib.util.spec_from_file_location('storage_benchmark', Path(__file__).parents[1]/'infra/storage_benchmark.py')
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


def region():
    raw = bytearray(5*4096)
    raw[:4] = ((4 << 8) | 1).to_bytes(4, 'big')
    raw[4096:4100] = (123).to_bytes(4, 'big')
    data = b'\x02' + zlib.compress(b'test NBT payload')
    raw[4*4096:4*4096+4] = struct.pack('>I', len(data))
    raw[4*4096+4:4*4096+4+len(data)] = data
    return raw


def test_compaction_preserves_payload_timestamp_and_source(tmp_path):
    source, target = tmp_path/'source.mca', tmp_path/'target.mca'
    source.write_bytes(region())
    result = bench.compact(source, target)
    assert result['reclaimedBytes'] == 8192
    assert source.read_bytes() == region()
    assert target.read_bytes()[4096:8192] == source.read_bytes()[4096:8192]


def test_invalid_location_refused(tmp_path):
    source = tmp_path/'source.mca'
    raw = region()
    raw[:4] = ((10 << 8) | 1).to_bytes(4, 'big')
    source.write_bytes(raw)
    with pytest.raises(ValueError, match='location'):
        bench.compact(source, tmp_path/'target.mca')
