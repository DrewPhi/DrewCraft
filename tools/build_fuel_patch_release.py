#!/usr/bin/env python3
"""Build an immutable fuel-only patch manifest; reuse all other locked assets."""
import argparse
import json
from pathlib import Path
import shutil
import urllib.parse
import zipfile

from release_contract import canonical_json_bytes, sha256_file, validate_manifest


def build(base, jar, overlay, output, version, baseline_jar):
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
    mod_path = 'mods/drewcraft-0.1.0-dev.1.jar'
    old_entry = next(e for e in manifest['files'] if e['side'] == 'common' and e['path'] == mod_path)
    if sha256_file(baseline_jar) != old_entry['sha256']:
        raise ValueError('Baseline integration jar does not match immutable manifest')
    # Production injection embeds loose integration recipes/loot in the jar.
    # Preserve ALL baseline data resources, including worldgen, exactly. New
    # code/resources come from the compiled jar; this patch changes no datapack.
    packed_jar = output/'common--mods--drewcraft-0.1.0-dev.1.jar'
    with zipfile.ZipFile(jar) as compiled, zipfile.ZipFile(baseline_jar) as previous, zipfile.ZipFile(packed_jar, 'w') as packed:
        for entry in compiled.infolist():
            if not entry.filename.startswith('data/'):
                packed.writestr(entry, compiled.read(entry.filename))
        for entry in previous.infolist():
            if entry.filename.startswith('data/'):
                packed.writestr(entry, previous.read(entry.filename))
    sources[mod_path] = packed_jar
    updated = set()
    tag = f'drewcraft-pack-{version}'
    for entry in manifest['files']:
        if entry['side'] == 'common' and entry['path'] in sources:
            if entry.get('origin', {}).get('type') != 'drewcraft_release':
                raise ValueError('Patch cannot redistribute provider assets')
            source = sources[entry['path']]
            asset = 'common--' + entry['path'].replace('/', '--')
            if source != output/asset:
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
    parser.add_argument('--baseline-jar', type=Path, required=True)
    args = parser.parse_args()
    build(args.base, args.jar, args.overlay, args.output, args.version, args.baseline_jar)
