"""Read-only diagnosis of metadata changes in a stopped conversion copy."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3

from worldgen_guard import NbtReader


class ExactReader(NbtReader):
    def payload(self, kind):
        if kind in (7, 11, 12):
            length = self.number('>i')
            return (kind, self.take(length * {7: 1, 11: 4, 12: 8}[kind]).hex())
        value = super().payload(kind)
        # Preserve scalar tag types as well as their values.
        return value if kind == 10 else (kind, value)


def load(path):
    reader = ExactReader(gzip.decompress(path.read_bytes()))
    if reader.number('>B') != 10:
        raise ValueError('Expected compound root')
    reader.string()
    data = reader.payload(10)
    if reader.pos != len(reader.data):
        raise ValueError('Trailing NBT data')
    return data


def differences(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        result = []
        for key in sorted(a.keys() | b.keys()):
            child = path + '/' + key
            if key not in a or key not in b:
                result.append(child)
            else:
                result.extend(differences(a[key], b[key], child))
        return result
    return [] if a == b else [path]


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            value.update(block)
    return value.hexdigest()


def sqlite_fingerprints(path):
    # The runner also mounts these files read-only; SQLite cannot alter either
    # world while resolving its existing write-ahead log.
    with sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True) as db:
        db.execute('PRAGMA query_only=ON')
        tables = db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        result = {}
        for table, schema in tables:
            quoted = '"' + table.replace('"', '""') + '"'
            columns = db.execute('PRAGMA table_info(' + quoted + ')').fetchall()
            primary = [c[1] for c in sorted(columns, key=lambda c: c[5]) if c[5]]
            order = ','.join('"' + c.replace('"', '""') + '"' for c in primary) if primary else 'rowid'
            hasher = hashlib.sha256()
            count = 0
            for row in db.execute('SELECT * FROM ' + quoted + ' ORDER BY ' + order):
                for value in row:
                    blob = value if isinstance(value, bytes) else repr(value).encode('utf-8')
                    hasher.update(type(value).__name__.encode('ascii') + b':' + str(len(blob)).encode('ascii') + b':' + blob)
                count += 1
            result[table] = {'schema': schema, 'rows': count, 'sha256': hasher.hexdigest()}
            print(json.dumps({'database': str(path), 'table': table, 'rows': count}), flush=True)
        return result


def inspect(baseline, converted, check_sqlite=False):
    before, after = load(baseline / 'level.dat'), load(converted / 'level.dat')
    old_mods = {entry['ModId'][1]: entry for entry in before['fml']['LoadingModList'][1]}
    new_mods = {entry['ModId'][1]: entry for entry in after['fml']['LoadingModList'][1]}
    changes = []
    checked = 0
    for source in sorted(baseline.rglob('*')):
        if not source.is_file() or source.suffix in ('.mca', '.mcc') or source.name == 'session.lock':
            continue
        relative = source.relative_to(baseline)
        target = converted / relative
        if not target.is_file() or digest(source) != digest(target):
            changes.append(str(relative))
        checked += 1
    old = load(converted / 'level.dat_old')
    result = {
        'levelDatChangedPaths': differences(before, after),
        'lastPlayedBefore': before['Data']['LastPlayed'],
        'lastPlayedAfter': after['Data']['LastPlayed'],
        'modsAdded': {key: new_mods[key] for key in new_mods.keys() - old_mods.keys()},
        'modsRemoved': sorted(old_mods.keys() - new_mods.keys()),
        'modsChanged': sorted(key for key in old_mods.keys() & new_mods.keys() if old_mods[key] != new_mods[key]),
        'nonRegionFilesChecked': checked,
        'changedNonRegionFiles': changes,
        'convertedLevelDatOldEqualsBaselineLevelDat': old == before,
        'convertedLevelDatOldChangedPathsAgainstBaselineCurrent': differences(before, old),
        'convertedLevelDatOldLastPlayed': old['Data']['LastPlayed'],
    }
    if check_sqlite:
        databases = [sqlite_fingerprints(root / 'data/DistantHorizons.sqlite') for root in (baseline, converted)]
        result['dhSqliteLogicalContentEqual'] = databases[0] == databases[1]
        result['dhSqliteTables'] = databases
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('baseline', type=Path)
    parser.add_argument('converted', type=Path)
    parser.add_argument('--sqlite', action='store_true')
    args = parser.parse_args()
    print(json.dumps(inspect(args.baseline, args.converted, args.sqlite)), flush=True)
