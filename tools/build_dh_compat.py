#!/usr/bin/env python3
"""Compile one pinned upstream DH source class; preserve all other release bytes.

Produces a candidate only. Does not deploy, promote, run Minecraft, or touch worlds.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('coreSubProjects/core/src/main/java/com/seibel/distanthorizons/core/wrapperInterfaces/modAccessor/AbstractChunkyAccessor.java')
CLASS = 'com/seibel/distanthorizons/core/wrapperInterfaces/modAccessor/AbstractChunkyAccessor.class'
UPSTREAM_SHA512 = 'd14b32d3fd143a06514d6ad388eee11e9d657c84e1a937aaf8d033b1137fb43ef8b05cff1011a994cc42f3106823c51234f8bc18d72bb05bc317a20ea83c50ed'
ORIGINAL_SOURCE_SHA256 = 'fd3e71c51f1475aafba4da9db591ba02ddfff285801f85de11369c22ef4d9755'
PATCHED_SOURCE_SHA256 = 'edabf210adb31c02d9013e6dc0c2a8a5085fc45654f8bffacf7f83380cb6380f'
PINS = {'upstreamRepository': 'https://gitlab.com/distant-horizons-team/distant-horizons',
        'upstreamCommit': 'a54dd3eb1df0078e63a71266d042c10d9cda4493',
        'coreCommit': 'b02c66d778beea11a931291815d652cd8abaa7ad',
        'providerVersion': '9w34y8ai', 'upstreamVersion': '3.3.3-1.21.1',
        'patchVersion': 'drewcraft.1',
        'baseJarUrl': 'https://cdn.modrinth.com/data/uCdwusMi/versions/9w34y8ai/DistantHorizons-3.3.3-1.21.1-fabric-neoforge.jar'}


def sha(path, algorithm='sha256'):
    return hashlib.new(algorithm, path.read_bytes()).hexdigest()


def build(args):
    assert sha(args.jar, 'sha512') == UPSTREAM_SHA512, 'Not the exact official DH 3.3.3 release'
    assert sha(args.chunky_jar) == 'd72f235cf1f56f2c374f52c00bdda5034524b28142305a84cfc123a3f92ad274', 'Not production Chunky 1.4.23'
    source_hash = sha(args.source / SOURCE)
    assert source_hash in (ORIGINAL_SOURCE_SHA256, PATCHED_SOURCE_SHA256), 'Unrecognized upstream source'
    args.output.mkdir(parents=True, exist_ok=False)
    source_root = args.output / 'source'
    target = source_root / SOURCE.relative_to('coreSubProjects')
    target.parent.mkdir(parents=True)
    shutil.copy2(args.source / SOURCE, target)
    patch = ROOT / 'patches/distant-horizons/3.3.3-chunky-init.patch'
    if source_hash == ORIGINAL_SOURCE_SHA256:
        subprocess.run(['patch', '-p1', '--batch', '--forward', '--input', str(patch)],
                       cwd=source_root, check=True)
    assert sha(target) == PATCHED_SOURCE_SHA256
    classes = args.output / 'classes'
    classes.mkdir()
    cp = os.pathsep.join(map(str, [args.jar, args.chunky_jar, *args.dependency_jar]))
    subprocess.run([args.javac, '--release', '8', '-proc:none', '-cp', cp, '-d', str(classes), str(target)], check=True)
    probe_classes = args.output / 'probe'
    probe_classes.mkdir()
    subprocess.run([args.javac, '--release', '8', '-proc:none', '-cp', cp, '-d', str(probe_classes),
                    str(ROOT / 'tests/dh/ChunkyStartupProbe.java')], check=True)
    baseline = subprocess.run([args.java, '-cp', os.pathsep.join([str(probe_classes), cp]),
                               'ChunkyStartupProbe'], capture_output=True, text=True, timeout=60)
    assert baseline.returncode != 0 and 'Chunky is not loaded' in baseline.stderr, baseline.stdout + baseline.stderr
    print('Original release reproduces startup failure', flush=True)
    patched_cp = os.pathsep.join([str(probe_classes), str(classes), cp])
    tested = subprocess.run([args.java, '-cp', patched_cp, 'ChunkyStartupProbe'],
                            capture_output=True, text=True, timeout=60)
    assert tested.returncode == 0 and 'CHUNKY_STARTUP_PROBE_PASS' in tested.stdout, tested.stdout + tested.stderr
    report = dict(PINS, sourceSha256=sha(target), patchSha256=sha(patch),
                  baseJarSha512=UPSTREAM_SHA512, regressionProbe='PASS',
                  minecraftRuntimeAcceptance='NOT_RUN',
                  compiler=subprocess.check_output([args.javac, '-version'], text=True).strip())
    jar = args.output / 'DistantHorizons-3.3.3-1.21.1-drewcraft.1.jar'
    with zipfile.ZipFile(args.jar) as original, zipfile.ZipFile(jar, 'w') as output:
        assert CLASS in original.namelist(), 'Missing target class in upstream release'
        assert len(original.namelist()) == len(set(original.namelist())), 'Duplicate upstream ZIP entries'
        for info in original.infolist():
            data = (classes / CLASS).read_bytes() if info.filename == CLASS else original.read(info.filename)
            output.writestr(info, data)
        output.writestr('META-INF/drewcraft-dh-compat.json', json.dumps(report, sort_keys=True))
    with zipfile.ZipFile(args.jar) as original, zipfile.ZipFile(jar) as output:
        assert set(output.namelist()) == set(original.namelist()) | {'META-INF/drewcraft-dh-compat.json'}
        for name in original.namelist():
            if name != CLASS:
                assert original.read(name) == output.read(name), name
    archive = args.output / 'DistantHorizons-3.3.3-drewcraft.1-sources.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for path in args.source.rglob('*'):
            rel = path.relative_to(args.source)
            if rel == SOURCE:
                continue
            if any(part in {'.git', '.gradle', 'build'} for part in rel.parts) or not path.is_file():
                continue
            tar.add(path, arcname=str(Path('upstream') / rel), recursive=False)
        tar.add(target, arcname=str(Path('upstream') / SOURCE))
        for path, name in ((patch, 'patches/distant-horizons/3.3.3-chunky-init.patch'),
                           (Path(__file__), 'tools/build_dh_compat.py'),
                           (ROOT / 'tests/dh/ChunkyStartupProbe.java', 'tests/dh/ChunkyStartupProbe.java')):
            tar.add(path, arcname=str(Path('drewcraft') / name))
    report.update(jarSha256=sha(jar), sourceArchiveSha256=sha(archive))
    (args.output / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--jar', type=Path, required=True)
    p.add_argument('--chunky-jar', type=Path, required=True)
    p.add_argument('--dependency-jar', type=Path, action='append', default=[])
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--javac', default='javac')
    p.add_argument('--java', default='java')
    args = p.parse_args()
    args.source = args.source.resolve(); args.jar = args.jar.resolve(); args.output = args.output.resolve()
    args.chunky_jar = args.chunky_jar.resolve()
    args.dependency_jar = [path.resolve() for path in args.dependency_jar]
    build(args)
