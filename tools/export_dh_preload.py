"""Export immutable visual-LOD tiles from a consistent SQLite online backup.

Never modifies the source database, Minecraft world or pregeneration state.
Publishing the resulting HTTPS catalog is a separate, explicit operation.
"""
import argparse
import base64
from contextlib import closing
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'launcher'))
from dh_preload import DH_SHA256, canonical, file_sha, layout, validate_catalog

TILE_CELLS = 16


def encode_row(row):
    return [{'blob':base64.b64encode(v).decode()} if isinstance(v, bytes) else v for v in row]


def export(source, output, metadata, base_url, previous=None, timeout=900):
    if output.exists():
        raise ValueError('Export requires a fresh output directory')
    if shutil.disk_usage(output.parent).free < source.stat().st_size * 2 + 1024**3:
        raise RuntimeError('Insufficient space for consistent snapshot and export')
    output.mkdir()
    tiles = []
    old_urls = {tile['sha256']:tile['url'] for tile in (previous or {}).get('tiles', [])}
    started = time.monotonic()
    def bounded(*args):
        if time.monotonic()-started > timeout:
            raise TimeoutError('Snapshot/export budget expired; catalog was not published')
    with tempfile.TemporaryDirectory(prefix='dh-export-', dir=output.parent) as temp:
        snapshot = Path(temp) / 'snapshot.sqlite'
        with closing(sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True)) as src, closing(sqlite3.connect(snapshot)) as dest:
            src.backup(dest, pages=4096, progress=bounded, sleep=.05)
        print('CONSISTENT_SNAPSHOT', flush=True)
        with closing(sqlite3.connect(snapshot)) as db:
            assert db.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
            full_layout = layout(db)
            columns = [row[1] for row in full_layout]
            required = {'DetailLevel','PosX','PosZ','Data','Mapping','LastModifiedUnixDateTime'}
            if not required <= set(columns):
                raise ValueError('Unsupported DH FullData schema')
            fingerprint = hashlib.sha256(canonical(full_layout)).hexdigest()
            template = output / 'template.sqlite'
            with closing(sqlite3.connect(template)) as empty, empty:
                objects = db.execute("SELECT type,sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END,name").fetchall()
                for kind, sql in objects:
                    if kind not in ('table', 'index'):
                        raise ValueError('Unexpected SQLite schema object')
                    empty.execute(sql)
                # Only migration bookkeeping, never player data or server keys.
                for row in db.execute('SELECT * FROM Schema ORDER BY SchemaVersionId'):
                    empty.execute('INSERT INTO Schema VALUES (' + ','.join('?' for _ in row) + ')', row)
            template_sha = file_sha(template)
            renamed = output / (template_sha + '.sqlite')
            template.rename(renamed)
            template_info = {'sha256':template_sha, 'size':renamed.stat().st_size, 'url':base_url + '/' + renamed.name}
            bounds = db.execute('SELECT MIN(PosX)*64,MIN(PosZ)*64,(MAX(PosX)+1)*64,(MAX(PosZ)+1)*64 FROM FullData WHERE DetailLevel=0 AND Data IS NOT NULL AND Mapping IS NOT NULL').fetchone()
            if not bounds or bounds[0] is None:
                raise ValueError('No base LOD data available')
            groups = db.execute('SELECT DISTINCT DetailLevel,PosX,PosZ FROM FullData WHERE Data IS NOT NULL AND Mapping IS NOT NULL')
            keys = sorted({(level, x//TILE_CELLS, z//TILE_CELLS) for level,x,z in groups})
            column_sql = ','.join('"' + c + '"' for c in columns)
            for level, tx, tz in keys:
                bounded()
                if not 0 <= level <= 30:
                    raise ValueError('Invalid DH detail level')
                pending = output / 'pending.gz'
                rows = 0
                with pending.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as zipped:
                    zipped.write(canonical({'identity':metadata['identity'], 'layoutSha256':fingerprint}) + b'\n')
                    for row in db.execute(f'SELECT {column_sql} FROM FullData WHERE DetailLevel=? AND PosX>=? AND PosX<? AND PosZ>=? AND PosZ<? AND Data IS NOT NULL AND Mapping IS NOT NULL ORDER BY PosX,PosZ',
                                          (level,tx*TILE_CELLS,(tx+1)*TILE_CELLS,tz*TILE_CELLS,(tz+1)*TILE_CELLS)):
                        zipped.write(canonical(encode_row(row)) + b'\n')
                        rows += 1
                digest = file_sha(pending)
                target = output / (digest + '.jsonl.gz')
                pending.rename(target)
                unit = 64 * (1 << level) * TILE_CELLS
                tiles.append({'sha256':digest, 'size':target.stat().st_size, 'rows':rows, 'detailLevel':level,
                              'bounds':[tx*unit,tz*unit,(tx+1)*unit,(tz+1)*unit],
                              'url':old_urls.get(digest,base_url + '/' + target.name)})
    catalog = {'schemaVersion':1, 'identity':metadata['identity'], 'dhSha256':DH_SHA256,
               'layoutSha256':fingerprint, 'levelKey':metadata['levelKey'],
               'serverKey':metadata.get('serverKey',''), 'spawn':metadata['spawn'],
               'serverName':metadata.get('serverName','DrewCraft'), 'baseBounds':list(bounds),
               'coverage':'Available stored LOD sections; not a guarantee of continuous coverage',
               'template':template_info, 'tiles':tiles,
               'exportedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    catalog['revision'] = hashlib.sha256(canonical(catalog)).hexdigest()
    validate_catalog(catalog, {'server':{'address':metadata['identity']['address']},
                             'world':metadata['identity']})
    (output / 'catalog.json').write_bytes(canonical(catalog))
    print('EXPORT_COMPLETE', len(tiles), 'tiles', flush=True)
    return catalog


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--previous', type=Path)
    args = parser.parse_args()
    export(args.source, args.output, json.loads(args.metadata.read_text()), args.base_url,
           json.loads(args.previous.read_text()) if args.previous else None)
