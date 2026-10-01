import importlib.util
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

spec = importlib.util.spec_from_file_location('restic_serverctl', Path(__file__).parents[1] / 'infra/serverctl.py')
ctl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ctl)


def fixture_root(tmp_path):
    ctl.ensure_layout(tmp_path)
    identity = {'schemaVersion': 1, 'worldId': 'test', 'worldRevision': 3,
                'generationPackVersion': 'test-3'}
    ctl._atomic_json(tmp_path / 'persistent/world/drewcraft-world.json', identity)
    ctl._atomic_json(tmp_path / 'state/backup-config.json', {
        'backend': 'restic', 'repository': str(tmp_path / 'backups/restic'),
        'passwordFile': '/secret/not-read'})
    return {'packVersion': 'test', 'protocolVersion': 1, 'world': identity}


def test_configured_backup_uses_restic_and_receipt(tmp_path):
    manifest = fixture_root(tmp_path)
    with patch.object(ctl, 'restic_run', side_effect=[json.dumps({
        'message_type': 'summary', 'snapshot_id': 'a' * 64, 'data_added': 100}), '', '',
        json.dumps([{'id': 'a' * 64}])]) as run:
        receipt = ctl.backup(tmp_path, manifest)
    assert receipt.name.endswith('.restic.json')
    assert json.loads(receipt.read_text())['snapshotId'] == 'a' * 64
    assert run.call_args_list[0].args[1] == 'backup'
    assert run.call_args_list[1].args[1] == 'check'
    assert run.call_args_list[2].args[1:] == ('forget', '--tag', 'drewcraft', '--group-by', '', '--keep-last', '1', '--prune')
    assert not list((tmp_path / 'backups').glob('*.tar.gz'))


def test_failed_check_never_prunes_old_snapshot(tmp_path):
    manifest = fixture_root(tmp_path)
    with patch.object(ctl, 'restic_run', side_effect=[json.dumps({
        'message_type': 'summary', 'snapshot_id': 'a' * 64}),
        subprocess.CalledProcessError(1, 'restic')]) as run:
        with pytest.raises(subprocess.CalledProcessError):
            ctl.backup(tmp_path, manifest)
    assert len(run.call_args_list) == 2


def test_restic_always_uses_max_compression():
    config = {'backend': 'restic', 'repository': '/repo', 'passwordFile': '/secret'}
    with patch.object(ctl.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, stdout='')) as run:
        ctl.restic_run(config, 'check')
    assert run.call_args.args[0][-3:] == ['--compression', 'max', 'check']


def test_retention_cannot_be_disabled(tmp_path):
    manifest = fixture_root(tmp_path)
    with pytest.raises(RuntimeError, match='exactly one'):
        ctl.backup(tmp_path, manifest, retain=0)


def test_partial_backup_does_not_write_success_receipt(tmp_path):
    manifest = fixture_root(tmp_path)
    with patch.object(ctl, 'restic_run', side_effect=subprocess.CalledProcessError(3, 'restic')):
        with pytest.raises(subprocess.CalledProcessError):
            ctl.backup(tmp_path, manifest)
    assert not list((tmp_path / 'backups').glob('*.restic.json'))


def test_restic_rejects_copy_of_receipt_as_offhost_backup(tmp_path):
    manifest = fixture_root(tmp_path)
    with pytest.raises(RuntimeError, match='replication'):
        ctl.backup(tmp_path, manifest, copy_dir=tmp_path / 'external')


def test_restore_never_overwrites_existing_target(tmp_path):
    receipt = tmp_path / 'snapshot.restic.json'
    receipt.write_text(json.dumps({'snapshotId': 'a' * 64}))
    target = tmp_path / 'target'
    target.mkdir()
    (target / 'valuable').write_text('keep')
    with pytest.raises(RuntimeError, match='empty'):
        ctl.restore_backup(receipt, target)
    assert (target / 'valuable').read_text() == 'keep'


def test_restore_verifies_and_checks_identity(tmp_path):
    manifest = fixture_root(tmp_path)
    receipt = tmp_path / 'snapshot.restic.json'
    receipt.write_text(json.dumps({'snapshotId': 'a' * 64, 'world': manifest['world']}))
    target = tmp_path / 'restored'

    def restore(config, *args):
        assert args[-1] == '--verify'
        ctl._atomic_json(target / 'persistent/world/drewcraft-world.json', manifest['world'])
        return ''

    with patch.object(ctl, 'restic_run', side_effect=restore):
        assert ctl.restore_backup(receipt, target) == target / 'persistent'
