"""Deploy an exact fuel-only manifest; preserve the world's Anvil format."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import zipfile

sys.path.insert(0, '/srv/drewcraft/bin')
import serverctl
from rcon.source import Client

ROOT = Path('/srv/drewcraft')


def rcon(command):
    with Client('127.0.0.1', 25575, passwd=Path('/etc/drewcraft/rcon-password').read_text().strip(), timeout=10) as client:
        return client.run(command)


def health():
    for _ in range(90):
        try:
            result = rcon('list')
            if 'players online' in result:
                print(result, flush=True)
                return
        except Exception:
            pass
        time.sleep(10)
    raise RuntimeError('Server RCON readiness timed out')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--health', action='store_true')
    parser.add_argument('--manifest-url')
    parser.add_argument('--sha256')
    args = parser.parse_args()
    if args.health:
        health()
        return
    if not args.manifest_url or not args.sha256:
        raise ValueError('Exact manifest URL/hash required')
    with urllib.request.urlopen(args.manifest_url, timeout=60) as response:
        raw = response.read()
    if hashlib.sha256(raw).hexdigest() != args.sha256:
        raise RuntimeError('Published manifest hash mismatch')
    manifest = json.loads(raw)
    serverctl.require_world_identity(ROOT, manifest)
    release = serverctl.stage_release(ROOT, manifest)
    config = json.loads((release/'config/mtsconfig.json').read_text())['fuel']['fuels']
    if any(fluids != {'lava': 0.5} for fluids in config.values()):
        raise RuntimeError('Staged fuel config is not lava-only half potency')
    if any('linear' in path.name.lower() for path in (release/'mods').glob('*.jar')):
        raise RuntimeError('Fuel-only update must not install Linear')
    with zipfile.ZipFile(release/'mods/drewcraft-0.1.0-dev.1.jar') as jar:
        metadata = jar.read('META-INF/neoforge.mods.toml').decode()
        if 'drewcraft.mts-fuel.mixins.json' not in metadata or 'drewcraft.dh-linear.mixins.json' in metadata:
            raise RuntimeError('Unexpected integration hook selection')
        previous = ROOT/'current/mods/drewcraft-0.1.0-dev.1.jar'
        with zipfile.ZipFile(previous) as old:
            resources = {name: old.read(name) for name in old.namelist() if name.startswith('data/')}
            if {name: jar.read(name) for name in jar.namelist() if name.startswith('data/')} != resources:
                raise RuntimeError('Fuel patch altered baseline datapack resources')
    print('Staged verified fuel-only release', manifest['packVersion'], flush=True)
    try:
        rcon('say DrewCraft fuel update: server restarting shortly. Existing world will be preserved.')
    except Exception:
        pass
    try:
        result = serverctl.update_transaction(ROOT, manifest,
            stop_command='systemctl stop drewcraft-pregen.service drewcraft.service',
            start_command='systemctl start drewcraft.service',
            health_command=f'/usr/bin/python3 {Path(__file__).resolve()} --health')
        print(json.dumps(result), flush=True)
        print('DEPLOYMENT_COMPLETE', manifest['packVersion'], flush=True)
    finally:
        # Resume checkpoint with whichever application is healthy after update
        # or application rollback. Never touch terrain/LOD files here.
        subprocess.run(['systemctl', 'start', 'drewcraft-pregen.service'], check=True)


if __name__ == '__main__':
    main()
