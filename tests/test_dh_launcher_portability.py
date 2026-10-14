"""Real launcher entrypoint through process handoff; no game/account/network.

Run on native Windows/macOS/Linux CI, not only a POSIX developer machine.
"""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'launcher'))
import drewcraft_entry as entry
import drewcraft_bootstrap as bootstrap
import drewcraft_client_defaults as defaults
import dh_config_upgrade as migration
import self_update


@pytest.mark.parametrize('newline', ['\r\n', '\n'])
@pytest.mark.parametrize('without_posix_api', [True, False])
def test_real_entrypoint_migrates_and_reaches_launch_handoff(tmp_path, monkeypatch, newline, without_posix_api):
    app = tmp_path / 'app'
    prism = app / 'prism-data'
    minecraft = prism / 'instances/DrewCraft-test/minecraft'
    (minecraft / 'config').mkdir(parents=True)
    config = minecraft / 'config/DistantHorizons.toml'
    original = newline.join(['_version = 4', '[client.advanced.graphics.quality]',
                'lodChunkRenderDistanceRadius = 96', '[common.worldGenerator]',
                'generatorPlan = "CHUNKS_ONLY"', 'chunkGeneratorMode = "PRE_EXISTING_ONLY"',
                '[client.advanced.graphics.culling]', 'overdrawPrevention = "0.2"',
                'reduceOverdrawWithFastMovement = true', '']).encode()
    config.write_bytes(original)
    (minecraft / 'mods').mkdir()
    jar_bytes = b'DH portability fixture (not a runnable mod)'
    (minecraft / 'mods/DistantHorizons-3.3.3-1.21.1-drewcraft.1.jar').write_bytes(jar_bytes)
    real_sha256 = hashlib.sha256
    def digest(data):
        if data == jar_bytes:
            return SimpleNamespace(hexdigest=lambda: 'b43f5ac302a2ed6039d34f737d3182a0bc771333c71653c06aa7528cae6ecb67')
        return real_sha256(data)
    monkeypatch.setattr(defaults.hashlib, 'sha256', digest)
    if without_posix_api:
        # Remove these attributes from this module's view, without changing
        # the interpreter's global os module or pathlib platform selection.
        portable_os = SimpleNamespace(**{k:v for k,v in vars(migration.os).items()
                                          if k not in ('geteuid', 'chown')})
        monkeypatch.setattr(migration, 'os', portable_os)
    state = {'packVersion':'0.1.18', 'prismRoot':str(prism), 'instanceId':'DrewCraft-test',
             'prismExecutable':'fake-prism-never-executed', 'server':{'address':'example.invalid:25565'}}
    (app / 'state.json').write_text(json.dumps(state))
    (prism / 'accounts.json').write_text(json.dumps({'accounts':[{'testOnly':True}]}))
    monkeypatch.setattr(entry, 'default_app_dir', lambda: app)
    monkeypatch.setattr(self_update, 'maybe_self_update', lambda *args: None)
    monkeypatch.setattr(entry, '_converge_with_progress', lambda *args: state)
    monkeypatch.setattr(bootstrap, 'server_ready', lambda *args: (True, 'Test only'))
    calls = []
    monkeypatch.setattr(bootstrap.subprocess, 'call', lambda args: calls.append(args) or 0)
    # A previous 0.1.14 failure leaves a valid backup; retry must reuse it.
    backup = config.with_name(config.name + '.schema4-' + real_sha256(original).hexdigest()[:16] + '.bak')
    backup.write_bytes(original)
    assert entry.main() == 0
    assert len(calls) == 1 and calls[0][-2:] == ['--server', 'example.invalid:25565']
    assert '--launch' in calls[0] and 'DrewCraft-test' in calls[0]
    assert '_version = 5' in config.read_text()
    assert 'lodChunkRenderDistanceRadius = 96' in config.read_text()
    assert backup.read_bytes() == original
    assert len(list(config.parent.glob('*.bak'))) == 1
    assert not (app / 'launcher.lock').exists()
    assert 'MaxMemAlloc=8192' in (minecraft.parent / 'instance.cfg').read_text()
    # Reopening uses the migrated cached settings and still launches once.
    assert entry.main() == 0
    assert len(calls) == 2
    assert backup.read_bytes() == original
    assert len(list(config.parent.glob('*.bak'))) == 1
