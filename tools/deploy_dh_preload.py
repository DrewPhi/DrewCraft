"""Owner-authorized 0.1.19 recorder-only deployment. Never changes terrain/LOD format."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT=Path('/srv/drewcraft')
sys.path.insert(0,str(ROOT/'bin'))


def backup(serverctl, old, current):
    """Rotate the accepted DH333 restore point only AFTER its successor verifies."""
    config=serverctl.load_json(ROOT/'state/backup-config.json')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    metadata={'schemaVersion':1,'createdUtc':stamp,'packVersion':old['packVersion'],
              'protocolVersion':old['protocolVersion'],'world':serverctl.require_world_identity(ROOT,old)}
    serverctl._atomic_json(ROOT/'persistent/.drewcraft-backup-metadata.json',metadata)
    result=serverctl.restic_run(config,'backup','--json','--tag','drewcraft','--tag','pre-dh-preload','persistent',cwd=ROOT)
    summaries=[value for line in result.splitlines() if (value:=json.loads(line)).get('message_type')=='summary']
    if len(summaries)!=1 or not __import__('re').fullmatch('[0-9a-f]{64}',summaries[0].get('snapshot_id','')):
        raise RuntimeError('Backup did not confirm one complete snapshot')
    snapshot=summaries[0]['snapshot_id']
    serverctl.restic_run(config,'check')
    receipt=ROOT/'backups'/(stamp+'.restic.json')
    serverctl._atomic_json(receipt,{**metadata,**config,'snapshotId':snapshot,'summary':summaries[0]})
    serverctl._atomic_json(ROOT/'state/backup-hold.json',{
        'snapshotId':snapshot,'receipt':str(receipt),'previousRelease':str(current),
        'reason':'Pre-LOD-preload restore point; owner confirmed DH333 gameplay improvement'})
    serverctl.restic_run(config,'forget','--tag','drewcraft','--group-by','','--keep-last','1','--prune')
    remaining=json.loads(serverctl.restic_run(config,'snapshots','--json','--tag','drewcraft'))
    assert len(remaining)==1 and remaining[0]['id']==snapshot
    print('VERIFIED_BACKUP',snapshot,flush=True)


def deploy(expected_hash):
    import serverctl
    from deploy_fuel_patch import rcon
    url='https://github.com/DrewPhi/DrewCraft/releases/download/drewcraft-pack-0.1.19/release-manifest.json'
    with urllib.request.urlopen(url,timeout=120) as response:
        raw=response.read()
    assert hashlib.sha256(raw).hexdigest()==expected_hash
    manifest=json.loads(raw)
    current=(ROOT/'current').resolve()
    old=json.loads((current/'.drewcraft-release-manifest.json').read_text())
    assert old['packVersion']=='0.1.18' and manifest['packVersion']=='0.1.19'
    assert manifest['world']==old['world'] and manifest['worldStorage']==old['worldStorage']
    unchanged=lambda m:[e for e in m['files'] if not e['path'].startswith('mods/drewcraft-')]
    assert unchanged(manifest)==unchanged(old), 'Not a recorder-only update'
    assert json.loads((ROOT/'state/world-storage.json').read_text())['format']=='linear-v1'
    serverctl.require_world_identity(ROOT,manifest)
    with urllib.request.urlopen(manifest['server']['dhPreloadUrl'],timeout=30) as response:
        catalog=json.loads(response.read(8*1024**2))
    assert catalog['identity']['worldId']==manifest['world']['worldId']
    assert catalog['identity']['worldRevision']==manifest['world']['worldRevision']
    release=serverctl.stage_release(ROOT,manifest)
    shutil.copytree(current/'config',release/'config',dirs_exist_ok=True)
    shutil.copy2(current/'user_jvm_args.txt',release/'user_jvm_args.txt')
    serverctl._prepare_service_permissions(release)
    assert 'There are 0 ' in rcon('list'), 'Players online: deployment deferred'
    subprocess.run(['systemctl','stop','drewcraft-pregen'],check=True)
    activated=False
    try:
        assert 'There are 0 ' in rcon('list'), 'Player joined: deployment deferred'
        rcon('save-all flush')
        serverctl.write_health(ROOT,'updating',old,'Installing optional LOD cache support')
        subprocess.run(['systemctl','stop','drewcraft'],check=True)
        backup(serverctl,old,current)
        serverctl.activate(ROOT,release,manifest)
        activated=True
        subprocess.run(['systemctl','start','drewcraft'],check=True)
        for _ in range(120):
            try:
                if 'players online' in rcon('list'):
                    break
            except Exception:
                pass
            time.sleep(5)
        else:
            raise RuntimeError('Server readiness timed out')
        log=(ROOT/'logs/latest.log').read_text()
        assert 'Done (' in log
        for error in ('MixinApplyError','InvalidMixinException','Failed to initialize server','Corrupt Linear region'):
            assert error not in log,error
        assert 'Saved the game' in rcon('save-all flush')
        serverctl.write_health(ROOT,'ready',manifest,'Optional downloadable DH cache enabled')
        subprocess.run(['systemctl','start','drewcraft-pregen'],check=True)
        print('DH_PRELOAD_DEPLOYMENT_COMPLETE 0.1.19',flush=True)
    except Exception:
        if activated:
            subprocess.run(['systemctl','stop','drewcraft'],check=True)
            # Only an added Dist.CLIENT recorder class differs. No world/DB
            # migration exists in this transaction; old app remains compatible.
            serverctl.activate(ROOT,current,old)
        subprocess.run(['systemctl','start','drewcraft','drewcraft-pregen'],check=True)
        serverctl.write_health(ROOT,'ready',old,'LOD preload deployment aborted; previous application retained')
        raise


if __name__=='__main__':
    deploy(sys.argv[1])
