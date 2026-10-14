"""Idle, low-priority LOD snapshot export and signed public handoff.

The signing key authorizes LOD data only, not SSH or GitHub access. GitHub
publishes verified data with its own short-lived workflow token.
"""
import argparse
import base64
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse

from export_dh_preload import export
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'launcher'))
from dh_preload import atomic_json, canonical, identity, validate_catalog


def prepare(root, metadata_path, key, adopt=None):
    sys.path.insert(0, str(root/'bin'))
    from deploy_fuel_patch import rcon
    if not adopt and 'There are 0 ' not in rcon('list'):
        print('LOD export deferred: players online', flush=True)
        return
    manifest = json.loads((root/'current/.drewcraft-release-manifest.json').read_text())
    metadata = json.loads(metadata_path.read_text())
    if metadata['identity'] != identity(manifest):
        raise ValueError('World changed; regenerate independently verified LOD metadata')
    public = root/'state/lod-public'
    public.mkdir(exist_ok=True)
    previous = None
    if (public/'publication.json').exists():
        previous = json.loads(base64.b64decode(json.loads((public/'publication.json').read_text())['catalog']))
    state = json.loads((root/'state/pregen.json').read_text())
    receipt = root/'state/lod-export-receipt.json'
    completed = state.get('dhCompletedJobs', 0)
    if not adopt and receipt.exists() and json.loads(receipt.read_text()).get('dhCompletedJobs') == completed:
        print('LOD export skipped: no completed DH batch since last snapshot', flush=True)
        return
    tag = 'drewcraft-lods-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    base = 'https://github.com/DrewPhi/DrewCraft/releases/download/' + tag
    source = root/'persistent/world/data/DistantHorizons.sqlite'
    # Preserve operational reserve, including temporary SQLite snapshot space.
    if not adopt and shutil.disk_usage(public).free < source.stat().st_size*2 + 26*1024**3:
        raise RuntimeError('LOD export deferred: protect 25 GiB free-space reserve')
    with tempfile.TemporaryDirectory(prefix='lod-refresh-', dir=root/'state') as temp:
        directory = Path(temp)/'tiles'
        if adopt:
            directory = adopt
            catalog = validate_catalog(json.loads((adopt/'catalog.json').read_text()), manifest)
        else:
            catalog = export(source, directory, metadata, base, previous=previous, timeout=14400)
        for index, item in enumerate([catalog['template'], *catalog['tiles']]):
            suffix = '.sqlite' if item is catalog['template'] else '.jsonl.gz'
            name = item['sha256'] + suffix
            destination = public/name
            if not destination.exists():
                os.link(directory/name, destination)
            # Bound asset counts per GitHub release. Retain old immutable URLs.
            if adopt or not previous or item['url'].startswith(base+'/'):
                item['url'] = base + '-' + str(index//500) + '/' + name
        catalog['revision'] = __import__('hashlib').sha256(canonical({k:v for k,v in catalog.items() if k!='revision'})).hexdigest()
        validate_catalog(catalog, manifest)
        pending = Path(temp)/'catalog.json'
        pending.write_bytes(canonical(catalog))
        signature = subprocess.check_output(['openssl','dgst','-sha256','-sign',str(key),str(pending)])
        # Atomic envelope avoids catalog/signature races. HTTP clients cannot
        # authorize publication: the workflow verifies this detached signature.
        atomic_json(public/'publication.json', {'catalog':base64.b64encode(pending.read_bytes()).decode(),
                                               'signature':base64.b64encode(signature).decode()})
        atomic_json(receipt, {'dhCompletedJobs':completed,'revision':catalog['revision']})
        keep = {Path(item['url']).name for item in [catalog['template'], *catalog['tiles']]}
        for path in public.iterdir():
            if path.name not in keep and path.suffix in {'.gz', '.sqlite'} and time.time()-path.stat().st_mtime > 7*86400:
                path.unlink()  # Derived, unreferenced export blobs only; never world data.
        print('LOD_PUBLICATION_READY', catalog['revision'], len(catalog['tiles']), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/srv/drewcraft'))
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--key', type=Path, required=True)
    parser.add_argument('--adopt', type=Path)
    args = parser.parse_args()
    prepare(args.root, args.metadata, args.key, args.adopt)
