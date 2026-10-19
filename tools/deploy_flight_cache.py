"""Narrow flight delta: empty server, fresh verified backup, unchanged world."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path('/srv/drewcraft')
sys.path.insert(0,str(ROOT/'bin'))


def main(expected):
    import serverctl
    from deploy_fuel_patch import rcon
    from deploy_dh_preload import backup
    url = 'https://github.com/DrewPhi/DrewCraft/releases/download/drewcraft-pack-0.1.20/release-manifest.json'
    with urllib.request.urlopen(url,timeout=60) as response:
        raw = response.read()
    assert hashlib.sha256(raw).hexdigest()==expected
    manifest = json.loads(raw)
    current = (ROOT/'current').resolve()
    old = json.loads((current/'.drewcraft-release-manifest.json').read_text())
    assert old['packVersion']=='0.1.19' and manifest['packVersion']=='0.1.20'
    assert old['world']==manifest['world'] and old['worldStorage']==manifest['worldStorage']
    added = {'mods/seamlesschunks-neoforge-0.1.0-beta.7.jar','mods/architectury-13.0.11-neoforge.jar',
             'mods/yet_another_config_lib_v3-3.8.2+1.21.1-neoforge.jar','config/seamlesschunks.properties'}
    unchanged_old = [e for e in old['files'] if not e['path'].startswith('mods/chunksending-')]
    assert unchanged_old==[e for e in manifest['files'] if e['path'] not in added]
    assert json.loads((ROOT/'state/world-storage.json').read_text())['format']=='linear-v1'
    serverctl.require_world_identity(ROOT,manifest)
    release = serverctl.stage_release(ROOT,manifest)
    shutil.copytree(current/'config',release/'config',dirs_exist_ok=True)
    shutil.copy2(current/'user_jvm_args.txt',release/'user_jvm_args.txt')
    serverctl._prepare_service_permissions(release)
    assert 'There are 0 ' in rcon('list'), 'Players online; deployment deferred'
    subprocess.run(['systemctl','stop','drewcraft-pregen'],check=True)
    activated = False
    try:
        assert 'There are 0 ' in rcon('list'), 'Player joined; deployment deferred'
        rcon('save-all flush')
        serverctl.write_health(ROOT,'updating',old,'Installing predictive flight chunk delivery')
        subprocess.run(['systemctl','stop','drewcraft'],check=True)
        backup(serverctl,old,current)
        serverctl.activate(ROOT,release,manifest)
        activated = True
        subprocess.run(['systemctl','start','drewcraft'],check=True)
        for _ in range(120):
            try:
                if 'players online' in rcon('list'):
                    break
            except Exception:
                pass
            time.sleep(3)
        else:
            raise RuntimeError('Startup readiness timed out')
        log = (ROOT/'logs/latest.log').read_text()
        assert 'Done (' in log
        for error in ('MixinApplyError','InvalidMixinException','Failed to initialize server','OutOfMemoryError'):
            assert error not in log,error
        assert 'seamlesschunks' in log.lower()
        assert not (release/'mods/chunksending-1.21-3.9.jar').exists()
        assert 'Saved the game' in rcon('save-all flush')
        serverctl.write_health(ROOT,'ready',manifest,'Predictive flight chunk delivery active; owner flight test pending')
        subprocess.run(['systemctl','start','drewcraft-pregen'],check=True)
        serverctl._atomic_json(ROOT/'state/flight-cache-deploy.json',{'status':'ready','packVersion':'0.1.20','manifestSha256':expected})
        print('FLIGHT_CACHE_READY',expected,flush=True)
    except Exception:
        if activated:
            subprocess.run(['systemctl','stop','drewcraft'],check=True)
            serverctl.activate(ROOT,current,old)
        subprocess.run(['systemctl','start','drewcraft','drewcraft-pregen'],check=True)
        serverctl.write_health(ROOT,'ready',old,'Flight update aborted; previous application restored')
        raise


if __name__=='__main__':
    main(sys.argv[1])
