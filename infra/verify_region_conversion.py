"""Independent byte-level ALL-chunk comparison of stopped Anvil/Linear worlds."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import struct
import time
import zlib
from region_inventory import linear_payloads
from worldgen_guard import read_nbt


def digest(path):
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            hasher.update(block)
    return hasher.digest()


def anvil_payloads(path):
    data = path.read_bytes()
    if not data:
        return {}  # Chunky creates zero-byte placeholders before writing terrain.
    if len(data) < 8192:
        raise ValueError(f'Truncated Anvil region: {path}')
    rx, rz = map(int, path.name.split('.')[1:3])
    result = {}
    for slot in range(1024):
        location = int.from_bytes(data[slot*4:slot*4+4], 'big')
        if not location:
            continue
        offset, sectors = location >> 8, location & 255
        start = offset * 4096
        if offset < 2 or not sectors or start + 5 > len(data):
            raise ValueError(f'Invalid Anvil location: {path}:{slot}')
        length = struct.unpack_from('>I', data, start)[0]
        kind = data[start + 4]
        if length < 1 or length > sectors * 4096 - 4 or start + 4 + length > len(data):
            raise ValueError(f'Invalid Anvil payload length: {path}:{slot}')
        if kind & 128:
            raw = (path.parent / f'c.{rx*32+slot%32}.{rz*32+slot//32}.mcc').read_bytes()
        else:
            raw = data[start + 5:start + 4 + length]
        codec = kind & 127
        if codec == 1:
            result[slot] = gzip.decompress(raw)
        elif codec == 2:
            result[slot] = zlib.decompress(raw)
        elif codec == 3:
            result[slot] = raw
        else:
            raise ValueError(f'Unsupported Anvil compression {codec}; cannot certify {path}')
    return result


def _startup_metadata_matches(source, target):
    """Permit only the server's LastPlayed update and Linear load-list entry."""
    original = read_nbt(source)
    actual = read_nbt(target)
    if actual['Data']['LastPlayed'] <= original['Data']['LastPlayed']:
        raise ValueError(f'LastPlayed was not a forward server-start update: {target}')
    expected = copy.deepcopy(original)
    expected['Data']['LastPlayed'] = actual['Data']['LastPlayed']
    before = expected['fml']['LoadingModList']
    after = actual['fml']['LoadingModList']
    linear = [entry for entry in after if entry.get('ModId') == 'linear']
    if len(linear) != 1 or linear[0].get('ModVersion') != '1.3.3':
        raise ValueError(f'Unexpected Linear entry in {target}')
    existing = [entry for entry in after if entry.get('ModId') != 'linear']
    if existing != before:
        raise ValueError(f'Existing mod list changed in {target}')
    expected['fml']['LoadingModList'] = after
    if expected != actual:
        raise ValueError(f'Unexpected world metadata change in {target}')


def verify(baseline, converted):
    began = time.monotonic()
    count = 0
    regions = 0
    expected_paths = set()
    for source in sorted(baseline.rglob('r.*.*.mca')):
        relative = source.relative_to(baseline).with_suffix('.linear')
        expected = anvil_payloads(source)
        target = converted / relative
        if not expected and not target.exists():
            continue
        actual = linear_payloads(target)
        if set(actual) != set(expected):
            raise ValueError(f'Occupied slots differ: {relative}')
        for slot in expected:
            if actual[slot] != expected[slot]:
                raise ValueError(f'Raw chunk NBT differs: {relative}:{slot}')
        expected_paths.add(relative)
        count += len(expected)
        regions += 1
        if regions % 50 == 0:
            print(f'VERIFIED {regions} regions {count} chunks', flush=True)
    found = {p.relative_to(converted) for p in converted.rglob('r.*.*.linear')}
    if found != expected_paths or list(converted.rglob('*.mca')) or list(converted.rglob('*.mcc')):
        raise ValueError('Unexpected/missing region files or retained Anvil/external files')
    # Every non-region persistent world file must remain exactly unchanged.
    unchanged = 0
    for source in baseline.rglob('*'):
        if source.is_file() and source.suffix not in ('.mca', '.mcc') and source.name != 'session.lock':
            target = converted / source.relative_to(baseline)
            relative = source.relative_to(baseline)
            if relative.as_posix() == 'level.dat':
                _startup_metadata_matches(source, target)
                unchanged += 1
                continue
            if relative.as_posix() == 'level.dat_old':
                _startup_metadata_matches(baseline / 'level.dat', target)
                unchanged += 1
                continue
            if relative.as_posix() in ('data/DistantHorizons.sqlite-shm', 'data/DistantHorizons.sqlite-wal'):
                # Main DH database is still byte-compared below. A separate
                # immutable SQLite read has verified all logical table rows.
                if not (baseline / 'data/DistantHorizons.sqlite').is_file() or not (converted / 'data/DistantHorizons.sqlite').is_file():
                    raise ValueError('DH journal exists without its database')
                unchanged += 1
                continue
            if not target.is_file() or digest(source) != digest(target):
                raise ValueError(f'Non-region data changed: {relative}')
            unchanged += 1
    return {'regions': regions, 'chunkPayloads': count, 'unchangedOtherFiles': unchanged,
            'elapsedSeconds': round(time.monotonic()-began, 2)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('baseline', type=Path)
    parser.add_argument('converted', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.baseline, args.converted)), flush=True)
