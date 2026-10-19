"""Optional, offline-only visual LOD cache import. No Minecraft chunk files.

Catalogs must come from the configured HTTPS origin. Immutable payload hashes
allow resumable downloads. World identity and schema are checked before writes.
"""
from __future__ import annotations
import base64
from contextlib import closing
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sqlite3
import time
import urllib.parse
import urllib.request

DH_SHA256 = 'b43f5ac302a2ed6039d34f737d3182a0bc771333c71653c06aa7528cae6ecb67'
PRELOAD_SCHEMA = 1


class Cancelled(Exception):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def file_sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    with temp.open('wb') as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def identity(state):
    world = state.get('world', {})
    if not world.get('worldId') or not isinstance(world.get('worldRevision'), int):
        raise ValueError('Preloading requires the current world identity')
    return {'address':state['server']['address'], 'worldId':world['worldId'],
            'worldRevision':world['worldRevision'], 'dimension':'minecraft:overworld'}


def validate_catalog(catalog, state):
    if catalog.get('schemaVersion') != PRELOAD_SCHEMA or catalog.get('identity') != identity(state):
        raise ValueError('LOD catalog belongs to a different world or server')
    if catalog.get('dhSha256') != DH_SHA256:
        raise ValueError('LOD catalog requires a different DH build')
    if not re.fullmatch(r'(?:[A-Za-z0-9_-]+@)?[A-Za-z0-9_-]+(?::[A-Za-z0-9_-]+)?', catalog.get('levelKey', '')) or len(catalog['levelKey']) > 150:
        raise ValueError('Invalid DH world cache key')
    if not re.fullmatch(r'[0-9a-f]{64}', catalog.get('layoutSha256', '')):
        raise ValueError('Invalid database layout fingerprint')
    for key, length in (('spawn',2), ('baseBounds',4)):
        values = catalog.get(key)
        if not isinstance(values,list) or len(values) != length or any(type(v) is not int or abs(v)>2**40 for v in values):
            raise ValueError('Invalid coverage coordinates')
    if not re.fullmatch(r'[A-Za-z0-9_-]{0,150}', catalog.get('serverKey','')):
        raise ValueError('Invalid server cache key')
    tiles = catalog.get('tiles', [])
    if not isinstance(tiles, list) or len(tiles) > 100000:
        raise ValueError('Invalid tile catalog')
    seen = set()
    for tile in [catalog['template'], *tiles]:
        if not re.fullmatch(r'[0-9a-f]{64}', tile.get('sha256', '')):
            raise ValueError('Invalid LOD file hash')
        if not isinstance(tile.get('size'), int) or not 0 < tile['size'] <= 2 * 1024**3:
            raise ValueError('Invalid LOD file size')
        url = urllib.parse.urlparse(tile['url'])
        if url.scheme != 'https' or url.hostname != 'github.com' or not url.path.startswith('/DrewPhi/DrewCraft/releases/download/'):
            raise ValueError('LOD artifacts require the trusted HTTPS release host')
        if tile is not catalog['template']:
            if type(tile.get('detailLevel')) is not int or not 0 <= tile['detailLevel'] <= 30:
                raise ValueError('Invalid tile detail level')
            if type(tile.get('rows')) is not int or not 0 < tile['rows'] <= 256:
                raise ValueError('Invalid LOD tile row count')
            bounds = tile.get('bounds')
            if not isinstance(bounds, list) or len(bounds) != 4 or any(type(v) is not int for v in bounds):
                raise ValueError('Invalid tile bounds')
            if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
                raise ValueError('Empty tile bounds')
            if tile['sha256'] in seen:
                raise ValueError('Duplicate tile')
            seen.add(tile['sha256'])
    return catalog


def intersects(bounds, center, radius):
    x, z = center
    return max(bounds[0]-x, 0, x-bounds[2])**2 + max(bounds[1]-z, 0, z-bounds[3])**2 <= radius**2


def max_radius(catalog, center):
    # Only finest-detail observed coverage defines "all"; coarse parent cells
    # can span enormous empty areas and must not inflate the slider maximum.
    bounds = catalog['baseBounds']
    return math.ceil(max(math.hypot(x-center[0], z-center[1])
                         for x in (bounds[0], bounds[2]) for z in (bounds[1], bounds[3])))


def select_tiles(catalog, center, radius):
    if type(radius) is not int or radius < 0:
        raise ValueError('Invalid radius')
    if radius == 0:
        return []
    return [tile for tile in catalog['tiles'] if intersects(tile['bounds'], center, radius)]


