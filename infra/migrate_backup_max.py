"""One-off, verified restic migration. Does not read password contents."""
import json
import pathlib
import shutil
import subprocess

ROOT = pathlib.Path('/srv/drewcraft')
CONFIG = ROOT / 'state/backup-config.json'


def main():
    config = json.loads(CONFIG.read_text())
    old = pathlib.Path(config['repository'])
    new = ROOT / 'backups/restic-max'
    if old != ROOT / 'backups/restic' or new.exists():
        raise RuntimeError('unexpected repository paths; migration needs manual review')
    password = config['passwordFile']

    def run(repo, *args):
        return subprocess.check_output(['restic', '--no-cache', '-r', str(repo),
            '--password-file', password, '--compression', 'max', *args], text=True)

    snapshots = json.loads(run(old, 'snapshots', '--json'))
    expected = str(ROOT / 'persistent')
    if not snapshots or any(s['paths'] != [expected] or 'drewcraft' not in s.get('tags', []) for s in snapshots):
        raise RuntimeError('repository contains unexpected snapshots; refusing deletion')
    newest = max(snapshots, key=lambda s: s['time'])
    receipts = list((ROOT / 'backups').glob('*.restic.json'))
    matching = [p for p in receipts if newest['id'].startswith(json.loads(p.read_text())['snapshotId'])]
    if len(matching) != 1:
        raise RuntimeError('newest snapshot needs exactly one receipt')
    print('Initializing maximum-compression replacement', flush=True)
    print(run(new, 'init', '--repository-version', '2', '--from-repo', str(old),
              '--from-password-file', password, '--copy-chunker-params'), flush=True)
    print(run(new, 'copy', '--from-repo', str(old), '--from-password-file', password, newest['id']), flush=True)
    print('Checking every retained data block before deleting old backups', flush=True)
    print(run(new, 'check', '--read-data'), flush=True)
    retained = json.loads(run(new, 'snapshots', '--json'))
    if len(retained) != 1 or retained[0]['tree'] != newest['tree']:
        raise RuntimeError('replacement snapshot content differs')
    updated = {**config, 'repository': str(new), 'compression': 'max', 'retain': 1}
    receipt = matching[0]
    info = {**json.loads(receipt.read_text()), **updated, 'snapshotId': retained[0]['id']}
    # Atomic pointer changes occur only after a full verified copy. An interrupted
    # migration before this point leaves the original repository available.
    for path, data in ((receipt, info), (CONFIG, updated)):
        temp = path.with_suffix(path.suffix + '.tmp')
        temp.write_text(json.dumps(data, indent=2) + '\n')
        temp.replace(path)
    shutil.rmtree(old)  # Exact, validated dedicated repository; user approved cleanup.
    for stale in receipts:
        if stale != receipt and json.loads(stale.read_text()).get('repository') == str(old):
            stale.unlink()
    print(json.dumps({'status': 'complete', 'removedRestorePoints': len(snapshots)-1,
                      'retainedSnapshot': retained[0]['id'], 'repository': str(new)}), flush=True)


if __name__ == '__main__':
    main()
