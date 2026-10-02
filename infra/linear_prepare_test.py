"""Prepare fully independent localhost server from a verified stopped baseline."""
import json
from pathlib import Path
import secrets
import shutil
import zipfile

ROOT = Path('/srv/drewcraft')
TEST = ROOT / 'linear-verification'
UPLOAD = Path('/tmp/drewcraft-linear-ops')


def main():
    metadata = json.loads((TEST / 'baseline.json').read_text())
    verified = json.loads((TEST / 'baseline-verified.json').read_text())
    if verified.get('snapshotId') != metadata['hold']['snapshotId'] or not verified.get('verified'):
        raise RuntimeError('Baseline restore verification missing')
    baseline = TEST / 'baseline/persistent'
    if not (baseline / 'world/level.dat').is_file():
        raise RuntimeError('Verified baseline not yet restored')
    runtime = TEST / 'runtime'
    if runtime.exists():
        raise RuntimeError('Runtime already exists; inspect instead of overwriting')
    source = Path(metadata['hold']['application'])
    ignored = {'world', 'logs', 'terrain-diffusion-models', 'terrain-diffusion-cache',
               'server.properties', 'ops.json', 'whitelist.json', 'banned-ips.json', 'banned-players.json'}
    shutil.copytree(source, runtime, ignore=lambda directory, names:
                    ignored.intersection(names) if Path(directory) == source else ())
    # Refuse any inherited symlink. Test runtime owns its own data, config/cache.
    if any(p.is_symlink() for p in runtime.rglob('*')):
        raise RuntimeError('Unexpected inherited symlink; refusing isolated boot')
    for name in ('world', 'terrain-diffusion-models', 'terrain-diffusion-cache'):
        shutil.copytree(baseline / name, runtime / name)
    (runtime / 'logs').mkdir()
    for name in ('ops.json', 'whitelist.json', 'banned-ips.json', 'banned-players.json'):
        (runtime / name).write_text('[]\n')
    override = {'server-ip': '127.0.0.1', 'server-port': '25585', 'enable-rcon': 'true',
                'rcon.port': '25586', 'rcon.ip': '127.0.0.1',
                'rcon.password': secrets.token_urlsafe(40), 'enable-query': 'false',
                'level-name': 'world', 'white-list': 'true', 'online-mode': 'true'}
    props = [line for line in (baseline / 'server.properties').read_text().splitlines()
             if line.split('=', 1)[0] not in override]
    (runtime / 'server.properties').write_text('\n'.join(props + [f'{k}={v}' for k, v in override.items()]) + '\n')
    (runtime / 'server.properties').chmod(0o600)
    (runtime / 'user_jvm_args.txt').write_text('-Xms2G\n-Xmx8G\n')
    # Preserve every existing embedded datapack resource while adding adapter code.
    jar = runtime / 'mods/drewcraft-0.1.0-dev.1.jar'
    packed = jar.with_suffix('.new')
    with zipfile.ZipFile(jar) as old, zipfile.ZipFile(UPLOAD / 'drewcraft-linear-adapter.jar') as compiled, zipfile.ZipFile(packed, 'w') as output:
        for entry in compiled.infolist():
            if not entry.filename.startswith('data/'):
                output.writestr(entry, compiled.read(entry.filename))
        for entry in old.infolist():
            if entry.filename.startswith('data/'):
                output.writestr(entry, old.read(entry.filename))
    packed.replace(jar)
    shutil.copy2(UPLOAD / 'linear-1.21.1-1.3.3+legacy.jar', runtime / 'mods')
    (runtime / 'config/linear-server.toml').write_text(
        'compressionLevel = 4\nregionCacheSize = 64\nbackupEnabled = false\nautoRecompressEnabled = false\n')
    print('ISOLATED_RUNTIME_READY', runtime, flush=True)


if __name__ == '__main__':
    main()
