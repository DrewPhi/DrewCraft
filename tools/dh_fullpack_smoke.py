"""Full released server on disposable flat data: DH331 -> patched333 + Linear.

No production access, player account or GUI. Not a Diffusion inference benchmark
or aircraft/rendering test. Fresh flat data avoids expensive neural generation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys
import time
import tomllib
from rcon.source import Client
from dh_config_upgrade import migrate
from dh_smoke_checks import dh_radius_chunks, verify_saved_block

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'infra'))
from worldgen_guard import read_nbt

BAD = r'MixinApplyError|InvalidMixinException|Failed to initialize server|Encountered an unexpected exception|Corrupt Linear region|Chunky is not loaded|Querying coarse map to find spawn'


def run(root, candidate):
    assert not (root / 'world/level.dat').exists(), 'Disposable runtime required'
    baseline = root / 'mods/DistantHorizons-3.3.1-1.21.1-fabric-neoforge.jar'
    assert hashlib.sha256(baseline.read_bytes()).hexdigest() == 'b12931cc0c680914e461b478f6a361285870a489bedd3985dee52cd3ce3590c0'
    linear = root / 'mods/linear-1.21.1-1.3.3+legacy.jar'
    assert hashlib.sha256(linear.read_bytes()).hexdigest() == 'cdc685ca718f74b69444e45dedebdf90709407b06c9cac649822855a3631129a'
    report = json.loads((candidate.parent / 'build-report.json').read_text())
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == report['jarSha256']
    password = secrets.token_urlsafe(32)
    (root / 'server.properties').write_text('\n'.join([
        'server-ip=127.0.0.1', 'server-port=25585', 'online-mode=false',
        'white-list=true', 'enable-rcon=true', 'rcon.port=25586',
        f'rcon.password={password}', 'level-type=minecraft\\:flat',
        'level-seed=123456', 'view-distance=3', 'simulation-distance=3',
    ]) + '\n')
    (root / 'server.properties').chmod(0o600)
    (root / 'eula.txt').write_text('eula=true\n')
    (root / 'user_jvm_args.txt').write_text('-Xms1G\n-Xmx4G\n')
    config = root / 'config/DistantHorizons.toml'
    config.write_text('_version = 4\n[common.multiThreading]\nnumberOfThreads = 1\n'
                      '[common.worldGenerator]\ngeneratorPlan = "CHUNKS_ONLY"\n'
                      'chunkGeneratorMode = "PRE_EXISTING_ONLY"\n'
                      '[client.advanced.graphics.quality]\nlodChunkRenderDistanceRadius = 64\n'
                      '[client.advanced.graphics.culling]\noverdrawPrevention = "0.2"\n'
                      'reduceOverdrawWithFastMovement = true\n'
                      '[server]\nserverId = 1234567\nplayerBandwidthLimit = 6000\n'
                      'generationRequestRateLimit = 60\nsyncOnLoadRateLimit = 90\n'
                      'enableAdaptiveTransferSpeed = false\n')
    db = root / 'world/data/DistantHorizons.sqlite'
    def lods():
        with sqlite3.connect(f'file:{db}?mode=ro', uri=True) as conn:
            assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
            return {tuple(row) for row in conn.execute('SELECT DetailLevel, PosX, PosZ FROM FullData WHERE DetailLevel=0')}
    def command(*args):
        with Client('127.0.0.1', 25586, passwd=password, timeout=30) as client:
            reply = client.run(*args)
        print('RCON', args, reply, flush=True)
        return reply
    def stage(name, action):
        log = root / f'{name}.log'
        with log.open('w') as output:
            proc = subprocess.Popen(['bash', 'run.sh', 'nogui'], cwd=root, stdout=output, stderr=subprocess.STDOUT)
            def wait(predicate, seconds=600):
                end = time.monotonic() + seconds
                while time.monotonic() < end:
                    assert proc.poll() is None, f'{name}: server exited'
                    assert not re.search(BAD, log.read_text()), f'{name}: server error; inspect log'
                    if predicate():
                        return
                    time.sleep(2)
                raise TimeoutError(name)
            def ready():
                try:
                    return 'There are 0' in command('list')
                except (OSError, ConnectionError):
                    return False
            try:
                wait(ready)
                action(wait)
                assert 'Saved the game' in command('save-all', 'flush')
                command('stop')
                proc.wait(timeout=90)
                assert proc.returncode == 0
                assert not re.search(BAD, log.read_text()), f'{name}: shutdown error'
            finally:
                if proc.poll() is None:
                    try:
                        command('stop'); proc.wait(timeout=30)
                    except Exception:
                        proc.kill(); proc.wait(timeout=15)
        print('FULLPACK_STAGE_PASS', name, flush=True)
    def pregen(radius, wait):
        reply = command('dh', 'pregen', 'start', 'overworld', '0', '0', str(dh_radius_chunks(radius)))
        assert 'Starting pregen' in reply, reply
        wait(lambda: 'Pregen is not running' in command('dh', 'pregen', 'status'))
    def baseline_action(wait):
        command('setblock', '0', '65', '0', 'minecraft:diamond_block')
        command('scoreboard', 'objectives', 'add', 'dh_acceptance', 'dummy')
        verify_saved_block(command)
        log = root / 'logs/latest.log'
        offset = len(log.read_text())
        for args in [('chunky','world','minecraft:overworld'), ('chunky','center','0','0'), ('chunky','radius','640'), ('chunky','start')]:
            command(*args)
        wait(lambda: bool(re.search(r'Task finished for (?:minecraft:)?overworld', log.read_text()[offset:])))
        time.sleep(4)
        pregen(32, wait)
    # TD's fresh-spawn injection is unconditional even for flat generators.
    # Seed an initialized flat save with just exact released Linear first; then
    # restore EVERY released mod and datapack for the actual acceptance stages.
    held_mods = root / 'fullpack-mods'
    (root / 'mods').rename(held_mods)
    (root / 'mods').mkdir()
    shutil.copy2(held_mods / linear.name, root / 'mods' / linear.name)
    world_packs = root / 'world/datapacks'
    held_packs = root / 'fullpack-world-datapacks'
    if world_packs.exists():
        world_packs.rename(held_packs)
    try:
        stage('seed-flat', lambda wait: None)
        saved = read_nbt(root / 'world/level.dat')['Data']
        assert saved['initialized'] == 1, 'Seed world has not initialized spawn'
        assert saved['WorldGenSettings']['dimensions']['minecraft:overworld']['generator']['type'] == 'minecraft:flat'
    finally:
        # Remove only our one-file seed mods directory, retaining that file.
        (root / 'mods').rename(root / 'seed-mods')
        held_mods.rename(root / 'mods')
        if held_packs.exists():
            held_packs.rename(world_packs)
    stage('baseline-331', baseline_action)
    # Controlled missing-LOD fixture on disposable data ONLY. Keep central old
    # rows to test preservation, remove outer rows so native pregen must read
    # saved Linear chunks outside spawn rather than pass as a no-op.
    with sqlite3.connect(db) as conn:
        conn.execute('DELETE FROM FullData WHERE DetailLevel != 0 OR ABS(PosX) > 1 OR ABS(PosZ) > 1')
    before = lods()
    assert before, 'No baseline LODs'
    assert list((root / 'world/region').glob('*.linear')), 'Linear did not save chunks'
    assert not list((root / 'world/region').glob('*.mca')), 'Unexpected Anvil fallback'
    baseline.rename(root / baseline.name)  # Keep out of mods, do not delete the baseline.
    shutil.copy2(candidate, root / 'mods' / candidate.name)
    assert migrate(config)
    before_config = tomllib.loads(config.read_text())
    def candidate_action(wait):
        verify_saved_block(command)
        pregen(512, wait)
    stage('candidate-333', candidate_action)
    after = lods()
    assert before <= after, 'Upgrade lost base LOD keys'
    assert len(after) > len(before), 'Candidate did not extend saved-chunk LOD coverage'
    def check_settings():
        data = tomllib.loads(config.read_text())
        for path in [('common','worldGenerator','generatorPlan'), ('common','worldGenerator','chunkGeneratorMode'),
                     ('common','multiThreading','numberOfThreads'), ('client','advanced','graphics','quality','lodChunkRenderDistanceRadius'),
                     ('client','advanced','graphics','culling','overdrawPrevention'), ('client','advanced','graphics','culling','reduceOverdrawWithFastMovement')]:
            expected, actual = before_config, data
            for key in path:
                expected, actual = expected[key], actual[key]
            assert actual == expected, (path, actual, expected)
        for key in ('serverId', 'playerBandwidthLimit', 'generationRequestRateLimit', 'syncOnLoadRateLimit', 'enableAdaptiveTransferSpeed'):
            assert data['server'][key] == before_config['server'][key], key
        assert data['_version'] == 5
    check_settings()
    stage('candidate-restart', lambda wait: candidate_action(wait))
    check_settings()
    assert after <= lods()
    assert not list((root / 'world/region').glob('*.mca'))
    result = {'status':'PASS', 'baselineBaseLods':len(before), 'candidateBaseLods':len(after),
              'candidateSha256':report['jarSha256'], 'scope':'Flat save seeded with released Linear only; full rc.2 server mod set restored before baseline/upgrade tests. Existing DH331 LOD upgrade, native saved-chunk LOD growth, restart, shared client/server config preservation. Not production-world or aircraft acceptance.'}
    (root / 'fullpack-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runtime', type=Path)
    parser.add_argument('candidate', type=Path)
    args = parser.parse_args()
    run(args.runtime.resolve(), args.candidate.resolve())
