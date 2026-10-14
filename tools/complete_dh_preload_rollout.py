"""Local owner-side rollout chain. Secrets remain in their existing trust boundary.

Wait for signed export + public launcher, dispatch verified GitHub publication,
deploy at zero players with backup, then promote the matching client pointer.
Every wait is bounded. State is written to build/dh-preload-rollout-state.json.
"""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

from publish_dh_preload import verify, ORIGIN

ROOT=Path(__file__).resolve().parents[1]
POINTER=ROOT/'build/dh-preload-release-0.1.19/live.json'
STATUS=ROOT/'build/dh-preload-rollout-state.json'
LIVE='https://github.com/DrewPhi/DrewCraft/releases/download/drewcraft-dev-pack/live.json'
OLD='e724ace68689c989f8c5001daccded484666ce946686138b48125219d1bd3a7f'


def state(phase,**extra):
    value={'phase':phase,'updatedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra}
    STATUS.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(value),flush=True)


def fetch(url):
    with urllib.request.urlopen(url,timeout=20) as response:
        body=response.read(12*1024**2+1)
    if len(body)>12*1024**2:
        raise ValueError('Unexpected response size')
    return body


def gh(*args):
    return subprocess.check_output(['gh',*args,'--repo','DrewPhi/DrewCraft'],text=True,timeout=120)


def remote(command):
    return subprocess.check_output(['ssh','-i','/home/drew/Downloads/drewcraft_oci',
        '-o','BatchMode=yes','-o','ConnectTimeout=10','ubuntu@150.136.96.174',command],text=True,timeout=60)


def wait_for(function, seconds):
    deadline=time.monotonic()+seconds
    while True:
        value=function()
        if value:
            return value
        if time.monotonic()>=deadline:
            raise TimeoutError('Rollout gate did not finish in budget')
        time.sleep(60)


def main():
    pointer=json.loads(POINTER.read_text())
    expected=pointer['manifestSha256']
    assert pointer['packVersion']=='0.1.19'
    assert hashlib.sha256(fetch(pointer['manifestUrl'])).hexdigest()==expected
    assert json.loads(fetch(LIVE))['manifestSha256']==OLD, 'Client channel changed; do not overwrite'
    state('waiting_for_verified_memory_recovery')
    def memory_recovered():
        result=remote("sudo python3 -c 'import json,pathlib;p=pathlib.Path(\"/srv/drewcraft/state/pregen-memory-verification.json\");s=pathlib.Path(\"/srv/drewcraft/logs/latest.log\").stat();v=json.loads(p.read_text()) if p.exists() else {};print(v.get(\"status\")==\"pass\" and v.get(\"logIdentity\")==[s.st_dev,s.st_ino])'")
        return result.strip()=='True'
    wait_for(memory_recovered,7200)
    state('waiting_for_signed_export')
    def exported():
        try:
            return json.loads(fetch(ORIGIN+'publication.json'))
        except urllib.error.HTTPError as error:
            if error.code==404:
                return None
            raise
    envelope=wait_for(exported,15000)
    with tempfile.TemporaryDirectory(prefix='dh-signature-check-') as temp:
        catalog=verify(envelope,ROOT/'infra/lod-export-public.pem',Path(temp))
    state('waiting_for_public_launcher',catalogRevision=catalog['revision'])
    def launcher_ready():
        result=subprocess.run(['gh','release','view','launcher-v0.1.16','--repo','DrewPhi/DrewCraft','--json','assets'],capture_output=True,text=True,timeout=60)
        if result.returncode:
            return False
        names={asset['name'] for asset in json.loads(result.stdout)['assets']}
        return {'DrewCraft-Windows.exe','DrewCraft-macOS.dmg','DrewCraft-Linux.deb',
                'DrewCraft-Linux-x86_64','DrewCraft-macOS-arm64'}<=names
    wait_for(launcher_ready,3600)
    state('publishing_catalog')
    dispatched=datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(seconds=3)
    gh('workflow','run','publish-dh-preload.yml','--ref','main')
    def find_run():
        runs=json.loads(gh('run','list','--workflow','publish-dh-preload.yml','--event','workflow_dispatch',
                          '--branch','main','--limit','5','--json','databaseId,createdAt'))
        return next((run['databaseId'] for run in runs if datetime.datetime.fromisoformat(run['createdAt'].replace('Z','+00:00'))>=dispatched),None)
    run_id=wait_for(find_run,180)
    state('publishing_catalog',runId=run_id)
    def published():
        run=json.loads(gh('run','view',str(run_id),'--json','status,conclusion'))
        if run['status']!='completed':
            return False
        if run['conclusion']!='success':
            raise RuntimeError(f'Catalog publication failed: {run_id} {run}')
        return True
    wait_for(published,7500)
    public=json.loads(fetch('https://github.com/DrewPhi/DrewCraft/releases/download/drewcraft-dh-cache/catalog.json'))
    assert public['identity']==catalog['identity']
    assert public['revision']==catalog['revision'], 'Catalog changed concurrently; review before deployment'
    assert json.loads(fetch(LIVE))['manifestSha256']==OLD
    state('deploying_server',runId=run_id,manifestSha256=expected)
    remote('sudo systemd-run --unit=drewcraft-preload-rollout-019 /usr/bin/python3 '
           '/srv/drewcraft/state/dh-preload-validation-code/tools/deploy_dh_preload.py '+expected)
    def deployed():
        journal=remote('sudo journalctl -u drewcraft-preload-rollout-019 -n 45 --no-pager')
        if 'Traceback (most recent call last)' in journal:
            raise RuntimeError('Server deployment failed; client pointer NOT promoted: '+journal)
        return 'DH_PRELOAD_DEPLOYMENT_COMPLETE 0.1.19' in journal
    wait_for(deployed,5400)
    health=json.loads(fetch('http://150.136.96.174:25566/health'))
    assert health.get('packVersion')=='0.1.19' and health.get('joinable') is True
    assert remote('sudo systemctl is-active drewcraft drewcraft-pregen').splitlines()==['active','active']
    state('promoting_client',manifestSha256=expected)
    assert json.loads(fetch(LIVE))['manifestSha256'] in {OLD,expected}
    gh('release','upload','drewcraft-dev-pack',str(POINTER),'--clobber')
    wait_for(lambda:json.loads(fetch(LIVE+'?lod-preload=019'))['manifestSha256']==expected,600)
    state('complete',packVersion='0.1.19',launcherVersion='0.1.16',
          manifestSha256=expected,catalogRevision=public['revision'],
          ownerRenderingAndFlightAcceptance='pending')


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        state('failed',error=str(error))
        raise
