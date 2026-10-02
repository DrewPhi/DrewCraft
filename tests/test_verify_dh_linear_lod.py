import sqlite3
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parents[1]/'infra'))
from verify_dh_linear_lod import inspect


def database(path, *, step=9, data=None):
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE FullData(DetailLevel,PosX,PosZ,MinY,Data,ColumnGenerationStep,Mapping,DataFormatVersion,CompressionMode,DataChecksum,LastModifiedUnixDateTime)')
        conn.execute('INSERT INTO FullData VALUES(0,-44,12,-64,?,?,?,?,0,123,1000)',
                     (data if data is not None else b'\1'*(62*62), bytes([step])*4096, b'minecraft:stone', 2))


def test_real_section_evidence_requires_nonempty_generated_columns(tmp_path):
    path = tmp_path/'dh.sqlite'
    database(path)
    assert inspect(path, -2816, 768)['nonemptyColumns'] == 3844
    with pytest.raises(ValueError, match='no LOD row'):
        inspect(path, 10000, 10000)


@pytest.mark.parametrize('step,data', [(0,None), (9,b'\0'*(62*62))])
def test_empty_or_partial_data_is_not_completion_evidence(tmp_path, step, data):
    path = tmp_path/'dh.sqlite'
    database(path, step=step, data=data)
    with pytest.raises(ValueError):
        inspect(path, -2816, 768)
