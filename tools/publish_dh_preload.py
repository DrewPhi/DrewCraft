"""Verify signed Oracle LOD export, upload immutable blobs, promote catalog last."""
import argparse
import base64
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'launcher'))
from dh_preload import file_sha, validate_catalog

REPO = 'DrewPhi/DrewCraft'
ORIGIN = 'http://150.136.96.174:25566/lod-export/'


def fetch(url, limit):
    with urllib.request.urlopen(url, timeout=120) as response:
        body = response.read(limit+1)
    if len(body)>limit:
        raise ValueError('Publication metadata exceeds limit')
    return body


def verify(envelope, public_key, directory):
    raw = base64.b64decode(envelope['catalog'], validate=True)
    signature = base64.b64decode(envelope['signature'], validate=True)
    if len(raw)>8*1024**2 or len(signature)>4096:
        raise ValueError('Invalid signed metadata size')
    catalog = directory/'catalog.json'
    sig = directory/'catalog.sig'
    catalog.write_bytes(raw)
    sig.write_bytes(signature)
    subprocess.run(['openssl','dgst','-sha256','-verify',str(public_key),
                    '-signature',str(sig),str(catalog)], check=True)
    return json.loads(raw)


def gh(*args, check=True):
    return subprocess.run(['gh',*args,'--repo',REPO], check=check, capture_output=True, text=True)


def publish(public_key, target):
    with tempfile.TemporaryDirectory(prefix='dh-publish-') as temporary:
        directory = Path(temporary)
        try:
            envelope = json.loads(fetch(ORIGIN+'publication.json', 12*1024**2))
        except urllib.error.HTTPError as error:
            if error.code==404:
                print('No completed signed LOD export yet')
                return
            raise
        catalog = verify(envelope, public_key, directory)
        pointer = json.loads(fetch('https://github.com/DrewPhi/DrewCraft/releases/download/drewcraft-dev-pack/live.json', 65536))
        manifest = json.loads(fetch(pointer['manifestUrl'], 8*1024**2))
        validate_catalog(catalog, manifest)
        entries = [catalog['template'], *catalog['tiles']]
        groups = {}
        for item in entries:
            match = re.fullmatch(r'https://github.com/DrewPhi/DrewCraft/releases/download/(drewcraft-lods-\d{8}T\d{6}Z-\d+)/([0-9a-f]{64}\.(?:sqlite|jsonl\.gz))', item['url'])
            if not match or not match[2].startswith(item['sha256']+'.'):
                raise ValueError('Invalid immutable publication URL')
            groups.setdefault(match[1], []).append((match[2],item))
        for tag, items in groups.items():
            viewed = gh('release','view',tag,'--json','assets',check=False)
            if viewed.returncode:
                gh('release','create',tag,'--target',target,'--prerelease',
                   '--title',tag,'--notes','Immutable, signed-source visual LOD payloads. Not a modpack.')
                names = set()
            else:
                names = {asset['name'] for asset in json.loads(viewed.stdout)['assets']}
            batch = []
            for name,item in items:
                if name in names:
                    continue
                path = directory/name
                with urllib.request.urlopen(ORIGIN+name,timeout=120) as response, path.open('wb') as stream:
                    received = 0
                    while block := response.read(1024**2):
                        received += len(block)
                        if received>item['size']:
                            raise ValueError('Oversized LOD payload')
                        stream.write(block)
                if path.stat().st_size != item['size'] or file_sha(path)!=item['sha256']:
                    raise ValueError('Corrupted LOD payload')
                batch.append(path)
                if len(batch)==16:
                    gh('release','upload',tag,*map(str,batch))
                    for done in batch:
                        done.unlink()
                    batch=[]
            if batch:
                gh('release','upload',tag,*map(str,batch))
                for done in batch:
                    done.unlink()
            verified = gh('release','view',tag,'--json','assets')
            assets = {asset['name']:asset['size'] for asset in json.loads(verified.stdout)['assets']}
            if any(assets.get(name)!=item['size'] for name,item in items):
                raise RuntimeError('Published LOD assets incomplete')
            print('Verified',tag,len(items),'assets',flush=True)
        stable = 'drewcraft-dh-cache'
        if gh('release','view',stable,check=False).returncode:
            gh('release','create',stable,'--target',target,'--prerelease',
               '--title','DrewCraft LOD cache','--notes','Optional visual cache catalog; updated after immutable payloads are verified.')
        # Replacing the tiny catalog is the final, fail-open promotion. Clients
        # retain their old cache if GitHub briefly returns 404 during replacement.
        gh('release','upload',stable,str(directory/'catalog.json'),'--clobber')
        print('LOD_CATALOG_PUBLISHED',catalog['revision'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public-key',type=Path,required=True)
    parser.add_argument('--target',required=True)
    args=parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',args.target):
        raise ValueError('Release target must be full commit SHA')
    publish(args.public_key,args.target)
