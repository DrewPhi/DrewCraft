"""Resume an interrupted restore ONLY in the fixed disposable baseline."""
from pathlib import Path
import serverctl

ROOT = Path('/srv/drewcraft')
TEST = ROOT / 'linear-verification'
metadata = serverctl.load_json(TEST / 'baseline.json')
hold = serverctl.load_json(ROOT / 'state/backup-hold.json')
if hold != metadata['hold']:
    raise RuntimeError('Pinned snapshot changed; refusing restore')
target = TEST / 'baseline'
if target.is_symlink() or not target.is_dir():
    raise RuntimeError('Unexpected disposable baseline target')
receipt = serverctl.load_json(Path(hold['receipt']))
serverctl.restic_run(receipt, 'restore', receipt['snapshotId'], '--target', str(target), '--verify')
identity = serverctl.read_world_identity(target)
if identity != receipt['world']:
    raise RuntimeError('Restored identity mismatch')
serverctl._atomic_json(TEST / 'baseline-verified.json', {'snapshotId': receipt['snapshotId'], 'verified': True})
print('BASELINE_RESTORED_AND_VERIFIED', flush=True)
