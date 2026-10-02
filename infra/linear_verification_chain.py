"""Background, fail-closed runtime verification on the fixed disposable world.

No production cutover or release publication. Each stage emits durable evidence.
Production idle pregeneration is resumed on exit; its world stays Anvil.
"""
import hashlib
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import traceback

from region_inventory import linear_payloads, linear_slots
from verify_dh_linear_lod import inspect as inspect_lod
from verify_region_conversion import anvil_payloads
from worldgen_guard import NbtReader, verify as verify_worldgen
from inspect_conversion_metadata import ExactReader

TEST = Path('/srv/drewcraft/linear-verification')
RUNTIME = TEST / 'runtime'
WORLD = RUNTIME / 'world'
BASELINE = TEST / 'baseline/persistent/world'
EVIDENCE = TEST / 'chain-evidence'
UNIT = 'drewcraft-linear-test'
JAVA = '/opt/drewcraft/java/bin/java'
X, Z = -2816, 768
NEW_X, NEW_Z = 16392, 16392


def properties():
    result = dict(line.split('=', 1) for line in (RUNTIME / 'server.properties').read_text().splitlines()
                  if '=' in line and not line.startswith('#'))
    if result.get('server-ip') != '127.0.0.1' or result.get('server-port') != '25585' or result.get('rcon.port') != '25586':
        raise RuntimeError('Refusing any endpoint outside the isolated runtime')
    if RUNTIME.resolve() != RUNTIME or WORLD.resolve() != WORLD:
        raise RuntimeError('Refusing runtime/world symlinks')
    return result


def rcon(*command):
    from rcon.source import Client
    props = properties()
    with Client('127.0.0.1', 25586, passwd=props['rcon.password'], timeout=30) as client:
        response = client.run(*command)
    print('RCON', ' '.join(command), response.strip(), flush=True)
    return response


def checked(*command):
    response = rcon(*command)
    if not response.strip() or re.search(r'unknown|incorrect|invalid|exception|failed|error', response, re.I):
        raise RuntimeError('Test command failed: ' + response)
    return response


def reserve():
    if shutil.disk_usage(TEST).free < 25_000_000_000:
        raise RuntimeError('25 GB storage reserve reached; stopping test jobs')


def wait_for(callback, seconds, description):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        reserve()
        if callback():
            return
        time.sleep(30)
    raise TimeoutError(description)


def ready():
    properties()
    try:
        return bool(re.search(r'There are 0 ', rcon('list')))
    except Exception:
        return False


def stop_server():
    # SIGINT shutdown sometimes exits 130; RCON stop requests normal saving.
    try:
        rcon('stop')
    except Exception:
        pass
    def stopped():
        pid = subprocess.check_output(['systemctl', 'show', UNIT, '-p', 'MainPID', '--value'], text=True).strip()
        return pid in ('', '0')
    wait_for(stopped, 240, 'Isolated server did not stop after saving')


def boot_server():
    subprocess.run(['systemctl', 'reset-failed', UNIT], check=False)
    subprocess.run(['systemd-run', '--unit=' + UNIT, '--description=Isolated Linear chain runtime',
                    '--property=User=drewcraft', '--property=WorkingDirectory=' + str(RUNTIME),
                    '--property=Nice=10', '--property=CPUQuota=200%', '--property=MemoryMax=16G',
                    '--property=ProtectSystem=strict', '--property=ReadWritePaths=' + str(RUNTIME),
                    '--property=PrivateTmp=yes', '--property=KillSignal=SIGINT', '--property=TimeoutStopSec=120',
                    JAVA, '@user_jvm_args.txt', '@libraries/net/neoforged/neoforge/21.1.250/unix_args.txt', 'nogui'], check=True)
    wait_for(ready, 1200, 'Converted server boot timed out')


def save():
    began = time.monotonic()
    response = checked('save-all', 'flush')
    if 'Saved the game' not in response:
        raise RuntimeError('Save acknowledgement missing')
    return round(time.monotonic() - began, 3)


def no_fallbacks():
    if list(WORLD.rglob('*.mca')) or list(WORLD.rglob('*.mcc')):
        raise RuntimeError('Converted runtime created Anvil/external fallback files')


def chunk_payload(world, x, z, linear=True):
    cx, cz = x // 16, z // 16
    path = world / 'region' / f'r.{cx//32}.{cz//32}.{"linear" if linear else "mca"}'
    if not path.exists():
        return None
    payloads = linear_payloads(path) if linear else anvil_payloads(path)
    return payloads.get((cz % 32) * 32 + cx % 32)


