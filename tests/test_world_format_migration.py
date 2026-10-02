import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / 'infra'))
import world_format_migration as migration

ctl = migration.serverctl


def make_manifest(*, storage=None, with_linear_mod=False):
    files = []
    if with_linear_mod:
        files.append({'path': 'mods/linear-1.21.1-1.3.3+legacy.jar', 'side': 'server',
                      'size': 1, 'sha256': '0' * 64,
                      'url': 'https://example.invalid/x', 'managed': True})
    manifest = {'schemaVersion': 1, 'packVersion': 'test', 'channel': 'candidate',
                'protocolVersion': 1, 'minecraftVersion': '1.21.1',
                'loader': {'id': 'neoforge', 'version': '21.1.250'},
                'java': {'major': 21}, 'minimumLauncherVersion': '0.1.0',
                'world': {'worldId': 'w', 'worldRevision': 1,
                          'generationPackVersion': 'drewcraft-worldgen-1'},
                'files': files}
    if storage is not None:
        manifest['worldStorage'] = storage
    return ctl.validate_manifest(manifest)


def pin_anvil_world(tmp_path):
    old = tmp_path / 'releases/old'
    old.mkdir(parents=True)
    (tmp_path / 'current').symlink_to(old, target_is_directory=True)
    receipt = tmp_path / 'backups/snapshot.restic.json'
    ctl._atomic_json(receipt, {'snapshotId': 'a' * 64})
    region = tmp_path / 'persistent/world/region'
    region.mkdir(parents=True, exist_ok=True)
    (region / 'r.0.0.mca').write_bytes(b'anvil')
    migration.pin(tmp_path, receipt)
    return receipt


def test_authorize_requires_hold_and_stopped(tmp_path):
    (tmp_path / 'persistent/world/region').mkdir(parents=True)
    with pytest.raises(RuntimeError, match='pinned backup'):
        migration.authorize_migration(tmp_path, stopped=True)
    pin_anvil_world(tmp_path)
    with pytest.raises(RuntimeError, match='stopped'):
        migration.authorize_migration(tmp_path, stopped=False)
    state = migration.authorize_migration(tmp_path, stopped=True)
    assert state['migrationAuthorized'] is True
    assert state['format'] == 'anvil'


def test_authorize_then_compat_allows_linear_cutover(tmp_path):
    pin_anvil_world(tmp_path)
    linear = make_manifest(storage={'format': 'linear-v1', 'version': '1.3.3'},
                           with_linear_mod=True)
    with pytest.raises(RuntimeError, match='protected world-format'):
        ctl.require_storage_compatibility(tmp_path, linear)
    migration.authorize_migration(tmp_path, stopped=True)
    ctl.require_storage_compatibility(tmp_path, linear)


def test_mark_converted_consumes_authorization(tmp_path):
    pin_anvil_world(tmp_path)
    migration.authorize_migration(tmp_path, stopped=True)
    region = tmp_path / 'persistent/world/region'
    with pytest.raises(RuntimeError, match='No Linear regions'):
        migration.mark_converted(tmp_path, stopped=True)
    (region / 'r.0.0.mca').unlink()
    (region / 'r.0.0.linear').write_bytes(b'linear')
    state = migration.mark_converted(tmp_path, stopped=True)
    assert state == {'schemaVersion': 1, 'format': 'linear-v1'}
    ctl.require_storage_compatibility(
        tmp_path, make_manifest(storage={'format': 'linear-v1', 'version': '1.3.3'},
                                with_linear_mod=True))
    with pytest.raises(RuntimeError, match='Refusing Anvil-only'):
        ctl.require_storage_compatibility(tmp_path, make_manifest())


def test_rotate_pin_supersedes_hold_atomically(tmp_path):
    pin_anvil_world(tmp_path)
    new_receipt = tmp_path / 'backups/fresh.restic.json'
    ctl._atomic_json(new_receipt, {'snapshotId': 'b' * 64})
    with pytest.raises(RuntimeError, match='stopped'):
        migration.rotate_pin(tmp_path, new_receipt, stopped=False)
    hold = migration.rotate_pin(tmp_path, new_receipt, stopped=True)
    assert hold['snapshotId'] == 'b' * 64
    assert hold['receipt'] == str(new_receipt.resolve())


def test_recovery_restores_world_and_app_and_preserves_failed_data(tmp_path):
    old = tmp_path / 'releases/old'
    old.mkdir(parents=True)
    new = tmp_path / 'releases/new'
    new.mkdir()
    (tmp_path / 'current').symlink_to(old, target_is_directory=True)
    receipt = tmp_path / 'backups/snapshot.restic.json'
    migration.serverctl._atomic_json(receipt, {'snapshotId': 'a'*64})
    (tmp_path / 'persistent').mkdir()
    (tmp_path / 'persistent/converted.linear').write_bytes(b'converted')
    migration.pin(tmp_path, receipt)
    (tmp_path / 'current').unlink()
    (tmp_path / 'current').symlink_to(new, target_is_directory=True)
    def restore(receipt, target):
        restored = target / 'persistent'
        restored.mkdir(parents=True)
        (restored / 'original.mca').write_bytes(b'original')
        return restored
    with patch.object(migration.serverctl, 'restore_backup', side_effect=restore):
        with pytest.raises(RuntimeError, match='stopped'):
            migration.recover(tmp_path, stopped=False)
        failed = migration.recover(tmp_path, stopped=True)
    assert (tmp_path / 'current').resolve() == old
    assert (tmp_path / 'persistent/original.mca').read_bytes() == b'original'
    assert (failed / 'converted.linear').read_bytes() == b'converted'
    assert (tmp_path / 'state/backup-hold.json').is_file()


def test_interrupted_restore_leaves_converted_world_and_pin_intact(tmp_path):
    old = tmp_path / 'releases/old'
    old.mkdir(parents=True)
    (tmp_path / 'current').symlink_to(old, target_is_directory=True)
    receipt = tmp_path / 'backups/snapshot.restic.json'
    migration.serverctl._atomic_json(receipt, {'snapshotId': 'b'*64})
    (tmp_path / 'persistent').mkdir()
    (tmp_path / 'persistent/converted.linear').write_bytes(b'keep-converted-data')
    migration.pin(tmp_path, receipt)

    with patch.object(migration.serverctl, 'restore_backup',
                      side_effect=RuntimeError('injected restore interruption')):
        with pytest.raises(RuntimeError, match='injected restore interruption'):
            migration.recover(tmp_path, stopped=True)

    assert (tmp_path / 'persistent/converted.linear').read_bytes() == b'keep-converted-data'
    assert (tmp_path / 'state/backup-hold.json').is_file()
    assert not (tmp_path / 'migration-failed-persistent').exists()
