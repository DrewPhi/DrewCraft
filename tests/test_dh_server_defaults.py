import importlib.util
from pathlib import Path
import tomllib
import pytest

spec = importlib.util.spec_from_file_location("dh_server_defaults", Path(__file__).resolve().parents[1] / "infra/dh_server_defaults.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_policy_preserves_other_settings_and_is_idempotent(tmp_path):
    config = tmp_path / "DistantHorizons.toml"
    config.write_text('[server]\nplayerBandwidthLimit = 6000\n'
                      '[common.worldGenerator]\ngeneratorPlan = "SURFACE_THEN_CHUNKS"\n'
                      'chunkGeneratorMode = "FEATURES"\nlimitIfServerUnhealthy = true\n')
    assert module.apply(config)
    data = tomllib.loads(config.read_text())
    assert data['server']['playerBandwidthLimit'] == 6000
    assert data['common']['worldGenerator'] == {
        'generatorPlan': 'CHUNKS_ONLY', 'chunkGeneratorMode': 'PRE_EXISTING_ONLY',
        'limitIfServerUnhealthy': True,
    }
    assert not module.apply(config)


def test_invalid_config_is_not_modified(tmp_path):
    config = tmp_path / "DistantHorizons.toml"
    config.write_text('[broken')
    with pytest.raises(tomllib.TOMLDecodeError):
        module.apply(config)
    assert config.read_text() == '[broken'
