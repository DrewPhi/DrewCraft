"""Bounded, read-only production sampling into a private disposable probe.

No server restart, original DB writes, publication or player position access.
"""
from contextlib import closing
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import struct
import sys
import time
import tomllib

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'launcher'))
sys.path.insert(0,str(REPO/'infra'))
from dh_preload import import_tile
from export_dh_preload import export
from worldgen_guard import read_nbt


def probe(root, output):
    output.mkdir(parents=True,exist_ok=False)
    source = root/'persistent/world/data/DistantHorizons.sqlite'
    saved = read_nbt(root/'persistent/world/level.dat')['Data']
    seed = int(saved['WorldGenSettings']['seed'])
    # Minecraft BiomeManager.obfuscateSeed: Guava sha256().hashLong(seed).asLong()
    # uses little-endian primitive bytes; DH base32hex encodes big-endian long.
    hashed = struct.unpack('<q',hashlib.sha256(struct.pack('<q',seed)).digest()[:8])[0]
    encoded = base64.b32hexencode(struct.pack('>q',hashed)).decode()[:13].lower()
    config = tomllib.loads((root/'current/config/DistantHorizons.toml').read_text())['server']
    prefix = config.get('levelKeyPrefix') or encoded
    world = json.loads((root/'persistent/world/drewcraft-world.json').read_text())
    identity = {'address':'150.136.96.174:25565','worldId':world['worldId'],
                'worldRevision':world['worldRevision'],'dimension':'minecraft:overworld'}
    server_key = config.get('serverKey','').strip()
    if server_key:
        server_key = re.sub('[^a-zA-Z0-9_ -]','',str(config['serverId'])+'_'+server_key).replace(' ','_')
    metadata = {'identity':identity,'levelKey':prefix[:150-len('@minecraft:overworld')]+'@minecraft:overworld',
                'serverKey':server_key,'spawn':[int(saved['SpawnX']),int(saved['SpawnZ'])],'serverName':'DrewCraft'}
    fixture = output/'production-sample.sqlite'
    started = time.monotonic()
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src, closing(sqlite3.connect(fixture)) as dest, dest:
        src.set_progress_handler(lambda:int(time.monotonic()-started>20),2000)
        src.execute('BEGIN')
        for kind,sql in src.execute("SELECT type,sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END,name"):
            if kind not in ('table','index'):
                raise ValueError('Unexpected source schema object')
            dest.execute(sql)
        for row in src.execute('SELECT * FROM Schema ORDER BY SchemaVersionId'):
            dest.execute('INSERT INTO Schema VALUES('+','.join('?' for _ in row)+')',row)
        x,z = (v//64 for v in metadata['spawn'])
        rows = src.execute('SELECT * FROM FullData WHERE DetailLevel=0 AND PosX>=? AND PosX<? AND PosZ>=? AND PosZ<? AND Data IS NOT NULL AND Mapping IS NOT NULL ORDER BY PosX,PosZ LIMIT 256',
                           (x-8,x+8,z-8,z+8)).fetchall()
        if not rows:
            raise ValueError('No stored LODs near spawn')
        positions = [(row[1],row[2]) for row in rows]
        for level, in src.execute('SELECT DISTINCT DetailLevel FROM FullData WHERE DetailLevel>0 ORDER BY DetailLevel'):
            if level>30:
                raise ValueError('Unknown detail level')
            for px,pz in sorted({(px//(1<<level),pz//(1<<level)) for px,pz in positions}):
                row = src.execute('SELECT * FROM FullData WHERE DetailLevel=? AND PosX=? AND PosZ=? AND Data IS NOT NULL AND Mapping IS NOT NULL',(level,px,pz)).fetchone()
                if row:
                    rows.append(row)
        for row in rows:
            dest.execute('INSERT INTO FullData VALUES('+','.join('?' for _ in row)+')',row)
    catalog = export(fixture,output/'tiles',metadata,'https://github.com/DrewPhi/DrewCraft/releases/download/unpublished-probe',timeout=120)
    target = output/'client.sqlite'
    shutil.copy2(output/'tiles'/(catalog['template']['sha256']+'.sqlite'),target)
    for tile in catalog['tiles']:
        import_tile(target,output/'tiles'/(tile['sha256']+'.jsonl.gz'),catalog,tile)
    with closing(sqlite3.connect(fixture)) as original, closing(sqlite3.connect(target)) as client:
        assert client.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert original.execute('SELECT * FROM FullData ORDER BY DetailLevel,PosX,PosZ').fetchall() == client.execute('SELECT * FROM FullData ORDER BY DetailLevel,PosX,PosZ').fetchall()
    (output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    result = {'status':'PASS','baseRows':len(positions),'totalRows':len(rows),
              'payloadBytes':sum(t['size'] for t in catalog['tiles']), 'layoutSha256':catalog['layoutSha256'],
              'sourceModified':False,'scope':'Read-only production sample, full schema and exact binary LOD export/import comparison. Not full catalog or rendered-client acceptance.'}
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    probe(args.root.resolve(),args.output.resolve())
