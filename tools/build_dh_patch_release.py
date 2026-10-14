"""Publishable DH-only delta over the exact released pack; no other mod changes."""
import argparse
import json
from pathlib import Path
import shutil
from release_contract import canonical_json_bytes, sha256_file, validate_manifest, make_live_pointer


def build(base, candidate, output):
    manifest = validate_manifest(json.loads(base.read_text()))
    assert manifest['packVersion'] == '0.1.17-rc.2'
    report = json.loads((candidate / 'build-report.json').read_text())
    jar = candidate / 'DistantHorizons-3.3.3-1.21.1-drewcraft.1.jar'
    assert sha256_file(jar) == report['jarSha256'] == 'b43f5ac302a2ed6039d34f737d3182a0bc771333c71653c06aa7528cae6ecb67'
    source = candidate / 'DistantHorizons-3.3.3-drewcraft.1-sources.tar.gz'
    assert sha256_file(source) == report['sourceArchiveSha256']
    output.mkdir(parents=True, exist_ok=False)
    version = '0.1.18'
    prefix = f'https://github.com/DrewPhi/DrewCraft/releases/download/drewcraft-pack-{version}/'
    entry = next(e for e in manifest['files'] if e['path'] == 'mods/DistantHorizons-3.3.1-1.21.1-fabric-neoforge.jar')
    assert entry['side'] == 'common'
    asset = 'common--mods--' + jar.name
    entry.clear()
    entry.update(path='mods/' + jar.name, side='common', managed=True, size=jar.stat().st_size,
                 sha256=sha256_file(jar), url=prefix + asset,
                 origin={'type':'drewcraft_release'})
    manifest.update(packVersion=version, minimumLauncherVersion='0.1.13', channel='candidate')
    validate_manifest(manifest)
    shutil.copy2(jar, output / asset)
    shutil.copy2(source, output / source.name)
    shutil.copy2(candidate / 'build-report.json', output / 'dh-build-report.json')
    (output / 'release-manifest.json').write_bytes(canonical_json_bytes(manifest))
    pointer = make_live_pointer('candidate', prefix + 'release-manifest.json', manifest)
    (output / 'live.json').write_bytes(canonical_json_bytes(pointer))
    print(json.dumps(pointer))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('base', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    build(args.base, args.candidate, args.output)