def download(entry, cache, *, progress=lambda event: None, cancelled=lambda: False):
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / entry['sha256']
    if target.exists() and target.stat().st_size == entry['size'] and file_sha(target) == entry['sha256']:
        return target
    partial = target.with_suffix('.part')
    offset = partial.stat().st_size if partial.exists() else 0
    if offset >= entry['size']:
        partial.unlink()
        offset = 0
    headers = {'User-Agent':'DrewCraft-LOD-Preloader'}
    if offset:
        headers['Range'] = f'bytes={offset}-'
    request = urllib.request.Request(entry['url'], headers=headers)
    started, initial = time.monotonic(), offset
    with urllib.request.urlopen(request, timeout=60) as response:
        if offset and response.status != 206:
            offset = initial = 0
        if response.status == 206 and not response.headers.get('Content-Range', '').startswith(f'bytes {offset}-'):
            raise ValueError('Invalid resumed download range')
        with partial.open('ab' if offset else 'wb') as output:
            while True:
                if cancelled():
                    raise Cancelled()
                block = response.read(256 * 1024)
                if not block:
                    break
                offset += len(block)
                if offset > entry['size']:
                    raise ValueError('LOD download exceeds declared size')
                output.write(block)
                rate = (offset-initial) / max(time.monotonic()-started, .001)
                progress({'phase':'download', 'label':'Distant terrain', 'downloaded':offset,
                          'total':entry['size'], 'etaSeconds':(entry['size']-offset)/rate if rate else 0})
    if offset != entry['size'] or file_sha(partial) != entry['sha256']:
        raise ValueError('LOD download failed size/hash verification')
    os.replace(partial, target)
    return target


def layout(connection):
    return [list(row) for row in connection.execute('PRAGMA table_info(FullData)')]


def decode_row(row):
    return [base64.b64decode(v['blob'], validate=True) if isinstance(v, dict) and set(v) == {'blob'} else v for v in row]


def import_tile(database, archive, catalog, tile, *, cancelled=lambda: False):
    # A real write transaction fails safely if Minecraft has the DB locked.
    # The UI additionally refuses to run when the managed instance is active.
    with closing(sqlite3.connect(database, timeout=1)) as connection, connection:
        if file_sha(archive) != tile['sha256']:
            raise ValueError('LOD payload hash mismatch')
        actual_layout = layout(connection)
        if hashlib.sha256(canonical(actual_layout)).hexdigest() != catalog['layoutSha256']:
            raise ValueError('Client/server LOD database layouts differ')
        columns = [row[1] for row in actual_layout]
        if any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', c) for c in columns):
            raise ValueError('Invalid LOD column name')
        connection.execute('BEGIN IMMEDIATE')
        connection.execute('CREATE TABLE IF NOT EXISTS DrewCraftPreload (Identity TEXT PRIMARY KEY, Value TEXT NOT NULL)')
        owner = canonical(catalog['identity']).decode()
        saved = connection.execute("SELECT Value FROM DrewCraftPreload WHERE Identity='world'").fetchone()
        if saved and saved[0] != owner:
            raise ValueError('Cache belongs to another world')
        connection.execute("INSERT OR IGNORE INTO DrewCraftPreload VALUES ('world',?)", (owner,))
        receipt = 'tile:' + tile['sha256']
        if connection.execute('SELECT 1 FROM DrewCraftPreload WHERE Identity=?', (receipt,)).fetchone():
            return 0
        quoted = ','.join('"'+c+'"' for c in columns)
        assignments = ','.join(f'"{c}"=excluded."{c}"' for c in columns if c not in ('DetailLevel','PosX','PosZ'))
        sql = (f'INSERT INTO FullData ({quoted}) VALUES ({",".join("?" for _ in columns)}) '
               f'ON CONFLICT (DetailLevel,PosX,PosZ) DO UPDATE SET {assignments} '
               'WHERE excluded.LastModifiedUnixDateTime > FullData.LastModifiedUnixDateTime')
        rows = 0
        with gzip.open(archive, 'rt', encoding='utf-8') as stream:
            header = json.loads(stream.readline(1024 * 1024))
            if header != {'identity':catalog['identity'], 'layoutSha256':catalog['layoutSha256']}:
                raise ValueError('LOD tile identity differs from catalog')
            while True:
                line = stream.readline(32 * 1024 * 1024)
                if not line:
                    break
                if len(line) >= 32 * 1024 * 1024 or rows >= tile['rows']:
                    raise ValueError('LOD payload exceeds declared bounds')
                if cancelled():
                    raise Cancelled()
                row = decode_row(json.loads(line))
                if len(row) != len(columns):
                    raise ValueError('Malformed LOD row')
                level,x,z = (row[columns.index(c)] for c in ('DetailLevel','PosX','PosZ'))
                if any(type(v) is not int for v in (level,x,z)) or level != tile['detailLevel']:
                    raise ValueError('LOD row belongs to a different detail level')
                unit = 64 * (1 << level)
                bounds = tile['bounds']
                if not (bounds[0] <= x*unit and (x+1)*unit <= bounds[2] and bounds[1] <= z*unit and (z+1)*unit <= bounds[3]):
                    raise ValueError('LOD row lies outside its declared tile')
                connection.execute(sql, row)
                rows += 1
        if rows != tile['rows']:
            raise ValueError('Incomplete LOD tile')
        connection.execute('INSERT INTO DrewCraftPreload VALUES (?,?)', (receipt, str(rows)))
        return rows


