import sys
from pathlib import Path
import struct
import zlib
import pytest

sys.path.insert(0, str(Path(__file__).parents[1]/'infra'))
from verify_region_conversion import anvil_payloads, _startup_metadata_matches


def region(path, *, external=False):
    raw = zlib.compress(b'raw chunk NBT')
    payload = b'' if external else raw
    header = struct.pack('>I', (2 << 8) | 1) + bytes(8192 - 4)
    sector = struct.pack('>I', len(payload)+1) + bytes([130 if external else 2]) + payload
    path.write_bytes(header + sector + bytes(4096-len(sector)))
    if external:
        (path.parent/'c.-32.64.mcc').write_bytes(raw)


@pytest.mark.parametrize('external', [False, True])
def test_independent_anvil_reader_supports_internal_and_external(tmp_path, external):
    path = tmp_path/'r.-1.2.mca'
    region(path, external=external)
    assert anvil_payloads(path) == {0: b'raw chunk NBT'}


def test_empty_placeholder_allowed_but_truncation_rejected(tmp_path):
    path = tmp_path/'r.0.0.mca'
    path.touch()
    assert anvil_payloads(path) == {}
    path.write_bytes(b'broken')
    with pytest.raises(ValueError, match='Truncated'):
        anvil_payloads(path)


def test_startup_metadata_only_allows_timestamp_and_linear_entry(monkeypatch, tmp_path):
    import verify_region_conversion as verifier
    baseline = {'Data': {'LastPlayed': 10}, 'fml': {'LoadingModList': [{'ModId': 'minecraft'}]}, 'other': {'keep': 1}}
    converted = {'Data': {'LastPlayed': 20}, 'fml': {'LoadingModList': [{'ModId': 'minecraft'}, {'ModId': 'linear', 'ModVersion': '1.3.3'}]}, 'other': {'keep': 1}}
    values = {tmp_path/'before': baseline, tmp_path/'after': converted}
    monkeypatch.setattr(verifier, 'read_nbt', lambda path: values[path])
    _startup_metadata_matches(tmp_path/'before', tmp_path/'after')


def test_startup_metadata_rejects_world_setting_changes(monkeypatch, tmp_path):
    import verify_region_conversion as verifier
    baseline = {'Data': {'LastPlayed': 10}, 'fml': {'LoadingModList': [{'ModId': 'minecraft'}]}, 'other': {'keep': 1}}
    converted = {'Data': {'LastPlayed': 20}, 'fml': {'LoadingModList': [{'ModId': 'minecraft'}, {'ModId': 'linear', 'ModVersion': '1.3.3'}]}, 'other': {'keep': 2}}
    values = {tmp_path/'before': baseline, tmp_path/'after': converted}
    monkeypatch.setattr(verifier, 'read_nbt', lambda path: values[path])
    with pytest.raises(ValueError, match='Unexpected world metadata'):
        _startup_metadata_matches(tmp_path/'before', tmp_path/'after')
