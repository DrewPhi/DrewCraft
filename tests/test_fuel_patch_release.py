import importlib.util
import json
from pathlib import Path
import sys
import zipfile

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from build_fuel_patch_release import build
from release_contract import sha256_file


def fixture(tmp_path, linear=False):
    jar = tmp_path/'mod.jar'
    with zipfile.ZipFile(jar, 'w') as out:
        out.writestr('META-INF/neoforge.mods.toml', 'drewcraft.mts-fuel.mixins.json' +
                     (' drewcraft.dh-linear.mixins.json' if linear else ''))
    previous = tmp_path/'previous.jar'
    with zipfile.ZipFile(previous, 'w') as out:
        out.writestr('data/mtsofficialpack/recipe/plating.json', '{"original":true}')
    paths = ['config/mtsconfig.json', 'drewcraft-integration/mts-fuel-policy.json',
             'mods/drewcraft-0.1.0-dev.1.jar', 'mods/terrain.jar']
    files = [{'side':'common', 'path':path, 'size':1, 'sha256':'a'*64,
              'url':'https://example.com/'+path, 'origin':{'type':'drewcraft_release'}} for path in paths]
    files[2]['sha256'] = sha256_file(previous)
    manifest = {'schemaVersion':1, 'packVersion':'old', 'channel':'development', 'protocolVersion':1,
                'minecraftVersion':'1.21.1', 'java':{'major':21}, 'loader':{}, 'minimumLauncherVersion':'0.1.10',
                'world':{'worldId':'same','worldRevision':3,'generationPackVersion':'same'}, 'files':files}
    base = tmp_path/'base.json'
    base.write_text(json.dumps(manifest))
    return base, jar, manifest, previous


def test_fuel_patch_preserves_world_and_all_unrelated_assets(tmp_path):
    base, jar, original, previous = fixture(tmp_path)
    result = build(base, jar, ROOT/'pack/overlays/v1_1_integration', tmp_path/'output', 'new', previous)
    assert result['world'] == original['world']
    assert result['files'][-1] == original['files'][-1]
    assert result['packVersion'] == 'new'
    assert len(result['files']) == len(original['files'])
    assert all('drewcraft-pack-new' in f['url'] for f in result['files'][:3])
    with zipfile.ZipFile(tmp_path/'output/common--mods--drewcraft-0.1.0-dev.1.jar') as out:
        assert out.read('data/mtsofficialpack/recipe/plating.json') == b'{"original":true}'


def test_experimental_linear_hook_not_allowed_in_fuel_patch(tmp_path):
    base, jar, _, previous = fixture(tmp_path, linear=True)
    with pytest.raises(ValueError, match='experimental'):
        build(base, jar, ROOT/'pack/overlays/v1_1_integration', tmp_path/'output', 'new', previous)
