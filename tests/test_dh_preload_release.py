import copy
import json
from pathlib import Path
import sys
import zipfile
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / 'tools'))
from build_dh_preload_release import build, RECORDER
from release_contract import sha256_file


def test_preload_delta_preserves_existing_integration_hooks(tmp_path):
    baseline = tmp_path/'baseline.jar'
    compiled = tmp_path/'compiled.jar'
    with zipfile.ZipFile(baseline, 'w') as jar:
        jar.writestr('META-INF/neoforge.mods.toml', b'linear-adapter=true')
        jar.writestr('drewcraft.mixins.json', b'fuel-and-linear-hooks')
    with zipfile.ZipFile(compiled, 'w') as jar:
        jar.writestr(RECORDER, b'\xca\xfe\xba\xbeTEST')
        jar.writestr('drewcraft.mixins.json', b'WRONG-DEFAULT')
    manifest = {'schemaVersion':1,'packVersion':'0.1.18','channel':'candidate',
                'protocolVersion':1,'minecraftVersion':'1.21.1','loader':{},
                'java':{'major':21},'minimumLauncherVersion':'0.1.15',
                'world':{'worldId':'test','worldRevision':3,'generationPackVersion':'old'},
                'server':{'address':'example:25565'}, 'files':[
                    {'side':'common','path':'mods/drewcraft-1.jar','size':baseline.stat().st_size,
                     'sha256':sha256_file(baseline),'url':'https://example/old.jar'},
                    {'side':'common','path':'mods/other.jar','size':1,'sha256':'a'*64,'url':'https://example/other.jar'}]}
    source = tmp_path/'manifest.json'
    source.write_text(json.dumps(manifest))
    result = build(source, baseline, compiled, tmp_path/'out')
    assert result['world'] == manifest['world']
    assert result['files'][1:] == manifest['files'][1:]
    with zipfile.ZipFile(tmp_path/'out/common--mods--drewcraft-1.jar') as jar:
        assert jar.read('drewcraft.mixins.json') == b'fuel-and-linear-hooks'
    with pytest.raises(FileExistsError):
        build(source, baseline, compiled, tmp_path/'out')
