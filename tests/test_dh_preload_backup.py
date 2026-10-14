import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
import deploy_dh_preload as deploy


@pytest.mark.parametrize('fail_check',[True,False])
def test_backup_pins_successor_before_pruning_and_keeps_original_on_failure(tmp_path,monkeypatch,fail_check):
    monkeypatch.setattr(deploy,'ROOT',tmp_path)
    hold=tmp_path/'state/backup-hold.json'
    hold.parent.mkdir()
    hold.write_text(json.dumps({'snapshotId':'old'}))
    def atomic(path,value):
        path.parent.mkdir(exist_ok=True,parents=True)
        path.write_text(json.dumps(value))
    calls=[]
    def restic(config,*args,**kwargs):
        calls.append(args[0])
        if args[0]=='backup':
            assert json.loads(hold.read_text())['snapshotId']=='old'
            return json.dumps({'message_type':'summary','snapshot_id':'a'*64})
        if args[0]=='check' and fail_check:
            raise RuntimeError('verification failed')
        if args[0]=='forget':
            assert json.loads(hold.read_text())['snapshotId']=='a'*64
        if args[0]=='snapshots':
            return json.dumps([{'id':'a'*64}])
        return ''
    ctl=SimpleNamespace(load_json=lambda p:{},_atomic_json=atomic,
                        require_world_identity=lambda *args:{},restic_run=restic)
    if fail_check:
        with pytest.raises(RuntimeError):
            deploy.backup(ctl,{'packVersion':'0.1.18','protocolVersion':1},Path('/old'))
        assert json.loads(hold.read_text())['snapshotId']=='old'
        assert 'forget' not in calls
    else:
        deploy.backup(ctl,{'packVersion':'0.1.18','protocolVersion':1},Path('/old'))
        assert calls==['backup','check','forget','snapshots']
