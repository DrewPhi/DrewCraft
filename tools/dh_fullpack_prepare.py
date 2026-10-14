"""Assemble an isolated test of the exact public rc.2 server, not a release."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import urllib.request

MANIFEST = 'https://github.com/DrewPhi/DrewCraft/releases/download/drewcraft-pack-0.1.17-rc.2/release-manifest.json'
MANIFEST_SHA = '7d17795ebc8d1da7076a69913233370c24072504c1edb5000959f82c7bef95e2'


def fetch(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'DrewCraft-compatibility-test'}), timeout=120) as response:
                return response.read()
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2)


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    raw = fetch(MANIFEST)
    assert hashlib.sha256(raw).hexdigest() == MANIFEST_SHA
    manifest = json.loads(raw)
    files = [entry for entry in manifest['files'] if entry['side'] in ('common', 'server')]
    def install(entry):
        rel = Path(entry['path'])
        assert not rel.is_absolute() and '..' not in rel.parts
        data = fetch(entry['url'])
        assert len(data) == entry['size'] and hashlib.sha256(data).hexdigest() == entry['sha256'], entry['path']
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(install, files))
    installer = root.parent / 'neoforge-fullpack-installer.jar'
    installer.write_bytes(fetch('https://maven.neoforged.net/releases/net/neoforged/neoforge/21.1.250/neoforge-21.1.250-installer.jar'))
    assert hashlib.sha256(installer.read_bytes()).hexdigest() == '0e47a91ba2139a8db4bf7627af081f7b5789b508bb039ee8dea1272b79693d60'
    subprocess.run(['java', '-jar', str(installer.resolve()), '--installServer', str(root.resolve())], check=True)
    # World datapacks are installed exactly as on production, on disposable data.
    if (root / 'datapacks').is_dir():
        shutil.copytree(root / 'datapacks', root / 'world/datapacks')
    (root / 'verified-input.json').write_text(json.dumps({'manifestSha256': MANIFEST_SHA, 'files': files}, indent=2))
    print('FULLPACK_VERIFIED', len(files), flush=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runtime', type=Path)
    prepare(parser.parse_args().runtime)
