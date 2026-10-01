import ctypes
import ctypes.util
import json
from pathlib import Path
import struct
import sys
import zlib

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]/'infra'))
from region_inventory import SIGNATURE, linear_header, linear_slots
from pregen_controller import region_fingerprints
from world_size import measure


def sample(path, slots=(0, 33)):
    name = ctypes.util.find_library('zstd')
    if not name:
        pytest.skip('libzstd unavailable')
    native = ctypes.CDLL(name)
    native.ZSTD_compressBound.argtypes = [ctypes.c_size_t]
    native.ZSTD_compressBound.restype = ctypes.c_size_t
    native.ZSTD_compress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
    native.ZSTD_compress.restype = ctypes.c_size_t
    body = b''.join(struct.pack('>II', 3 if i in slots else 0, 123) for i in range(1024)) + b'NBT'*len(slots)
    source = ctypes.create_string_buffer(body)
    target = ctypes.create_string_buffer(native.ZSTD_compressBound(len(body)))
    length = native.ZSTD_compress(target, len(target), source, len(body), 3)
    compressed = target.raw[:length]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack('>QBQBHIQ', SIGNATURE, 1, 123, 3, len(slots), length,
        zlib.crc32(compressed)) + compressed + SIGNATURE.to_bytes(8, 'big'))


def test_valid_linear_slots_and_world_inventory(tmp_path):
    world = tmp_path/'world'
    path = world/'region/r.-1.2.linear'
    sample(path)
    assert linear_header(path)[0] == 2
    assert linear_slots(path) == [0, 33]
    assert set(region_fingerprints(world)) == {path.name}
    state = tmp_path/'state.json'
    state.write_text(json.dumps({}))
    report = measure(world, state)
    assert report['storedOverworldChunkEntries'] == 2
    assert report['savedOverworldBoundsBlocks'] == [-512, -481, 1024, 1055]


def test_empty_linear_region_does_not_trigger_pregen(tmp_path):
    world = tmp_path/'world'
    sample(world/'region/r.0.0.linear', ())
    assert region_fingerprints(world) == {}


def test_corrupt_or_incomplete_linear_refused(tmp_path):
    path = tmp_path/'r.0.0.linear'
    sample(path)
    data = bytearray(path.read_bytes())
    data[32] ^= 1
    path.write_bytes(data)
    with pytest.raises(ValueError, match='checksum'):
        linear_slots(path)
    path.write_bytes(data[:-8])
    with pytest.raises(ValueError, match='Incomplete'):
        linear_header(path)


def test_conversion_overlap_is_not_double_counted(tmp_path):
    world = tmp_path/'world'
    sample(world/'region/r.0.0.linear')
    (world/'region/r.0.0.mca').write_bytes(b'\0'*8192)
    with pytest.raises(RuntimeError, match='Duplicate'):
        region_fingerprints(world)
    with pytest.raises(ValueError, match='Duplicate'):
        measure(world, tmp_path/'missing-state.json')