def full(payload):
    if payload is None:
        return False
    reader = NbtReader(payload)
    if reader.number('>B') != 10:
        raise RuntimeError('Chunk NBT root is not compound')
    reader.string()
    return reader.payload(10).get('Status') in ('full', 'minecraft:full')


def log_messages(offset):
    with (RUNTIME / 'logs/latest.log').open('rb') as stream:
        stream.seek(offset)
        return stream.read().decode('utf-8', 'replace')


def start_chunky():
    response = checked('chunky', 'start')
    if 'task was already started for this world' in response.lower():
        response = checked('chunky', 'confirm')
    if 'started' not in response.lower() or 'already started' in response.lower():
        raise RuntimeError('Chunky did not acknowledge a new selection: ' + response)
    return response


def native_dh(x=X, z=Z):
    checked('dh', 'config', 'generation.plan', 'CHUNKS_ONLY')
    checked('dh', 'config', 'generation.chunkMode', 'PRE_EXISTING_ONLY')
    offset = (RUNTIME / 'logs/latest.log').stat().st_size
    began = time.monotonic()
    checked('dh', 'pregen', 'start', 'overworld', str(x), str(z), '32')
    def done():
        messages = log_messages(offset)
        if re.search(r'Pregen failed|MixinApplyError|InvalidMixinException', messages):
            raise RuntimeError('Native DH generation failed; see isolated log')
        return 'Pregen is complete' in messages
    wait_for(done, 7200, 'DH completion acknowledgement missing')
    no_fallbacks()
    evidence = {}
    def written():
        try:
            evidence['lod'] = inspect_lod(WORLD / 'data/DistantHorizons.sqlite', x, z)
            return True
        except ValueError:
            return False
    wait_for(written, 180, 'DH finished without valid populated LOD evidence')
    return {'elapsedSeconds': round(time.monotonic()-began, 3), **evidence}


def restart_integrity():
    wait_for(ready, 1200, 'Current isolated server is not ready')
    first_save = save()
    stop_server()
    no_fallbacks()
    # Validate regions actually written by the preceding boot/save.
    converted_at = (WORLD / '.linear-conversion-complete').stat().st_mtime
    modified = [p for p in WORLD.rglob('*.linear') if p.stat().st_mtime > converted_at]
    for path in modified:
        linear_slots(path)
    boot_server()
    second_save = save()
    no_fallbacks()
    return {'firstSaveSeconds': first_save, 'secondSaveSeconds': second_save,
            'validatedWrittenRegions': len(modified), 'rconReadyAfterReopen': True}


def cold_dh():
    if not full(chunk_payload(BASELINE, X, Z, linear=False)):
        raise RuntimeError('Cold-read fixture is not a saved FULL source chunk')
    stop_server()
    archive = EVIDENCE / 'dh-original'
    archive.mkdir()
    for suffix in ('', '-wal', '-shm'):
        source = WORLD / ('data/DistantHorizons.sqlite' + suffix)
        if source.exists():
            source.rename(archive / source.name)
    boot_server()
    return native_dh()


def changed_dh():
    before = inspect_lod(WORLD / 'data/DistantHorizons.sqlite', X, Z)
    checked('forceload', 'add', str(X), str(Z))
    # A tall gold column in the disposable copy makes the LOD change measurable.
    # Pinned Terrain Diffusion scale-3 type spans Y=-64..1071. Reach its top
    # so the change is visible even if the fixture is a tall mountain.
    checked('fill', str(X), '64', str(Z), str(X), '1071', str(Z), 'minecraft:gold_block')
    save()
    checked('forceload', 'remove', str(X), str(Z))
    result = native_dh()
    if result['lod']['checksum'] == before['checksum']:
        raise RuntimeError('Changed disposable chunk did not refresh its LOD checksum')
    return {'before': before, 'after': result}


def chunky(x, z, radius):
    old_task = rcon('chunky', 'progress')
    if 'no task' not in old_task.lower() and 'task running' in old_task.lower():
        raise RuntimeError('An unrelated Chunky task is running in the disposable copy')
    for command in [('world', 'minecraft:overworld'), ('shape', 'square'),
                    ('center', str(x), str(z)), ('radius', str(radius))]:
        checked('chunky', *command)
    offset = (RUNTIME / 'logs/latest.log').stat().st_size
    began = time.monotonic()
    start_chunky()
    def done():
        messages = log_messages(offset)
        if re.search(r'Task finished for (?:minecraft:)?overworld\..*\(100(?:\.0+)?%\)', messages):
            return True
        if re.search(r'MixinApplyError|InvalidMixinException|Exception generating', messages):
            raise RuntimeError('Chunky runtime failure; see isolated log')
        return False
    wait_for(done, 21600, 'Bounded Terrain Diffusion generation did not finish')
    save()
    no_fallbacks()
    return {'elapsedSeconds': round(time.monotonic()-began, 3), 'messages': log_messages(offset)[-4000:]}


