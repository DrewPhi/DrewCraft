"""Read-only native DH 3.3.1 base-section LOD evidence on isolated terrain."""
import argparse
import ctypes
import ctypes.util
import json
from pathlib import Path
import sqlite3


def decode(blob, mode):
    if mode == 0:
        return blob
    if mode != 4:
        raise ValueError(f'Unsupported evidence compression mode {mode}')
    native = ctypes.CDLL(ctypes.util.find_library('zstd'))
    native.ZSTD_getFrameContentSize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    native.ZSTD_getFrameContentSize.restype = ctypes.c_ulonglong
    native.ZSTD_decompress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
    native.ZSTD_decompress.restype = ctypes.c_size_t
    native.ZSTD_isError.argtypes = [ctypes.c_size_t]
    native.ZSTD_isError.restype = ctypes.c_uint
    source = ctypes.create_string_buffer(blob)
    size = native.ZSTD_getFrameContentSize(source, len(blob))
    if size > 64*1024*1024:
        raise ValueError('Invalid/oversized DH evidence frame')
    target = ctypes.create_string_buffer(size)
    decoded = native.ZSTD_decompress(target, size, source, len(blob))
    if native.ZSTD_isError(decoded) or decoded != size:
        raise ValueError('DH evidence decompression failed')
    return target.raw


def inspect(database, x, z):
    with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as connection:
        row = connection.execute('SELECT MinY, Data, ColumnGenerationStep, Mapping, DataFormatVersion, '
                                 'CompressionMode, DataChecksum, LastModifiedUnixDateTime FROM FullData '
                                 'WHERE DetailLevel=0 AND PosX=? AND PosZ=?', (x//64, z//64)).fetchone()
    if row is None:
        raise ValueError('Known cold terrain section has no LOD row')
    minimum, data, steps, mapping, version, mode, checksum, modified = row
    steps = decode(steps, mode)
    data = decode(data, mode)
    mapping = decode(mapping, mode)
    if len(steps) != 4096 or min(steps) < 7:
        raise ValueError('Known FULL terrain section has missing/partial LOD generation steps')
    if version != 2:
        raise ValueError(f'Unsupported DH evidence data version {version}')
    cursor = 0
    lengths = []
    for _ in range(62*62):
        value = 0
        shift = 0
        while True:
            if cursor >= len(data) or shift > 28:
                raise ValueError('Invalid LOD column lengths')
            byte = data[cursor]
            cursor += 1
            value |= (byte & 127) << shift
            if not byte & 128:
                break
            shift += 7
        lengths.append(value)
    if min(lengths) == 0 or not any(token in mapping for token in
                                      (b'minecraft:stone', b'minecraft:water', b'minecraft:dirt')):
        raise ValueError('LOD has empty columns or lacks expected real terrain mapping')
    return {'sectionX': x//64, 'sectionZ': z//64, 'minY': minimum,
            'interiorColumns': len(lengths), 'nonemptyColumns': sum(n>0 for n in lengths),
            'minimumGenerationStep': min(steps), 'maximumGenerationStep': max(steps),
            'checksum': checksum, 'modifiedUnix': modified, 'uncompressedDataBytes': len(data)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('database', type=Path)
    parser.add_argument('x', type=int)
    parser.add_argument('z', type=int)
    args = parser.parse_args()
    print(json.dumps(inspect(args.database, args.x, args.z)), flush=True)
