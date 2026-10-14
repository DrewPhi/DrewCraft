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
