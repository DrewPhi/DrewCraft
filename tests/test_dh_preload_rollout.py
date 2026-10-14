import json
from pathlib import Path
import sys
from unittest import mock

import pytest

sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
import complete_dh_preload_rollout as rollout


def test_bounded_wait_does_not_spin_or_sleep_after_success():
    with mock.patch.object(rollout.time,'sleep') as sleep:
        values=iter([False,True])
        assert rollout.wait_for(lambda:next(values),120)
        sleep.assert_called_once_with(60)
    with pytest.raises(TimeoutError):
        rollout.wait_for(lambda:False,0)


def test_concurrently_changed_channel_prevents_deploy_or_publication(tmp_path,monkeypatch):
    pointer=tmp_path/'live.json'
    raw=b'manifest'
    pointer.write_text(json.dumps({'packVersion':'0.1.19','manifestSha256':rollout.hashlib.sha256(raw).hexdigest(),
                                   'manifestUrl':'https://example/manifest'}))
    monkeypatch.setattr(rollout,'POINTER',pointer)
    monkeypatch.setattr(rollout,'fetch',lambda url:json.dumps({'manifestSha256':'another-owner-release'}).encode() if url==rollout.LIVE else raw)
    with mock.patch.object(rollout,'remote') as remote, mock.patch.object(rollout,'gh') as gh:
        with pytest.raises(AssertionError,match='Client channel changed'):
            rollout.main()
        remote.assert_not_called()
        gh.assert_not_called()
