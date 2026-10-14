"""Bounded localhost-only DH/Chunky lifecycle smoke; no real player/client login."""
import argparse
import json
from pathlib import Path
import re
import secrets
import sqlite3
import subprocess
import time
from rcon.source import Client


def run(root):
    assert root.is_dir() and not (root / 'world').exists(), 'Smoke requires disposable fresh runtime'
    password = secrets.token_urlsafe(32)
    (root / 'server.properties').write_text('\n'.join([
        'server-ip=127.0.0.1', 'server-port=25585', 'online-mode=false',
        'white-list=true', 'enable-rcon=true', 'rcon.port=25586',
        f'rcon.password={password}', 'level-type=minecraft\\:flat',
        'level-seed=123456', 'view-distance=3', 'simulation-distance=3',
    ]) + '\n')
    (root / 'server.properties').chmod(0o600)
    (root / 'eula.txt').write_text('eula=true\n')
    (root / 'user_jvm_args.txt').write_text('-Xms1G\n-Xmx3G\n')
    (root / 'config').mkdir(exist_ok=True)
    (root / 'config/DistantHorizons.toml').write_text(
        '_version = 5\n[common.multiThreading]\nnumberOfThreads = 1\n'
        '[common.worldGenerator]\ngeneratorPlan = "CHUNKS_ONLY"\n'
        'chunkGeneratorMode = "PRE_EXISTING_ONLY"\n')
    def rcon(*command):
        with Client('127.0.0.1',25586,passwd=password,timeout=15) as client:
            return client.run(*command)
    def wait(predicate, timeout=180):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            if proc.poll() is not None:raise RuntimeError('Server exited; inspect smoke-server.log')
            if predicate():return
            time.sleep(2)
        raise TimeoutError('Smoke gate timed out')
    log=root/'smoke-server.log'
    with log.open('w') as output:
        proc=subprocess.Popen(['bash','run.sh','nogui'],cwd=root,stdout=output,stderr=subprocess.STDOUT)
        try:
            def ready():
                try:return 'There are 0' in rcon('list')
                except Exception:return False
            wait(ready,240)
            print('SMOKE_BOOT_PASS',flush=True)
            offset=(root/'logs/latest.log').stat().st_size
            for command in [('chunky','world','minecraft:overworld'),('chunky','center','0','0'),
                            ('chunky','radius','32'),('chunky','start')]:
                print(rcon(*command),flush=True)
            wait(lambda: bool(re.search(r'Task finished for (?:minecraft:)?overworld',
                                       (root/'logs/latest.log').read_text()[offset:])))
            time.sleep(4)  # DH's Chunky-inactive debounce is two seconds.
            for command in [('dh','config','generation.plan','CHUNKS_ONLY'),
                            ('dh','config','generation.chunkMode','PRE_EXISTING_ONLY'),
                            ('dh','pregen','start','overworld','0','0','32')]:
                reply=rcon(*command); print(reply,flush=True)
                assert not re.search(r'unknown|incorrect|failed|exception',reply,re.I),reply
                if command[0:3] == ('dh','pregen','start'):
                    assert 'Starting pregen' in reply,reply
            wait(lambda:'Pregen is not running' in rcon('dh','pregen','status'),240)
            assert 'Saved the game' in rcon('save-all','flush')
            assert 'Chunky is not loaded' not in log.read_text()
            assert not re.search(r'MixinApplyError|Failed to initialize server',log.read_text())
            rcon('stop');proc.wait(timeout=60)
            assert proc.returncode==0,proc.returncode
            proc=subprocess.Popen(['bash','run.sh','nogui'],cwd=root,stdout=output,stderr=subprocess.STDOUT)
            wait(ready,240)
            assert 'Saved the game' in rcon('save-all','flush')
            rcon('stop');proc.wait(timeout=60)
            assert proc.returncode==0,proc.returncode
            db=root/'world/data/DistantHorizons.sqlite'
            with sqlite3.connect(f'file:{db}?mode=ro',uri=True) as connection:
                rows=connection.execute('SELECT COUNT(*) FROM FullData WHERE DetailLevel=0').fetchone()[0]
                assert rows>0
            (root/'smoke-result.json').write_text(json.dumps({'status':'PASS','baseLodRows':rows,
                'scope':'NeoForge 21.1.250 + patched DH 3.3.3 + Chunky. Not full DrewCraft or a flight test.'})+'\n')
            print('SMOKE_DH_CHUNKY_PASS',rows,flush=True)
        finally:
            if proc.poll() is None:
                try:rcon('stop');proc.wait(timeout=30)
                except Exception:proc.kill();proc.wait(timeout=15)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('runtime',type=Path)
    run(parser.parse_args().runtime.resolve())
