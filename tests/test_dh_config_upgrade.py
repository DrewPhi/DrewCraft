import importlib.util
from pathlib import Path
import pytest
import tomllib

spec = importlib.util.spec_from_file_location('dh_config_upgrade', Path(__file__).parents[1] / 'tools/dh_config_upgrade.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_preserves_settings_comments_backup_and_permissions(tmp_path):
    path = tmp_path / 'DistantHorizons.toml'
    original = ('# user choices\n_version = 4 # upstream schema\n'
                '[common.worldGenerator]\ngeneratorPlan = "CHUNKS_ONLY"\n'
                'chunkGeneratorMode = "PRE_EXISTING_ONLY"\n'
                '[client.advanced.graphics.quality]\nlodChunkRenderDistanceRadius = 96\n'
                '[client.advanced.graphics.culling]\noverdrawPrevention = "0.2"\n')
    path.write_text(original)
    path.chmod(0o640)
    assert module.migrate(path)
    assert path.read_text() == original.replace('_version = 4', '_version = 5')
    assert path.stat().st_mode & 0o777 == 0o640
    backups = list(tmp_path.glob('*.bak'))
    assert len(backups) == 1 and backups[0].read_text() == original
    assert not module.migrate(path)
    assert len(list(tmp_path.glob('*.bak'))) == 1


@pytest.mark.parametrize('content', ['_version = 3\n', '_version = 6\n', '[client]\nx = 1\n', 'broken['])
def test_refuses_unknown_or_malformed_without_mutation(tmp_path, content):
    path = tmp_path / 'DistantHorizons.toml'
    path.write_text(content)
    with pytest.raises((ValueError, tomllib.TOMLDecodeError)):
        module.migrate(path)
    assert path.read_text() == content
    assert not list(tmp_path.glob('*.bak'))


@pytest.mark.parametrize('newline', ['\r\n', '\n'])
@pytest.mark.parametrize('declaration', ['_version = 4', '_version=4 # DH config', '"_version" = 4', "'_version' = +4"])
def test_accepts_real_line_endings_and_keeps_exact_bytes(tmp_path, newline, declaration):
    path = tmp_path / 'DistantHorizons.toml'
    original = (declaration + newline + '[client.advanced.graphics.quality]' + newline +
                'lodChunkRenderDistanceRadius = 96' + newline).encode()
    path.write_bytes(original)
    assert module.migrate(path)
    assert path.read_bytes() == original.replace(b'4', b'5', 1)
    assert next(tmp_path.glob('*.bak')).read_bytes() == original
    assert not module.migrate(path)
