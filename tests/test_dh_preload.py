from contextlib import closing
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'launcher'))
sys.path.insert(0,str(ROOT/'tools'))
import dh_preload as preload
from export_dh_preload import export

STATE = {'world':{'worldId':'test-world','worldRevision':3},'server':{'address':'150.136.96.174:25565'}}
META = {'identity':preload.identity(STATE),'levelKey':'abc123@minecraft:overworld','spawn':[0,0], 'serverName':'DrewCraft'}
URL = 'https://github.com/DrewPhi/DrewCraft/releases/download/lod-test'


@pytest.fixture
def exported(tmp_path):
    source = tmp_path/'source.sqlite'
    with closing(sqlite3.connect(source)) as db, db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE Schema (SchemaVersionId INTEGER PRIMARY KEY,ScriptName TEXT)')
        db.execute("INSERT INTO Schema VALUES(1,'test.sql')")
        db.execute('CREATE TABLE FullData (DetailLevel INTEGER,PosX INTEGER,PosZ INTEGER,Data BLOB,Mapping BLOB,LastModifiedUnixDateTime INTEGER,PRIMARY KEY(DetailLevel,PosX,PosZ))')
        for level,x,z in [(0,0,0),(0,1,0),(0,20,0),(0,-20,0),(1,0,0)]:
            db.execute('INSERT INTO FullData VALUES(?,?,?,?,?,?)',(level,x,z,b'original-lod'+bytes([x%256]),b'mapping',10))
    output = tmp_path/'export'
    catalog = export(source,output,META,URL)
    return source,output,catalog


def client_db(tmp_path, output, catalog):
    path = tmp_path/'client.sqlite'
    shutil.copy2(output/(catalog['template']['sha256']+'.sqlite'),path)
    return path


def test_radius_zero_negative_tiles_parent_selection_and_bounds(exported):
    source,output,catalog = exported
    assert preload.validate_catalog(catalog,STATE) is catalog
    assert preload.select_tiles(catalog,[0,0],0) == []
    selected = preload.select_tiles(catalog,[0,0],32)
    assert len(selected)==2  # local base tile plus its parent tile
    assert any(t['bounds'][0]<0 for t in catalog['tiles'])
    assert preload.max_radius(catalog,[0,0]) < 2000


def test_import_retains_newer_rows_and_is_idempotent(exported,tmp_path):
    source,output,catalog = exported
    target = client_db(tmp_path,output,catalog)
    with closing(sqlite3.connect(target)) as db,db:
        db.execute("INSERT INTO FullData VALUES(0,0,0,?, ?,100)",(b'newer-client-data',b'mapping'))
    for tile in catalog['tiles']:
        archive = output/(tile['sha256']+'.jsonl.gz')
        assert preload.import_tile(target,archive,catalog,tile)==tile['rows']
        assert preload.import_tile(target,archive,catalog,tile)==0
    with closing(sqlite3.connect(target)) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert db.execute('SELECT COUNT(*) FROM FullData').fetchone()[0]==5
        assert db.execute('SELECT Data FROM FullData WHERE DetailLevel=0 AND PosX=0').fetchone()[0]==b'newer-client-data'


def test_cancelled_tile_rolls_back_partial_import(exported,tmp_path):
    source,output,catalog = exported
    target = client_db(tmp_path,output,catalog)
    tile = next(t for t in catalog['tiles'] if t['rows']==2)
    count = 0
    def cancelled():
        nonlocal count
        count += 1
        return count==2
    with pytest.raises(preload.Cancelled):
        preload.import_tile(target,output/(tile['sha256']+'.jsonl.gz'),catalog,tile,cancelled=cancelled)
    with closing(sqlite3.connect(target)) as db:
        assert db.execute('SELECT COUNT(*) FROM FullData').fetchone()[0]==0
    assert preload.import_tile(target,output/(tile['sha256']+'.jsonl.gz'),catalog,tile)==2


