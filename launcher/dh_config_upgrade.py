"""Explicit, stopped-process DH 3.3.1 -> 3.3.3 config migration.

Shared TOML layout contains client and server settings. Preserve the file rather
than letting DH's version mismatch handler delete it.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import tempfile
import tomllib


def migrate(path: Path) -> bool:
    original = path.read_bytes()
    data = tomllib.loads(original.decode('utf-8'))
    if data.get('_version') == 5:
        return False
    if data.get('_version') != 4:
        raise ValueError('Only explicit DH config schema 4 -> 5 is supported')
    updated, count = re.subn(r'(?m)^([ \t]*_version[ \t]*=[ \t]*)4([ \t]*(?:#.*)?)$',
                             r'\g<1>5\2', original.decode('utf-8'), count=1)
    if count != 1:
        raise ValueError('Unrecognized version declaration; refusing to rewrite')
    expected = dict(data, _version=5)
    if tomllib.loads(updated) != expected:
        raise ValueError('Migration changed settings unexpectedly')
    digest = hashlib.sha256(original).hexdigest()
    backup = path.with_name(path.name + '.schema4-' + digest[:16] + '.bak')
    if backup.exists():
        if backup.read_bytes() != original:
            raise ValueError('Existing configuration backup differs')
    else:
        with backup.open('xb') as stream:
            os.chmod(backup, 0o600)
            stream.write(original)
            stream.flush()
            os.fsync(stream.fileno())
    stat = path.stat()
    fd, name = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, stat.st_mode & 0o777)
        if os.geteuid() == 0:
            os.chown(name, stat.st_uid, stat.st_gid)
        if path.read_bytes() != original:
            raise RuntimeError('Config changed during migration; stop Minecraft first')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    args = parser.parse_args()
    print('migrated' if migrate(args.config) else 'already schema 5')
