"""Make one stopped-world snapshot, pin it, resume production, restore isolation.

Run from a disposable directory alongside serverctl/world_format_migration and
with /srv/drewcraft/tools on PYTHONPATH. No key/password is printed.
"""
import json
import pathlib
import shutil
import subprocess
import time
import serverctl
import world_format_migration

ROOT = pathlib.Path('/srv/drewcraft')
TEST = ROOT / 'linear-verification'


def main():
    if TEST.exists():
        raise RuntimeError('Staging already exists; inspect and resume instead of overwriting')
    required = serverctl._tree_bytes(ROOT / 'persistent') * 2 + 25_000_000_000
    if shutil.disk_usage(ROOT).free < required:
        raise RuntimeError('Insufficient capacity for two staging copies and 25 GB reserve')
    from rcon.source import Client
    with Client('127.0.0.1', 25575,
                passwd=pathlib.Path('/etc/drewcraft/rcon-password').read_text().strip(), timeout=10) as c:
        players = c.run('list')
        if 'There are 0 of a max of' not in players:
            raise RuntimeError('Players online or unrecognized response; maintenance deferred')
        c.run('say Brief maintenance for a consistent migration-test snapshot; production will resume on Anvil.')
    subprocess.run(['systemctl', 'stop', 'drewcraft-pregen', 'drewcraft'], check=True)
    try:
        manifest = serverctl.load_json(ROOT / 'current/.drewcraft-release-manifest.json')
        receipt = serverctl.backup(ROOT, manifest, label='pre-linear-verification')
        hold = world_format_migration.pin(ROOT, receipt)
        print('PINNED', json.dumps(hold), flush=True)
    finally:
        subprocess.run(['systemctl', 'start', 'drewcraft', 'drewcraft-pregen'], check=True)
    TEST.mkdir()
    serverctl._atomic_json(TEST / 'baseline.json', {'receipt': str(receipt), 'hold': hold})
    serverctl.restore_backup(receipt, TEST / 'baseline')
    serverctl._atomic_json(TEST / 'baseline-verified.json', {'snapshotId': hold['snapshotId'], 'verified': True})
    print('BASELINE_RESTORED_AND_VERIFIED', flush=True)


if __name__ == '__main__':
    main()
