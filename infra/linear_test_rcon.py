"""RCON to disposable localhost test server ONLY; never the production port."""
from pathlib import Path
import sys
from rcon.source import Client

runtime = Path('/srv/drewcraft/linear-verification/runtime')
props = dict(line.split('=', 1) for line in (runtime/'server.properties').read_text().splitlines()
             if '=' in line and not line.startswith('#'))
if props.get('rcon.port') != '25586' or props.get('server-ip') != '127.0.0.1':
    raise RuntimeError('Refusing RCON outside isolated test endpoint')
with Client('127.0.0.1', 25586, passwd=props['rcon.password'], timeout=30) as client:
    print(client.run(*sys.argv[1:]), flush=True)
