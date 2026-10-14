from pathlib import Path
import sys
import tomllib
import pytest

sys.path.insert(0,str(Path(__file__).parents[1]/'infra'))
from pregen_memory_limits import apply


def test_memory_limits_preserve_heap_other_settings_and_are_idempotent(tmp_path):
    (tmp_path/'config').mkdir()
    config=tmp_path/'config/linear-server.toml'
    config.write_text('regionCacheSize = 64 # cache\ncompressionLevel = 4\nbackupEnabled = false\n')
    args=tmp_path/'user_jvm_args.txt'
    args.write_text('-Xms4G\n-Xmx8G\n-XX:+UseZGC\n-Dchunky.maxWorkingCount=50\n')
    apply(tmp_path)
    assert tomllib.loads(config.read_text())=={'regionCacheSize':8,'compressionLevel':4,'backupEnabled':False}
    assert args.read_text()=='-Xms4G\n-Xmx8G\n-XX:+UseZGC\n-Dchunky.maxWorkingCount=2\n'
    original=(config.read_bytes(),args.read_bytes())
    apply(tmp_path)
    assert (config.read_bytes(),args.read_bytes())==original


def test_ambiguous_jvm_property_rejected_before_config_write(tmp_path):
    (tmp_path/'config').mkdir()
    config=tmp_path/'config/linear-server.toml'
    config.write_text('regionCacheSize = 64\n')
    (tmp_path/'user_jvm_args.txt').write_text('-Dchunky.maxWorkingCount=1\n-Dchunky.maxWorkingCount=50\n')
    with pytest.raises(ValueError):
        apply(tmp_path)
    assert config.read_text()=='regionCacheSize = 64\n'
