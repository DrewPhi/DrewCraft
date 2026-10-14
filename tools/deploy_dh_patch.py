"""Owner-authorized DH-only rollout on Oracle. Run explicitly, not at import.

On post-activation failure, STOP and retain the snapshot; never app-only rollback
a potentially upgraded DH database. No world regeneration or automatic restore.
"""
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path('/srv/drewcraft')
sys.path.insert(0, str(ROOT / 'bin'))


def main():
    import serverctl
    from deploy_fuel_patch import rcon
    from dh_config_upgrade import migrate
    url = 'https://github.com/DrewPhi/DrewCraft/releases/download/drewcraft-pack-0.1.18/release-manifest.json'
    with urllib.request.urlopen(url, timeout=120) as response:
        raw = response.read()
    assert hashlib.sha256(raw).hexdigest() == 'e724ace68689c989f8c5001daccded484666ce946686138b48125219d1bd3a7f'
    manifest = json.loads(raw)
    current = (ROOT / 'current').resolve()
    old = json.loads((current / '.drewcraft-release-manifest.json').read_text())
    assert old['packVersion'] == '0.1.17-rc.2'
    assert manifest['world'] == old['world'] and manifest['worldStorage'] == old['worldStorage']
    def unchanged(m):
        return [e for e in m['files'] if not e['path'].startswith('mods/DistantHorizons-')]
    assert unchanged(manifest) == unchanged(old), 'Not a DH-only update'
    # Installed serverctl predates the general storage guard. This transaction
    # is narrower: exact same Linear manifest and already-converted world only.
    storage = json.loads((ROOT / 'state/world-storage.json').read_text())
    assert storage.get('format') == 'linear-v1'
    assert manifest['worldStorage']['format'] == 'linear-v1'
    assert any(e['path'] == 'mods/linear-1.21.1-1.3.3+legacy.jar' for e in manifest['files'])
    serverctl.require_world_identity(ROOT, manifest)
    release = serverctl.stage_release(ROOT, manifest)
    # This delta changes no config except DH schema; preserve all actual server
    # runtime tuning, including thread/network/flight/Linear settings.
    shutil.copytree(current / 'config', release / 'config', dirs_exist_ok=True)
    shutil.copy2(current / 'user_jvm_args.txt', release / 'user_jvm_args.txt')
    serverctl._prepare_service_permissions(release)
    players = rcon('list')
    assert 'There are 0 ' in players, 'Players online; rerun after they leave'
    print('STAGED_ZERO_PLAYERS', players, flush=True)
    subprocess.run(['systemctl', 'stop', 'drewcraft-pregen'], check=True)
    activated = False
    backed_up = False
    try:
        assert 'There are 0 ' in rcon('list'), 'Player joined before restart'
        rcon('save-all flush')
        serverctl.write_health(ROOT, 'updating', old, 'Owner-authorized DH333 upgrade; preparing verified backup')
        subprocess.run(['systemctl', 'stop', 'drewcraft'], check=True)
        assert subprocess.run(['systemctl', 'is-active', '--quiet', 'drewcraft']).returncode != 0
        recovery = ROOT / 'persistent/operator/dh333-pre-upgrade'
        recovery.mkdir(exist_ok=False)
        shutil.copy2(current / 'config/DistantHorizons.toml', recovery / 'DistantHorizons.toml')
        shutil.copy2(current / '.drewcraft-release-manifest.json', recovery / 'release-manifest.json')
        receipt = serverctl.backup(ROOT, old, label='pre-dh333', retain=1)
        info = json.loads(receipt.read_text())
        assert info.get('snapshotId'), 'No verified snapshot identity'
        # Keep the one pre-upgrade backup protected until owner acceptance.
        serverctl._atomic_json(ROOT / 'state/backup-hold.json', {
            'reason':'DH333 owner gameplay acceptance; recovery requires DH data and app together',
            'snapshotId':info['snapshotId'], 'receipt':str(receipt), 'previousRelease':str(current)})
        backed_up = True
        print('VERIFIED_BACKUP', info['snapshotId'], flush=True)
        config = release / 'config/DistantHorizons.toml'
        migrate(config)
        # DH333's supported sync rate has a hard maximum of 100. Retain the
        # original 150 in the recovery copy, but use a valid runtime value.
        import tomllib
        migrated = tomllib.loads(config.read_text())
        rate = migrated.get('server', {}).get('syncOnLoadRateLimit')
        if rate is not None and rate > 100:
            text, count = re.subn(r'(?m)^([ \t]*syncOnLoadRateLimit[ \t]*=[ \t]*)\d+', r'\g<1>100', config.read_text())
            assert count == 1, 'Ambiguous sync rate setting'
            config.write_text(text)
        serverctl._prepare_service_permissions(release)
        serverctl.activate(ROOT, release, manifest)
        activated = True
        subprocess.run(['systemctl', 'start', 'drewcraft'], check=True)
        for _ in range(90):
            try:
                if 'players online' in rcon('list'):
                    break
            except Exception:
                pass
            time.sleep(5)
        else:
            raise RuntimeError('DH333 startup readiness timed out')
        log = (ROOT / 'logs/latest.log').read_text()
        assert 'Done (' in log
        for error in ('Failed to initialize server', 'MixinApplyError', 'InvalidMixinException', 'Corrupt Linear region', 'Chunky is not loaded'):
            assert error not in log, error
        assert 'Saved the game' in rcon('save-all flush')
        before = tomllib.loads((recovery / 'DistantHorizons.toml').read_text())
        after = tomllib.loads(config.read_text())
        assert after['_version'] == 5
        for table, key in [('common', 'worldGenerator'), ('common', 'multiThreading')]:
            for name, value in before.get(table, {}).get(key, {}).items():
                assert after[table][key].get(name) == value, (table, key, name)
        for key in ('serverId', 'playerBandwidthLimit', 'generationRequestRateLimit', 'syncOnLoadRateLimit', 'enableAdaptiveTransferSpeed'):
            if key in before.get('server', {}):
                expected = min(before['server'][key], 100) if key == 'syncOnLoadRateLimit' else before['server'][key]
                assert after['server'][key] == expected, key
        serverctl.write_health(ROOT, 'ready', manifest, 'DH333 source patch active; owner flight acceptance pending')
        subprocess.run(['systemctl', 'start', 'drewcraft-pregen'], check=True)
        print('DH333_DEPLOYMENT_COMPLETE', manifest['packVersion'], flush=True)
    except Exception:
        if activated:
            subprocess.run(['systemctl', 'stop', 'drewcraft-pregen', 'drewcraft'], check=True)
            serverctl.write_health(ROOT, 'failed', manifest, 'DH333 rollout stopped; protected backup requires world/DH + app recovery')
        else:
            subprocess.run(['systemctl', 'start', 'drewcraft', 'drewcraft-pregen'], check=True)
            serverctl.write_health(ROOT, 'ready', old, 'DH333 rollout aborted before activation')
        print('DH333_DEPLOYMENT_FAILED', 'activated=', activated, 'backup=', backed_up, flush=True)
        raise


if __name__ == '__main__':
    main()
