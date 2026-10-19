"""Build a minimal, pinned 0.1.19 -> 0.1.20 chunk-delivery delta."""
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile
from release_contract import canonical_json_bytes, make_live_pointer, validate_manifest

PINS = ('U9AicWcu', '1IiqEQGl', '7TVdVtxF')


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent':'DrewCraft-flight-update/1'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def build(output):
    manifest = validate_manifest(json.loads(fetch('https://github.com/DrewPhi/DrewCraft/releases/download/drewcraft-pack-0.1.19/release-manifest.json')))
    assert manifest['packVersion'] == '0.1.19'
    output.mkdir(parents=True,exist_ok=False)
    removed = [e for e in manifest['files'] if e['path'].startswith('mods/chunksending-')]
    assert len(removed)==1
    manifest['files'] = [e for e in manifest['files'] if e not in removed]
    evidence = []
    for version_id in PINS:
        version = json.loads(fetch('https://api.modrinth.com/v2/version/'+version_id))
        assert '1.21.1' in version['game_versions'] and 'neoforge' in version['loaders']
        file = next(f for f in version['files'] if f['primary'])
        data = fetch(file['url'])
        assert len(data)==file['size'] and hashlib.sha512(data).hexdigest()==file['hashes']['sha512']
        path = output/file['filename']
        path.write_bytes(data)
        with zipfile.ZipFile(path) as jar:
            assert 'META-INF/neoforge.mods.toml' in jar.namelist()
            print(file['filename'],jar.read('META-INF/neoforge.mods.toml').decode(),flush=True)
        manifest['files'].append({'path':'mods/'+file['filename'],'side':'client' if version_id=='7TVdVtxF' else 'common','managed':True,
            'url':file['url'],'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),
            'origin':{'type':'modrinth','projectId':version['project_id'],'versionId':version_id}})
        evidence.append(version)
    manifest.update(packVersion='0.1.20',channel='candidate')
    prefix = 'https://github.com/DrewPhi/DrewCraft/releases/download/drewcraft-pack-0.1.20/'
    config = (Path(__file__).resolve().parents[1]/'pack/common/config/seamlesschunks.properties').read_bytes()
    asset = 'common--config--seamlesschunks.properties'
    (output/asset).write_bytes(config)
    manifest['files'].append({'path':'config/seamlesschunks.properties','side':'common','managed':True,
        'url':prefix+asset,'size':len(config),'sha256':hashlib.sha256(config).hexdigest(),'origin':{'type':'drewcraft_release'}})
    validate_manifest(manifest)
    (output/'release-manifest.json').write_bytes(canonical_json_bytes(manifest))
    (output/'live.json').write_bytes(canonical_json_bytes(make_live_pointer('stable',prefix+'release-manifest.json',manifest)))
    (output/'provider-evidence.json').write_bytes(canonical_json_bytes(evidence))
    print('MANIFEST_SHA256',hashlib.sha256((output/'release-manifest.json').read_bytes()).hexdigest())


if __name__=='__main__':
    import sys
    build(Path(sys.argv[1]))
