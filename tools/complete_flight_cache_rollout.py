"""Owner-side bounded promotion: never publish clients before exact server readiness."""
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = 'ed94360f816052e852b50b5af05683741ca5ea2f9741f27fe4df29ca17aa91b4'
OLD = '0cc85a766b7757fdfe0b12fb7ca7c9b231a02bbe4f32e67503e1c041df12c830'
PREFIX = 'https://github.com/DrewPhi/DrewCraft/releases/download/'


def fetch(url):
    with urllib.request.urlopen(url,timeout=30) as response:
        return response.read()


def main():
    pointer = ROOT/'build/flight-cache-0.1.20-final/live.json'
    local = json.loads(pointer.read_text())
    assert local['manifestSha256']==EXPECTED
    assert hashlib.sha256(fetch(local['manifestUrl'])).hexdigest()==EXPECTED
    deadline = time.monotonic()+900
    while time.monotonic()<deadline:
        result = subprocess.run(['ssh','-i','/home/drew/Downloads/drewcraft_oci','-o','BatchMode=yes',
            '-o','ConnectTimeout=10','ubuntu@150.136.96.174',
            'sudo systemctl is-active --quiet drewcraft && sudo cat /srv/drewcraft/state/flight-cache-deploy.json'],
            capture_output=True,text=True,timeout=45)
        if result.returncode==0 and result.stdout.strip():
            receipt = json.loads(result.stdout)
            assert receipt=={'status':'ready','packVersion':'0.1.20','manifestSha256':EXPECTED}
            break
        failure = subprocess.run(['ssh','-i','/home/drew/Downloads/drewcraft_oci','-o','BatchMode=yes',
            '-o','ConnectTimeout=10','ubuntu@150.136.96.174',
            'sudo systemctl is-failed --quiet drewcraft-flight-cache-20261019'],timeout=30)
        if failure.returncode==0:
            raise RuntimeError('Server deployment failed; client channel remains unchanged')
        time.sleep(30)
    else:
        raise TimeoutError('Server readiness pending; client channel remains unchanged')
    live = json.loads(fetch(PREFIX+'drewcraft-dev-pack/live.json'))
    assert live['manifestSha256'] in (OLD,EXPECTED), 'Client channel changed elsewhere; refusing overwrite'
    subprocess.run(['gh','release','upload','drewcraft-dev-pack',str(pointer),'--clobber','--repo','DrewPhi/DrewCraft'],check=True,timeout=120)
    assert json.loads(fetch(PREFIX+'drewcraft-dev-pack/live.json'))['manifestSha256']==EXPECTED
    (ROOT/'build/flight-cache-rollout-state.json').write_text(json.dumps({'status':'complete','packVersion':'0.1.20','manifestSha256':EXPECTED})+'\n')
    print('CLIENT_AND_SERVER_PROMOTED 0.1.20',flush=True)


if __name__=='__main__':
    main()
