"""Replace only disposable ticked world with pristine verified baseline."""
from pathlib import Path
import shutil
import subprocess

TEST = Path('/srv/drewcraft/linear-verification')
runtime = TEST / 'runtime'
if subprocess.run(['systemctl', 'is-active', '--quiet', 'drewcraft-linear-test']).returncode == 0:
    raise RuntimeError('Test Minecraft is still running')
evidence = TEST / 'anvil-boot-world'
if evidence.exists():
    raise RuntimeError('Anvil boot evidence exists; inspect instead of overwriting')
baseline = TEST / 'baseline/persistent/world'
if shutil.disk_usage(TEST).free < sum(p.stat().st_size for p in baseline.rglob('*') if p.is_file()) + 25_000_000_000:
    raise RuntimeError('Pristine copy would violate disk reserve')
(runtime / 'world').rename(evidence)
shutil.copytree(baseline, runtime / 'world')
shutil.copy2('/tmp/drewcraft-linear-ops/linear-1.21.1-1.3.3+legacy.jar', runtime/'mods')
shutil.copy2(runtime/'disabled-mods/drewcraft-adapter.jar', runtime/'mods/drewcraft-0.1.0-dev.1.jar')
subprocess.run(['chown', '-R', 'drewcraft:drewcraft', str(runtime)], check=True)
print('PRISTINE_WORLD_READY_FOR_CONVERSION', flush=True)
