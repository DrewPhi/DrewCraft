"""Explicit world+application recovery for format changes, never app-only rollback.

Caller must stop Minecraft/generators before pinning or recovery. Failed files
are moved aside, not deleted. The sole snapshot stays pinned through acceptance.
"""
import os
import pathlib
import re
import shutil
import serverctl

SNAPSHOT_RE = re.compile(r'^[0-9a-f]{8,64}$')


def pin(root: pathlib.Path, receipt: pathlib.Path) -> dict:
    root = root.resolve()
    if (root / 'state/backup-hold.json').exists():
        raise RuntimeError('A migration backup is already pinned')
    receipt = receipt.resolve(strict=True)
    if root / 'backups' not in receipt.parents:
        raise RuntimeError('Receipt must belong to this server')
    info = serverctl.load_json(receipt)
    application = (root / 'current').resolve(strict=True)
    if root / 'releases' not in application.parents:
        raise RuntimeError('Application is outside immutable releases')
    hold = {'schemaVersion': 1, 'receipt': str(receipt),
            'snapshotId': info.get('snapshotId'), 'application': str(application),
            'sourceFormat': 'anvil', 'targetFormat': 'linear'}
    serverctl._atomic_json(root / 'state/backup-hold.json', hold)
    for name in ('pregen.json', 'active-release.json', 'health.json', 'world-storage.json'):
        path = root / 'state' / name
        if path.exists():
            shutil.copy2(path, root / 'state' / ('migration-before-' + name))
    return hold


def authorize_migration(root: pathlib.Path, *, stopped: bool, target: str = 'linear-v1') -> dict:
    """Record explicit operator authorization to convert the pinned Anvil world.

    This is the flag `serverctl.require_storage_compatibility` requires before
    a linear-v1 application may touch an Anvil world. Caller must have stopped
    Minecraft/generators; the pinned backup hold must already exist.
    """
    if not stopped:
        raise RuntimeError('Migration authorization requires stopped Minecraft and generators')
    if target != 'linear-v1':
        raise ValueError('Only linear-v1 migration is supported')
    root = root.resolve()
    hold_path = root / 'state/backup-hold.json'
    if not hold_path.exists():
        raise RuntimeError('Cannot authorize migration without a pinned backup')
    hold = serverctl.load_json(hold_path)
    if not SNAPSHOT_RE.match(str(hold.get('snapshotId', ''))):
        raise RuntimeError('Pinned hold has no valid snapshot; refusing authorization')
    world = root / 'persistent/world'
    if any(world.rglob('r.*.*.linear')):
        raise RuntimeError('World already shows Linear files; refusing fresh conversion authorization')
    if not any(world.rglob('r.*.*.mca')):
        raise RuntimeError('No Anvil regions found; refusing authorization against an empty world')
    state = {'schemaVersion': 1, 'format': 'anvil', 'migrationAuthorized': True,
             'targetFormat': target, 'holdSnapshotId': hold.get('snapshotId')}
    serverctl._atomic_json(root / 'state/world-storage.json', state)
    return state


def mark_converted(root: pathlib.Path, *, stopped: bool, fmt: str = 'linear-v1') -> dict:
    """Consume the conversion authorization once the world verifies as Linear.

    Requires no remaining Anvil/external files and at least one Linear region.
    Clears `migrationAuthorized` so later releases see a plain linear-v1 world.
    """
    if not stopped:
        raise RuntimeError('Marking conversion requires stopped Minecraft and generators')
    if fmt != 'linear-v1':
        raise ValueError('Only linear-v1 conversion can be recorded')
    root = root.resolve()
    if not (root / 'state/backup-hold.json').exists():
        raise RuntimeError('Cannot record conversion without the pinned backup')
    world = root / 'persistent/world'
    if not any(world.rglob('r.*.*.linear')):
        raise RuntimeError('No Linear regions found; refusing to record conversion')
    leftovers = [p for p in world.rglob('*.mca')] + [p for p in world.rglob('*.mcc')]
    if leftovers:
        raise RuntimeError(f'Anvil/external files remain; conversion incomplete: {leftovers[0]}')
    state = {'schemaVersion': 1, 'format': fmt}
    serverctl._atomic_json(root / 'state/world-storage.json', state)
    return state


def rotate_pin(root: pathlib.Path, new_receipt: pathlib.Path, *, stopped: bool) -> dict:
    """Supersede the staging hold with a FRESH verified pre-cutover snapshot.

    Never leaves the server unpinned: the replacement is validated before the
    atomic swap. Use at BP7 once the new snapshot is verified.
    """
    if not stopped:
        raise RuntimeError('Pin rotation requires stopped Minecraft and generators')
    root = root.resolve()
    old_path = root / 'state/backup-hold.json'
    if not old_path.exists():
        raise RuntimeError('No pinned migration backup to rotate; use pin() instead')
    old = serverctl.load_json(old_path)
    new_receipt = new_receipt.resolve(strict=True)
    if root / 'backups' not in new_receipt.parents:
        raise RuntimeError('Receipt must belong to this server')
    info = serverctl.load_json(new_receipt)
    if not SNAPSHOT_RE.match(str(info.get('snapshotId', ''))):
        raise RuntimeError('Replacement receipt has no valid snapshot ID')
    hold = {'schemaVersion': 1, 'receipt': str(new_receipt),
            'snapshotId': info.get('snapshotId'), 'application': old.get('application'),
            'sourceFormat': old.get('sourceFormat', 'anvil'),
            'targetFormat': old.get('targetFormat', 'linear')}
    serverctl._atomic_json(old_path, hold)
    return hold


def recover(root: pathlib.Path, *, stopped: bool) -> pathlib.Path:
    if not stopped:
        raise RuntimeError('Recovery requires stopped Minecraft and generators')
    root = root.resolve()
    hold = serverctl.load_json(root / 'state/backup-hold.json')
    receipt = pathlib.Path(hold['receipt']).resolve(strict=True)
    application = pathlib.Path(hold['application']).resolve(strict=True)
    if root / 'backups' not in receipt.parents or root / 'releases' not in application.parents:
        raise RuntimeError('Pinned recovery paths escape this server')
    staging = root / 'migration-restore'
    failed = root / 'migration-failed-persistent'
    next_link = root / '.current.migration-recovery'
    if staging.exists() or failed.exists() or next_link.exists() or next_link.is_symlink():
        raise RuntimeError('Recovery evidence already exists; inspect before retrying')
    restored = serverctl.restore_backup(receipt, staging)
    # restore_backup verifies repository data and world identity BEFORE replacing.
    (root / 'persistent').rename(failed)
    restored.rename(root / 'persistent')
    os.symlink(application, next_link, target_is_directory=True)
    serverctl._replace_link(next_link, root / 'current')
    for name in ('pregen.json', 'active-release.json', 'health.json', 'world-storage.json'):
        before = root / 'state' / ('migration-before-' + name)
        if before.exists():
            shutil.copy2(before, root / 'state' / name)
        elif name == 'world-storage.json':
            (root / 'state' / name).unlink(missing_ok=True)
    return failed