def test_identity_hash_and_schema_fail_without_overwriting(exported,tmp_path):
    source,output,catalog = exported
    wrong = {**STATE,'world':{'worldId':'another-world','worldRevision':3}}
    with pytest.raises(ValueError):
        preload.validate_catalog(catalog,wrong)
    target = client_db(tmp_path,output,catalog)
    tile = catalog['tiles'][0]
    bad = tmp_path/'bad.gz'
    bad.write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='hash'):
        preload.import_tile(target,bad,catalog,tile)
    with closing(sqlite3.connect(target)) as db,db:
        db.execute('ALTER TABLE FullData ADD COLUMN Different INTEGER')
    with pytest.raises(ValueError,match='layouts'):
        preload.import_tile(target,output/(tile['sha256']+'.jsonl.gz'),catalog,tile)


def test_export_reuses_unchanged_tile_urls(exported,tmp_path):
    source,output,catalog = exported
    with closing(sqlite3.connect(source)) as db,db:
        db.execute('UPDATE FullData SET Data=?,LastModifiedUnixDateTime=20 WHERE DetailLevel=0 AND PosX=20',(b'updated',))
    updated = export(source,tmp_path/'export2',META,URL+'-second',previous=catalog)
    old = {tile['sha256']:tile for tile in catalog['tiles']}
    unchanged = [t for t in updated['tiles'] if t['sha256'] in old]
    assert len(unchanged)==len(old)-1
    assert all(t['url']==old[t['sha256']]['url'] for t in unchanged)


def test_cache_folder_matches_dh_guava_percent_escaping(exported):
    _,_,catalog = exported
    assert preload.server_folder(catalog,{})=='DrewCraft'
    assert preload.server_folder(catalog,{'client':{'advanced':{'multiplayer':{'serverFolderNameMode':'NAME_IP'}}}})=='DrewCraft%2C+IP+150%2E136%2E96%2E174'
    assert preload.server_folder({**catalog,'serverKey':'123_fixed'}, {})=='123_fixed'


class Response(io.BytesIO):
    def __init__(self,data,status=200,headers=None):
        super().__init__(data);self.status=status;self.headers=headers or {}


def test_download_resumes_and_validates_hash(tmp_path,monkeypatch):
    data = b'abcdefgh'
    digest = hashlib.sha256(data).hexdigest()
    entry = {'sha256':digest,'size':len(data),'url':URL+'/test.gz'}
    (tmp_path/(digest+'.part')).write_bytes(data[:3])
    def fetch(request,timeout):
        assert request.headers['Range']=='bytes=3-'
        return Response(data[3:],206,{'Content-Range':'bytes 3-7/8'})
    monkeypatch.setattr(preload.urllib.request,'urlopen',fetch)
    assert preload.download(entry,tmp_path).read_bytes()==data


def test_skip_never_checks_processes_or_downloads(monkeypatch,tmp_path):
    monkeypatch.setattr(preload,'managed_game_running',lambda *args:pytest.fail('Skip inspected processes'))
    catalog = {'schemaVersion':1,'identity':preload.identity(STATE),'dhSha256':preload.DH_SHA256,
        'levelKey':'abc@minecraft:overworld','layoutSha256':'a'*64,'spawn':[0,0],'baseBounds':[0,0,64,64],
        'template':{'sha256':'b'*64,'size':100,'url':URL+'/template'},'tiles':[]}
    assert preload.apply_selection(tmp_path,STATE,catalog,[0,0],0)==0


def test_pack_update_preserves_open_wal_cache_consistently(tmp_path):
    import drewcraft_bootstrap as bootstrap
    old = tmp_path/'old'
    new = tmp_path/'new'
    source = old/'Distant_Horizons_server_data/server/world/DistantHorizons.sqlite'
    source.parent.mkdir(parents=True)
    with closing(sqlite3.connect(source)) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE test (value INTEGER)')
        db.execute('INSERT INTO test VALUES (123)')
        db.commit()
        assert source.with_name(source.name+'-wal').exists()
        bootstrap._copy_preserved_user_data(old,new)
    copied = new/source.relative_to(old)
    with closing(sqlite3.connect(copied)) as db:
        assert db.execute('SELECT value FROM test').fetchone()[0]==123
    assert not copied.with_name(copied.name+'-wal').exists()
    assert source.stat().st_ino != copied.stat().st_ino


@pytest.mark.parametrize('key',['..','../escape','/absolute','a/b'])
def test_rejects_catalog_cache_path_traversal(exported,key):
    _,_,catalog = exported
    with pytest.raises(ValueError,match='cache key'):
        preload.validate_catalog({**catalog,'serverKey':key},STATE)