def server_folder(catalog, config):
    if catalog.get('serverKey'):
        return catalog['serverKey']
    address = catalog['identity']['address']
    # Initial integration is the managed IPv4/DNS server entry. Refuse unknown
    # address layouts instead of guessing a path that DH would never use.
    if address.count(':') > 1:
        raise ValueError('IPv6 cache naming requires a separate compatibility check')
    ip, _, port = address.partition(':')
    clean = lambda value: re.sub(r'[\\/:*?"<>|]', '', value)
    ip, port = clean(ip), clean(port)
    name = clean(catalog['serverName'])
    mode = config.get('client',{}).get('advanced',{}).get('multiplayer',{}).get('serverFolderNameMode','NAME_ONLY')
    names = {'NAME_ONLY':name, 'IP_ONLY':ip, 'NAME_IP':name + ', IP ' + ip,
             'NAME_IP_PORT':name + ', IP ' + ip + ('-' + port if port else '')}
    if mode not in names:
        raise ValueError('This custom DH folder-name mode has not been verified; skipping preload')
    # Guava PercentEscaper("", true) escapes punctuation that urllib keeps
    # unconditionally safe, including IP-address dots and underscores.
    return ''.join(chr(b) if 48<=b<=57 or 65<=b<=90 or 97<=b<=122 else '+' if b==32 else f'%{b:02X}'
                   for b in names[mode].encode('utf-8'))


def last_center(minecraft, catalog):
    path = minecraft / 'drewcraft-last-location.json'
    if path.is_file():
        try:
            record = json.loads(path.read_text())
            if record.get('identity') == catalog['identity'] and all(type(record.get(k)) is int for k in ('x','z')):
                return [record['x'],record['z']], 'Last logout location'
        except (ValueError, OSError):
            pass
    return catalog['spawn'], 'World spawn (no matching logout location recorded yet)'


def enable_stable_cache_name(path):
    """Only after successful user-approved preload; retain old cache folders."""
    import tomllib
    text = path.read_text()
    lines = text.splitlines()
    table = '[client.advanced.multiplayer]'
    start = next((i for i,line in enumerate(lines) if line.strip()==table),None)
    replacement = 'serverFolderNameMode = "IP_ONLY"'
    if start is None:
        lines += ['',table,replacement]
    else:
        end = next((i for i in range(start+1,len(lines)) if lines[i].strip().startswith('[')),len(lines))
        index = next((i for i in range(start+1,end) if re.match(r'\s*serverFolderNameMode\s*=',lines[i])),None)
        if index is None:
            lines.insert(start+1,replacement)
        else:
            lines[index] = replacement
    updated = '\n'.join(lines)+'\n'
    tomllib.loads(updated)
    pending = path.with_name(path.name+'.preload.tmp')
    pending.write_text(updated)
    os.replace(pending,path)


def managed_game_running(prism_root):
    try:
        import psutil
    except ImportError:
        raise RuntimeError('Process safety checker unavailable; skip terrain preload')
    instances = str((prism_root / 'instances').resolve()).casefold()
    for process in psutil.process_iter(['name','cmdline']):
        try:
            if 'java' not in (process.info['name'] or '').lower():
                continue
            command = process.info['cmdline']
            if command is None:
                raise RuntimeError('Cannot inspect a Java process; skip terrain preload')
            if any(instances in arg.casefold() for arg in command):
                return True
        except psutil.NoSuchProcess:
            continue
        except psutil.AccessDenied as error:
            raise RuntimeError('Cannot verify Minecraft process state; skip terrain preload') from error
    return False


