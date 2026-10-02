import io
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "infra"))
from check_linear_jar import check

ENTRIES = (Path(__file__).parents[1] / "infra/linear-jar-entries.txt").read_text().split()


def make_jar(path, *, names=None, stamp=(1980, 2, 1, 0, 0, 0)):
    if names is None:
        names = ENTRIES
    with zipfile.ZipFile(path, "w") as archive:
        for name in names:
            info = zipfile.ZipInfo(name, date_time=stamp)
            archive.writestr(info, b"content:" + name.encode())
    return path


def test_matching_normalized_jar_passes(tmp_path):
    result = check(make_jar(tmp_path / "linear.jar"))
    assert result["entries"] > 50
    assert result["reproducible"] is True


def test_extra_or_missing_entry_rejected(tmp_path):
    names = ENTRIES
    with pytest.raises(ValueError, match="entry set differs"):
        check(make_jar(tmp_path / "a.jar", names=names + ["evil.class"]))
    with pytest.raises(ValueError, match="entry set differs"):
        check(make_jar(tmp_path / "b.jar", names=names[1:]))


def test_unnormalized_timestamps_rejected(tmp_path):
    with pytest.raises(ValueError, match="reproducibly timestamped"):
        check(make_jar(tmp_path / "c.jar", stamp=(2026, 10, 2, 0, 0, 0)))
