from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
from recover_pregen_memory import recovered_state


def test_recovery_preserves_frontier_and_budget_and_prioritizes_real_saved_world():
    old={'continuousChunky':True,'continuousCompletedRadius':10240,'continuousTargetRadius':11264,
         'centerX':-1536,'centerZ':-1536,'targetBytes':150000000000,'activeRadius':11264,
         'phase':'continuous_chunky','workerLogOffset':9999,'chunkyYieldRequested':True}
    fixed=recovered_state(old,{'r.-25.-1.linear':[1,1000]})
    for key in ('continuousCompletedRadius','continuousTargetRadius','targetBytes','activeRadius'):
        assert fixed[key]==old[key]
    assert fixed['phase']=='complete' and fixed['continuousChunkySuspended']
    assert not fixed['chunkyYieldRequested'] and not fixed['dhStarted']
    assert 'workerLogOffset' not in fixed
    assert fixed['dhPendingJobs'][0]['kind']=='catchup'
    assert fixed['dhPendingJobs'][0]['radius']==11328
    assert old['chunkyYieldRequested']  # input checkpoint was not mutated


def test_recovery_never_infers_a_completed_circle_from_region_extents():
    with pytest.raises(ValueError):
        recovered_state({'continuousChunky':True,'continuousCompletedRadius':0,
                         'continuousTargetRadius':11264},{'r.0.0.linear':[1,1]})