def chunky_existing():
    before = chunk_payload(WORLD, X, Z)
    if not full(before):
        raise RuntimeError('Existing Chunky test requires FULL converted terrain')
    result = chunky(X+8, Z+8, 4)
    after = chunk_payload(WORLD, X, Z)
    if not full(after):
        raise RuntimeError('Chunky lost existing FULL terrain')
    def stable_nbt(payload):
        reader = ExactReader(payload)
        if reader.number('>B') != 10:
            raise RuntimeError('Expected compound chunk root')
        reader.string()
        root = reader.payload(10)
        if reader.pos != len(reader.data):
            raise RuntimeError('Unexpected trailing chunk data')
        for key in ('LastUpdate', 'InhabitedTime'):
            root.pop(key, None)
        return root
    if stable_nbt(before) != stable_nbt(after):
        raise RuntimeError('Chunky changed existing saved terrain beyond tick timestamps')
    result['fullChunkPreserved'] = True
    result['terrainNbtPreserved'] = True
    return result


def chunky_new():
    if chunk_payload(WORLD, NEW_X, NEW_Z) is not None:
        raise RuntimeError('New-generation fixture already exists; select a missing chunk')
    checked('worldborder', 'set', '64000')
    result = chunky(NEW_X, NEW_Z, 4)
    dh_result = native_dh(NEW_X, NEW_Z)
    stop_server()
    if not full(chunk_payload(WORLD, NEW_X, NEW_Z)):
        raise RuntimeError('New Terrain Diffusion chunk did not save with FULL status')
    result['newFullChunkVerifiedFromDisk'] = True
    result['newTerrainDhLod'] = dh_result
    return result


def recovery_and_storage():
    marker = json.loads((TEST / 'baseline-verified.json').read_text())
    hold = json.loads(Path('/srv/drewcraft/state/backup-hold.json').read_text())
    if not marker.get('verified') or marker.get('snapshotId') != hold.get('snapshotId'):
        raise RuntimeError('Protected restore baseline no longer matches pinned backup')
    sample = next(WORLD.rglob('*.linear'))
    corrupt = EVIDENCE / 'deliberately-truncated.linear'
    corrupt.write_bytes(sample.read_bytes()[:16])
    try:
        linear_slots(corrupt)
    except ValueError:
        pass
    else:
        raise RuntimeError('Truncated region evidence was incorrectly accepted')
    def bytes_of(root, pattern):
        return sum(p.stat().st_size for p in root.rglob(pattern) if p.is_file())
    before = bytes_of(BASELINE, '*.mca') + bytes_of(BASELINE, '*.mcc')
    after = bytes_of(WORLD, '*.linear')
    timings = []
    for name in ('r.-12.-5', 'r.-14.4', 'r.-3.2', 'r.7.6'):
        started = time.monotonic()
        source = anvil_payloads(BASELINE / 'region' / (name+'.mca'))
        anvil_seconds = time.monotonic()-started
        started = time.monotonic()
        target = linear_payloads(WORLD / 'region' / (name+'.linear'))
        linear_seconds = time.monotonic()-started
        if source != target:
            raise RuntimeError('Unmodified benchmark fixture changed: ' + name)
        timings.append({'region': name, 'anvilReaderSeconds': anvil_seconds, 'linearReaderSeconds': linear_seconds})
    return {'pinnedRestoreVerified': marker['snapshotId'], 'truncatedFileRejected': True,
            'baselineRegionBytes': before, 'convertedRegionBytes': after,
            'regionSavingsPercent': round((1-after/before)*100, 2),
            'baselineWorldBytes': bytes_of(BASELINE, '*'), 'runtimeWorldBytes': bytes_of(WORLD, '*'),
            'archivedOriginalOverworldDhBytes': bytes_of(EVIDENCE / 'dh-original', '*'),
            'freeDiskBytes': shutil.disk_usage(TEST).free, 'independentReaderTimings': timings,
            'note': 'Fresh staging DH corpus is smaller; total-world bytes are not directly comparable. '
                    'Reader timings are diagnostics, not a Java flight/TPS benchmark.'}


