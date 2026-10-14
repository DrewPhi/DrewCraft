"""Minimal preload release: preserve every production entry; add one client class."""
import argparse
import json
from pathlib import Path
import zipfile
from release_contract import canonical_json_bytes, make_live_pointer, sha256_file, validate_manifest

RECORDER = 'dev/drewcraft/client/LastOverworldLocation.class'
CATALOG = 'https://github.com/DrewPhi/DrewCraft/releases/download/drewcraft-dh-cache/catalog.json'


def build(base, baseline_jar, compiled_jar, output):
    manifest = validate_manifest(json.loads(base.read_text()))
    if manifest['packVersion'] != '0.1.18':
        raise ValueError('Expected exact production 0.1.18 baseline')
    entry = next(e for e in manifest['files'] if e['path'].startswith('mods/drewcraft-') and e['path'].endswith('.jar'))
    if entry['side'] != 'common' or sha256_file(baseline_jar) != entry['sha256']:
        raise ValueError('Baseline integration jar differs from release')
    output.mkdir(parents=True, exist_ok=False)
    asset = 'common--mods--' + Path(entry['path']).name
    target = output / asset
    with zipfile.ZipFile(baseline_jar) as old, zipfile.ZipFile(compiled_jar) as compiled, zipfile.ZipFile(target, 'w') as new:
        if RECORDER in old.namelist():
            raise ValueError('Recorder already present in baseline')
        recorder = compiled.read(RECORDER)
        if not recorder.startswith(b'\xca\xfe\xba\xbe'):
            raise ValueError('Recorder is not a Java class')
        for info in old.infolist():
            new.writestr(info, old.read(info.filename))
        info = zipfile.ZipInfo(RECORDER, (2026, 10, 14, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        new.writestr(info, recorder)
    with zipfile.ZipFile(baseline_jar) as old, zipfile.ZipFile(target) as new:
        assert set(new.namelist()) == set(old.namelist()) | {RECORDER}
        assert all(old.read(name) == new.read(name) for name in old.namelist())
    prefix = 'https://github.com/DrewPhi/DrewCraft/releases/download/drewcraft-pack-0.1.19/'
    entry.update(size=target.stat().st_size, sha256=sha256_file(target), url=prefix + asset,
                 origin={'type':'drewcraft_release'})
    manifest.update(packVersion='0.1.19', minimumLauncherVersion='0.1.16', channel='candidate')
    manifest['server']['dhPreloadUrl'] = CATALOG
    validate_manifest(manifest)
    (output / 'release-manifest.json').write_bytes(canonical_json_bytes(manifest))
    pointer = make_live_pointer('candidate', prefix + 'release-manifest.json', manifest)
    (output / 'live.json').write_bytes(canonical_json_bytes(pointer))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'baseline_jar', 'compiled_jar', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    build(args.base, args.baseline_jar, args.compiled_jar, args.output)
