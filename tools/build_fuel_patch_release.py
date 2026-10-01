#!/usr/bin/env python3
"""Build an immutable fuel-only patch manifest; reuse all other locked assets."""
import argparse
import json
from pathlib import Path
import shutil
import urllib.parse
import zipfile

from release_contract import canonical_json_bytes, sha256_file, validate_manifest


def build(base, jar, overlay, output, version):
    manifest = validate_manifest(json.loads(base.read_text()))
    with zipfile.ZipFile(jar) as archive:
        metadata = archive.read('META-INF/neoforge.mods.toml').decode()
        if 'drewcraft.mts-fuel.mixins.json' not in metadata or 'drewcraft.dh-linear.mixins.json' in metadata:
            raise ValueError('Fuel-only jar must enable MTS policy and exclude experimental Linear hook')
    sources = {'config/mtsconfig.json': overlay/'config/mtsconfig.json',
               'drewcraft-integration/mts-fuel-policy.json': overlay/'drewcraft-integration/mts-fuel-policy.json',
               'mods/drewcraft-0.1.0-dev.1.jar': jar}
    fuels = json.loads(sources['config/mtsconfig.json'].read_text())['fuel']['fuels']
    if set(fuels) != {'gasoline', 'avgas', 'diesel', 'furnace', 'brewing_stand'} or any(v != {'lava': 0.5} for v in fuels.values()):
        raise ValueError('Fuel configuration must be lava-only, potency 0.5')
    output.mkdir(parents=True, exist_ok=False)
    updated = set()
    tag = f'drewcraft-pack-{version}'
    for entry in manifest['files']:
        if entry['side'] == 'common' and entry['path'] in sources:
            if entry.get('origin', {}).get('type') != 'drewcraft_release':
                raise ValueError('Patch cannot redistribute provider assets')
            source = sources[entry['path']]
            asset = 'common--' + entry['path'].replace('/', '--')
            shutil.copyfile(source, output/asset)
            entry.update(size=source.stat().st_size, sha256=sha256_file(source),
                         url=f'https://github.com/DrewPhi/DrewCraft/releases/download/{tag}/{urllib.parse.quote(asset)}')
            updated.add(entry['path'])
    if updated != set(sources):
        raise ValueError('Baseline lacks expected fuel patch files')
    manifest['packVersion'] = version
    validate_manifest(manifest)
    (output/'release-manifest.json').write_bytes(canonical_json_bytes(manifest))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--jar', type=Path, required=True)
    parser.add_argument('--overlay', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    build(args.base, args.jar, args.overlay, args.output, args.version)