def selection_plan(app_dir, minecraft, catalog, center, radius):
    """Read receipts once; estimate only work that has not already been imported."""
    folder = server_folder(catalog, {'client':{'advanced':{'multiplayer':{'serverFolderNameMode':'IP_ONLY'}}}})
    database = Path(minecraft) / 'Distant_Horizons_server_data' / folder / catalog['levelKey'].replace(':','@@') / 'DistantHorizons.sqlite'
    receipts = set()
    if database.exists():
        with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro', uri=True)) as conn:
            if conn.execute("SELECT 1 FROM sqlite_master WHERE name='DrewCraftPreload'").fetchone():
                receipts = {row[0] for row in conn.execute('SELECT Identity FROM DrewCraftPreload')}
    pending = [t for t in select_tiles(catalog,center,radius) if 'tile:'+t['sha256'] not in receipts]
    cache = Path(app_dir) / 'user-data/dh-downloads'
    # Keep slider estimates cheap; download() verifies the full hash before use.
    missing = [t for t in pending if not ((cache/t['sha256']).is_file() and (cache/t['sha256']).stat().st_size==t['size'])]
    return {'database':database, 'pending':pending, 'downloadBytes':sum(t['size'] for t in missing)}


def apply_selection(app_dir, state, catalog, center, radius, *, progress=lambda event:None, cancelled=lambda:False):
    validate_catalog(catalog,state)
    if radius == 0:
        return 0
    prism = Path(state['prismRoot'])
    if managed_game_running(prism):
        raise RuntimeError('Close the running Minecraft instance before preloading terrain')
    minecraft = prism / 'instances' / state['instanceId'] / 'minecraft'
    jar = minecraft / 'mods/DistantHorizons-3.3.3-1.21.1-drewcraft.1.jar'
    if file_sha(jar) != DH_SHA256:
        raise ValueError('Preloader does not match the installed DH build')
    import tomllib
    config = tomllib.loads((minecraft / 'config/DistantHorizons.toml').read_text())
    # Direct-connect and server-list joins can have different display names.
    # Preloading opts this managed instance into DH's IP_ONLY cache naming,
    # but changes the config only after all imports succeed. Old caches stay.
    planned_config = {'client':{'advanced':{'multiplayer':{'serverFolderNameMode':'IP_ONLY'}}}}
    folder = server_folder(catalog,planned_config)
    dimension = catalog['levelKey'].replace(':','@@')
    directory = minecraft / 'Distant_Horizons_server_data' / folder / dimension
    directory.mkdir(parents=True,exist_ok=True)
    database = directory / 'DistantHorizons.sqlite'
    cache = app_dir / 'user-data/dh-downloads'
    plan = selection_plan(app_dir,minecraft,catalog,center,radius)
    selected = plan['pending']
    if not selected:
        if not catalog.get('serverKey'):
            enable_stable_cache_name(minecraft / 'config/DistantHorizons.toml')
        progress({'phase':'status','label':'Distant terrain is already up to date'})
        return 0
    required = sum(tile['size'] for tile in selected)
    if shutil.disk_usage(directory).free < required * 4 + plan['downloadBytes'] + catalog['template']['size'] + 1024**3:
        raise RuntimeError('Not enough free disk space for selected terrain and database transaction')
    if not database.exists():
        template = download(catalog['template'],cache,progress=progress,cancelled=cancelled)
        pending = database.with_suffix('.new')
        shutil.copyfile(template,pending)
        os.replace(pending,database)
    imported = 0
    for index,tile in enumerate(selected):
        if cancelled():
            raise Cancelled()
        # Receipts live inside the cache DB, not a stale external marker.
        with closing(sqlite3.connect(database)) as conn:
            table = conn.execute("SELECT 1 FROM sqlite_master WHERE name='DrewCraftPreload'").fetchone()
            applied = table and conn.execute('SELECT 1 FROM DrewCraftPreload WHERE Identity=?',('tile:'+tile['sha256'],)).fetchone()
        if applied:
            continue
        archive = download(tile,cache,progress=progress,cancelled=cancelled)
        if managed_game_running(prism):
            raise RuntimeError('Minecraft started; terrain import stopped')
        progress({'phase':'status','label':f'Installing distant terrain tile {index+1}/{len(selected)}'})
        imported += import_tile(database,archive,catalog,tile,cancelled=cancelled)
    if not catalog.get('serverKey'):
        enable_stable_cache_name(minecraft / 'config/DistantHorizons.toml')
    return imported