def baseline_logs():
    def errors(start, end):
        text = subprocess.check_output(['journalctl', '-u', UNIT, '--since', start,
                                       '--until', end, '--no-pager', '-o', 'cat'], text=True)
        return sorted({line.split("Couldn't parse element", 1)[1] for line in text.splitlines()
                       if "Couldn't parse element" in line and 'railways:blocks/' in line})
    old = errors('2026-10-01 08:14:00 UTC', '2026-10-01 08:17:00 UTC')
    new = errors('2026-10-01 18:04:00 UTC', '2026-10-01 18:17:00 UTC')
    extra = sorted(set(new) - set(old))
    if new and (not old or extra):
        raise RuntimeError('Railways errors are not proven baseline-equivalent: ' + json.dumps(extra[:5]))
    return {'baselineRailwaysErrors': len(old), 'convertedRailwaysErrors': len(new),
            'newRailwaysErrors': extra, 'originalBaselineWindowUtc': '08:14..08:17'}


def main():
    global EVIDENCE
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', default='')
    parser.add_argument('--start-at', choices=('restart_integrity', 'cold_dh', 'changed_dh',
                        'chunky_existing', 'chunky_new_terrain', 'recovery_and_storage', 'baseline_log_comparison'),
                        default='restart_integrity')
    args = parser.parse_args()
    properties()
    verify_worldgen(WORLD, RUNTIME / 'server.properties')
    stages = [('restart_integrity', restart_integrity), ('cold_dh', cold_dh),
              ('changed_dh', changed_dh), ('chunky_existing', chunky_existing),
              ('chunky_new_terrain', chunky_new), ('recovery_and_storage', recovery_and_storage),
              ('baseline_log_comparison', baseline_logs)]
    if args.run_id:
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,31}', args.run_id):
            raise ValueError('Invalid run id')
        EVIDENCE = TEST / ('chain-evidence-' + args.run_id)
    selected = [index for index, (name, _) in enumerate(stages) if name == args.start_at][0]
    reused = []
    if selected:
        previous = json.loads((TEST / 'chain-evidence/state.json').read_text())
        prior_names = [name for name, _ in stages[:selected]]
        if previous.get('completed', [])[:selected] != prior_names:
            raise RuntimeError('Earlier chain stages are not all recorded as passed')
        reused = prior_names
    if EVIDENCE.exists():
        raise RuntimeError('Chain evidence already exists; inspect before resubmitting')
    if not (TEST / 'chain-evidence/dh-original/DistantHorizons.sqlite').is_file():
        # Fresh-start chains archive the original database during cold_dh.
        if args.start_at != 'restart_integrity':
            raise RuntimeError('Expected prior DH database preservation evidence is missing')
    EVIDENCE.mkdir()
    state = {'status': 'RUNNING', 'completed': [], 'results': {}, 'startedUnix': time.time(),
             'productionDeployment': False, 'reusedPassingStages': reused}
    def persist():
        temporary = EVIDENCE / 'state.json.tmp'
        temporary.write_text(json.dumps(state, indent=2) + '\n')
        temporary.replace(EVIDENCE / 'state.json')
    try:
        if selected and not ready():
            state['stage'] = 'resume_boot'
            persist()
            print('RESUME_BOOT', flush=True)
            boot_server()
        for name, task in stages[selected:]:
            state['stage'] = name
            persist()
            print('STAGE_START', name, flush=True)
            state['results'][name] = task()
            state['completed'].append(name)
            persist()
            print('STAGE_PASS', name, flush=True)
        state['status'] = 'RUNTIME_CHAIN_PASSED'
        state['remainingGates'] = ['controller runtime handoff/checkpoint/pause fixtures',
                                   'controlled interrupted-save/library recovery acceptance',
                                   'Java runtime latency acceptance',
                                   'format-aware production cutover and immutable release publication']
    except BaseException as error:
        state['status'] = 'INTERRUPTED' if isinstance(error, KeyboardInterrupt) else 'FAILED'
        state['error'] = str(error)
        traceback.print_exc()
        raise
    finally:
        state['finishedUnix'] = time.time()
        persist()
        # Stop test-only generators/server even when a gate failed.
        try:
            rcon('dh', 'pregen', 'stop')
            rcon('chunky', 'pause')
        except Exception:
            pass
        subprocess.run(['systemctl', 'stop', UNIT], check=False)
        subprocess.run(['systemctl', 'start', 'drewcraft-pregen'], check=True)
        print('CHAIN_RESULT', json.dumps(state), flush=True)


if __name__ == '__main__':
    main()
