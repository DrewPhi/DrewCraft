"""Chain first snapshot completion into the signed relay; no game/client access."""
from pathlib import Path
import subprocess
import time
from refresh_dh_preload import prepare

ROOT=Path('/srv/drewcraft')
OUTPUT=ROOT/'state/dh-lod-export-v2-20261014'

if __name__=='__main__':
    deadline=time.monotonic()+15000
    while not (OUTPUT/'catalog.json').exists():
        if time.monotonic()>deadline:
            raise TimeoutError('Initial LOD export did not complete within budget')
        if subprocess.run(['systemctl','is-active','--quiet','drewcraft-lod-export-v2-20261014']).returncode:
            raise RuntimeError('Initial export stopped without a complete catalog')
        time.sleep(30)
    prepare(ROOT, ROOT/'state/dh-preload-validation-20261014/metadata.json',
            Path('/etc/drewcraft/lod-export-signing.pem'),adopt=OUTPUT)
    subprocess.run(['systemctl','enable','--now','drewcraft-lod-export.timer'],check=True)
    print('INITIAL_LOD_RELAY_READY',flush=True)
