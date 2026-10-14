"""Prove a real DH333 server accepts exported/imported LODs on disposable data."""
from contextlib import closing
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from rcon.source import Client
from export_dh_preload import export
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'launcher'))
from dh_preload import import_tile


def run(root):
    source = root/'world/data/DistantHorizons.sqlite'
    assert source.is_file() and (root/'smoke-result.json').is_file(), 'Requires finished isolated smoke fixture'
    output = root/'preload-export'
    identity = {'address':'localhost:25585','worldId':'disposable-test','worldRevision':1,'dimension':'minecraft:overworld'}
    catalog = export(source,output,{'identity':identity,'levelKey':'test@minecraft:overworld','spawn':[0,0]},
                     'https://github.com/DrewPhi/DrewCraft/releases/download/preload-test')
    cache = root/'imported.sqlite'
    shutil.copy2(output/(catalog['template']['sha256']+'.sqlite'),cache)
    for tile in catalog['tiles']:
        assert import_tile(cache,output/(tile['sha256']+'.jsonl.gz'),catalog,tile)==tile['rows']
    with closing(sqlite3.connect(source)) as original, closing(sqlite3.connect(cache)) as imported:
        expected = original.execute('SELECT * FROM FullData ORDER BY DetailLevel,PosX,PosZ').fetchall()
        actual = imported.execute('SELECT * FROM FullData ORDER BY DetailLevel,PosX,PosZ').fetchall()
        # Export excludes null/placeholder rows, not usable LOD data.
        columns = [row[1] for row in original.execute('PRAGMA table_info(FullData)')]
        expected = [row for row in expected if row[columns.index('Data')] is not None and row[columns.index('Mapping')] is not None]
        assert expected == actual, 'Binary LOD/metadata changed during transfer'
        assert imported.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        base = set(imported.execute('SELECT PosX,PosZ FROM FullData WHERE DetailLevel=0'))
    source.rename(source.with_name('preload-original.sqlite'))
    cache.rename(source)
    props = dict(line.split('=',1) for line in (root/'server.properties').read_text().splitlines() if '=' in line)
    def rcon(*args):
        with Client('127.0.0.1',int(props['rcon.port']),passwd=props['rcon.password'],timeout=15) as client:
            return client.run(*args)
    log = root/'preload-restart.log'
    with log.open('w') as stream:
        proc = subprocess.Popen(['bash','run.sh','nogui'],cwd=root,stdout=stream,stderr=subprocess.STDOUT)
        try:
            end=time.monotonic()+240
            while time.monotonic()<end:
                assert proc.poll() is None, 'Server exited; inspect preload-restart.log'
                assert not re.search(r'Failed to initialize server|SQLITE_ERROR|no such column|MixinApplyError',log.read_text())
                try:
                    if 'There are 0' in rcon('list'):
                        break
                except OSError:
                    pass
                time.sleep(2)
            else:
                raise TimeoutError('Preload database acceptance boot')
            assert 'Saved the game' in rcon('save-all','flush')
            rcon('stop');proc.wait(timeout=60)
            assert proc.returncode==0
        finally:
            if proc.poll() is None:
                try:rcon('stop');proc.wait(timeout=30)
                except Exception:proc.kill();proc.wait(timeout=15)
    with closing(sqlite3.connect(source)) as imported:
        assert imported.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert base <= set(imported.execute('SELECT PosX,PosZ FROM FullData WHERE DetailLevel=0'))
    result={'status':'PASS','exactRowsTransferred':len(expected),'scope':'Real DH333 exported/imported blobs and schema, server reload/save. Not a rendered client or aircraft test.'}
    (root/'preload-result.json').write_text(json.dumps(result)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    run(Path(sys.argv[1]).resolve())
