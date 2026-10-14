"""Finish an explicitly authorized rollout once its remote transaction succeeds.

No credentials are copied to the server. Only promotes the known DH manifest;
rejects a changed client channel instead of overwriting someone else's release.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
POINTER = ROOT / 'build/dh-release-0.1.18/live.json'
NEW_SHA = 'e724ace68689c989f8c5001daccded484666ce946686138b48125219d1bd3a7f'
OLD_SHA = '7d17795ebc8d1da7076a69913233370c24072504c1edb5000959f82c7bef95e2'
LIVE = 'https://github.com/DrewPhi/DrewCraft/releases/download/drewcraft-dev-pack/live.json'


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'DrewCraft-owner-DH-rollout'}), timeout=60) as response:
        return response.read()


def remote(command):
    return subprocess.check_output(['ssh', '-i', '/home/drew/Downloads/drewcraft_oci',
        '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'ubuntu@150.136.96.174', command], text=True, timeout=30)


def main():
    pointer = json.loads(POINTER.read_text())
    assert pointer['manifestSha256'] == NEW_SHA and pointer['packVersion'] == '0.1.18'
    assert hashlib.sha256(fetch(pointer['manifestUrl'])).hexdigest() == NEW_SHA
    for _ in range(70):
        # Successful transient units may be garbage-collected immediately;
        # their durable journal success marker remains authoritative.
        status = remote('sudo journalctl -u drewcraft-dh333-rollout-v2 -n 30 --no-pager')
        if 'DH333_DEPLOYMENT_FAILED' in status or 'Traceback (most recent call last)' in status:
            raise RuntimeError('Remote DH transaction failed; client channel NOT promoted: ' + status)
        if 'DH333_DEPLOYMENT_COMPLETE 0.1.18' in status:
            break
        time.sleep(30)
    else:
        raise TimeoutError('Remote transaction still running; client channel NOT promoted')
    journal = remote('sudo journalctl -u drewcraft-dh333-rollout-v2 -n 30 --no-pager')
    assert 'DH333_DEPLOYMENT_COMPLETE 0.1.18' in journal, journal
    services = remote('sudo systemctl is-active drewcraft drewcraft-pregen')
    assert services.splitlines() == ['active', 'active'], services
    health = json.loads(fetch('http://150.136.96.174:25566/health'))
    assert health.get('packVersion') == '0.1.18' and health.get('joinable') is True, health
    launcher = json.loads(subprocess.check_output(['gh', 'release', 'view', 'launcher-v0.1.13',
                         '--repo', 'DrewPhi/DrewCraft', '--json', 'assets'], text=True))
    names = {asset['name'] for asset in launcher['assets']}
    assert {'DrewCraft-Windows.exe', 'DrewCraft-macOS.dmg', 'DrewCraft-Linux.deb',
            'DrewCraft-Linux-x86_64', 'DrewCraft-macOS-arm64'} <= names
    old = json.loads(fetch(LIVE))
    assert old['manifestSha256'] in (OLD_SHA, NEW_SHA), 'Client channel changed concurrently; refusing promotion'
    if old['manifestSha256'] != NEW_SHA:
        subprocess.run(['gh', 'release', 'upload', 'drewcraft-dev-pack', str(POINTER), '--clobber',
                        '--repo', 'DrewPhi/DrewCraft'], check=True)
    for _ in range(12):
        actual = json.loads(fetch(LIVE + '?dh333-rollout=1'))
        if actual['manifestSha256'] == NEW_SHA:
            break
        time.sleep(5)
    else:
        raise RuntimeError('Pointer uploaded but public cache verification pending')
    result = {'status':'COMPLETE', 'packVersion':'0.1.18', 'launcherVersion':'0.1.13',
              'manifestSha256':NEW_SHA, 'health':health, 'ownerGameplayAcceptance':'PENDING',
              'backup':'Pre-DH333 snapshot held until owner acceptance'}
    (ROOT / 'build/dh-rollout-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
