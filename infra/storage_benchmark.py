"""Offline Anvil compaction and real Btrfs-Zstd tests on disposable copies."""
import argparse
import hashlib
import json
import pathlib
import shutil
import struct
import subprocess
import tempfile
import zlib
import time


def linear_layout_sample(source, scratch):
    """Format-level experiment; not a Minecraft/Linear mod integration test."""
    raw = source.read_bytes()
    chunks, timestamps = [], []
    for index in range(1024):
        entry = int.from_bytes(raw[index*4:index*4+4], 'big')
        timestamp = int.from_bytes(raw[4096+index*4:4100+index*4], 'big')
        timestamps.append(timestamp)
        if not entry:
            chunks.append(b'')
            continue
        at = (entry >> 8)*4096
        length = struct.unpack_from('>I', raw, at)[0]
        if raw[at+4] != 2:
            raise ValueError('format experiment currently requires zlib chunks')
        chunks.append(zlib.decompress(raw[at+5:at+4+length]))
    body = b''.join(struct.pack('>II', len(c), ts) for c, ts in zip(chunks, timestamps)) + b''.join(chunks)
    report = []
    for level in (3, 15):
        start = time.monotonic()
        compressed = subprocess.check_output(['zstd', '-q', '-c', f'-{level}'], input=body)
        elapsed = time.monotonic()-start
        encoded = struct.pack('>QBQBHIQ', 0xc3ff13183cca9d9a, 1, max(timestamps), level,
                              sum(bool(c) for c in chunks), len(compressed), zlib.crc32(compressed))
        encoded += compressed + struct.pack('>Q', 0xc3ff13183cca9d9a)
        decoded = subprocess.check_output(['zstd', '-q', '-d', '-c'], input=encoded[32:-8])
        assert decoded == body
        (scratch/f'{source.stem}.level{level}.linear').write_bytes(encoded)
        report.append({'level': level, 'bytes': len(encoded), 'encodeSeconds': elapsed,
                       'rawNbtAndTimestampsRoundtripVerified': True})
    return {'file': source.name, 'results': report, 'modRuntimeTested': False}


def compact(source, target):
    raw = source.read_bytes()
    if len(raw) < 8192 or len(raw) % 4096:
        raise ValueError('invalid region length')
    header = bytearray(raw[:8192])
    output = bytearray(header)
    occupied = {0, 1}
    payloads = []
    for index in range(1024):
        entry = int.from_bytes(raw[index*4:index*4+4], 'big')
        offset, count = entry >> 8, entry & 255
        if not entry:
            continue
        if offset < 2 or not count or (offset+count)*4096 > len(raw):
            raise ValueError('invalid chunk location')
        sectors = set(range(offset, offset+count))
        if occupied & sectors:
            raise ValueError('overlapping sectors')
        occupied |= sectors
        length = struct.unpack_from('>I', raw, offset*4096)[0]
        if length < 1 or length+4 > count*4096:
            raise ValueError('invalid chunk payload length')
        payload = raw[offset*4096+4:offset*4096+4+length]
        # External chunks need their companion files; exclude rather than
        # claiming a standalone region roundtrip for them.
        if payload[0] & 128:
            raise ValueError('external chunk: select a self-contained sample')
        if payload[0] == 2:
            zlib.decompress(payload[1:])  # Validate source compressed NBT stream.
        payloads.append(hashlib.sha256(payload).hexdigest())
        new_offset = len(output)//4096
        header[index*4:index*4+4] = ((new_offset << 8) | count).to_bytes(4, 'big')
        output.extend(raw[offset*4096:(offset+count)*4096])
    output[:8192] = header
    target.write_bytes(output)
    for index in range(1024):
        old_entry = int.from_bytes(raw[index*4:index*4+4], 'big')
        new_entry = int.from_bytes(output[index*4:index*4+4], 'big')
        if old_entry:
            count = old_entry & 255
            old_at, new_at = (old_entry >> 8)*4096, (new_entry >> 8)*4096
            assert raw[old_at:old_at+count*4096] == output[new_at:new_at+count*4096]
    assert raw[4096:8192] == output[4096:8192]
    return {'file': source.name, 'chunks': len(payloads), 'originalBytes': len(raw),
            'compactedBytes': len(output), 'reclaimedBytes': len(raw)-len(output),
            'payloadsAndTimestampsVerified': True}


def btrfs_sample(files, scratch):
    image, mount = scratch/'btrfs-test.img', scratch/'mount'
    mount.mkdir()
    with image.open('xb') as out:
        out.truncate(512*1024*1024)
    subprocess.run(['mkfs.btrfs', '-q', str(image)], check=True)
    subprocess.run(['mount', '-o', 'loop,compress-force=zstd:15', str(image), str(mount)], check=True)
    try:
        for source in files:
            shutil.copyfile(source, mount/source.name)
        subprocess.run(['sync', '-f', str(mount)], check=True)
        result = subprocess.check_output(['btrfs', 'filesystem', 'du', '-s', '--raw', str(mount)], text=True)
        physical = subprocess.check_output(['btrfs', 'filesystem', 'df', '-b', str(mount)], text=True)
        for source in files:
            assert hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256((mount/source.name).read_bytes()).digest()
        return {'logicalReferencedExtents': result, 'physicalAllocation': physical,
                'byteForByteReadbackVerified': True, 'compression': 'zstd:15'}
    finally:
        subprocess.run(['umount', str(mount)], check=True)
        image.unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('samples', type=pathlib.Path)
    parser.add_argument('--btrfs', action='store_true')
    args = parser.parse_args()
    files = sorted(args.samples.glob('*.mca'))
    if not files:
        raise RuntimeError('no sample regions')
    with tempfile.TemporaryDirectory(prefix='drewcraft-region-bench-') as temp:
        scratch = pathlib.Path(temp)
        results = [compact(source, scratch/source.name) for source in files]
        report = {'regions': results, 'sampleBytes': sum(r['originalBytes'] for r in results),
                  'reclaimableBytes': sum(r['reclaimedBytes'] for r in results)}
        report['linearFormatExperiment'] = [linear_layout_sample(f, scratch) for f in files]
        if args.btrfs:
            report['filesystemCompression'] = btrfs_sample(files, scratch)
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
