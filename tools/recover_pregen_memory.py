"""Stopped-world, checkpoint-preserving recovery from poisoned chunk I/O workers."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT=Path('/srv/drewcraft')
sys.path.insert(0,str(ROOT/'bin'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'infra'))
from pregen_memory_limits import apply as apply_limits
from pregen_controller import existing_world_radius, region_fingerprints


def recovered_state(original, regions):
    state=dict(original)
    completed=int(state.get('continuousCompletedRadius',0))
    target=int(state.get('continuousTargetRadius',0))
    if not state.get('continuousChunky') or not 0<completed<=target or not regions:
        raise ValueError('Missing verified continuous-generation checkpoint or saved terrain')
    radius=existing_world_radius(regions,state['centerX'],state['centerZ'])
    state.update(phase='complete', continuousChunkySuspended=True,
                 chunkyYieldRequested=False, chunkyProgressToken=None,
                 chunkyLastAdvanceEpoch=time.time(), dhStarted=False,
                 dhMaintenanceActive=False, maintenancePaused=False,
                 dhActiveJob=None, dhPendingJobs=[{
                     'kind':'catchup','centerX':state['centerX'],'centerZ':state['centerZ'],
                     'radius':radius,'regions':regions}],
                 dhLastRegionCheckEpoch=0,dhBackfillAttempts=0,
                 dhPyramidCheckEpoch=time.time(), reason=None,
                 memoryRecovery='Linear cache=8; Chunky in-flight=2; saved-world DH first')
    for key in ('workerLogIdentity','workerLogOffset','workerLogTail','faultPausedFromPhase',
                'faultDetectedUtc','chunkyYieldRequestedEpoch'):
        state.pop(key,None)
    assert state['continuousCompletedRadius']==original['continuousCompletedRadius']
    assert state['continuousTargetRadius']==original['continuousTargetRadius']
    return state


def main():
    sys.path.insert(0,str(ROOT/'bin'))
    import serverctl
    from deploy_fuel_patch import rcon
    import deploy_dh_preload
    assert 'There are 0 ' in rcon('list'), 'Players online: recovery deferred'
    current=(ROOT/'current').resolve()
    manifest=json.loads((current/'.drewcraft-release-manifest.json').read_text())
    serverctl.require_world_identity(ROOT,manifest)
    scratch=Path(tempfile.mkdtemp(prefix='pregen-memory-recovery-',dir=ROOT/'state'))
    print('RECOVERY_DIRECTORY',str(scratch),flush=True)
    subprocess.run(['systemctl','stop','drewcraft-pregen'],check=True)
    try:
        original=json.loads((ROOT/'state/pregen.json').read_text())
        assert 'There are 0 ' in rcon('list'), 'Player joined: recovery deferred'
        for source in (ROOT/'state/pregen.json',current/'config/linear-server.toml',current/'user_jvm_args.txt',
                       ROOT/'bin/pregen_controller.py',ROOT/'logs/latest.log'):
            shutil.copy2(source,scratch/source.name)
        tasks=current/'config/chunky/tasks'
        if tasks.exists():
            shutil.copytree(tasks,scratch/'chunky-tasks-before')
        serverctl.write_health(ROOT,'updating',manifest,'Recovering failed chunk I/O workers with lower memory limits')
        print('SAVE',rcon('save-all'),flush=True)
        subprocess.run(['systemctl','stop','drewcraft'],check=True,timeout=150)
        stopped=subprocess.check_output(['systemctl','show','drewcraft','--property=Result','--value'],text=True).strip()
        if stopped!='success':
            raise RuntimeError('Server did not stop cleanly: '+stopped+'; automatic recovery halted')
        assert subprocess.run(['systemctl','is-active','--quiet','drewcraft']).returncode!=0
        if tasks.exists():
            shutil.copytree(tasks,scratch/'chunky-tasks-after')
        print('CLEANLY_STOPPED',flush=True)
        # Existing held snapshot remains pinned until the successor passes check.
        deploy_dh_preload.backup(serverctl,manifest,current)
        print('LIMITS',apply_limits(current),flush=True)
        chunky=current/'config/chunky/config.json'
        config=json.loads(chunky.read_text())
        assert config.get('continueOnRestart') is False, 'Prevent uncontrolled Chunky startup before DH'
        controller=Path(__file__).resolve().parents[1]/'infra/pregen_controller.py'
        shutil.copy2(controller,ROOT/'bin/pregen_controller.py')
        regions=region_fingerprints(ROOT/'persistent/world')
        state=recovered_state(original,regions)
        serverctl._atomic_json(ROOT/'state/pregen.json',state)
        serverctl._atomic_json(scratch/'recovery.json',{
            'phase':'starting','completedRadius':state['continuousCompletedRadius'],
            'unfinishedTargetRadius':state['continuousTargetRadius'],
            'dhCatchupRadius':state['dhPendingJobs'][0]['radius'], 'packVersion':manifest['packVersion']})
        subprocess.run(['systemctl','start','drewcraft'],check=True)
        for _ in range(120):
            try:
                if 'players online' in rcon('list'):
                    break
            except Exception:
                pass
            time.sleep(5)
        else:
            raise RuntimeError('Recovered server did not reach RCON readiness')
        log=(ROOT/'logs/latest.log').read_text()
        assert 'Done (' in log and 'OutOfMemoryError' not in log
        assert 'Saved the game' in rcon('save-all flush')
        subprocess.run(['systemctl','start','drewcraft-pregen'],check=True)
        serverctl.write_health(ROOT,'ready',manifest,'Memory recovery applied; saved-world DH catch-up queued before Chunky')
        print('PREGEN_MEMORY_RECOVERY_COMPLETE',flush=True)
    except Exception:
        subprocess.run(['systemctl','stop','drewcraft-pregen'],check=False)
        serverctl._atomic_json(scratch/'failure.json',{'status':'failed','automaticGenerationStopped':True})
        print('PREGEN_MEMORY_RECOVERY_FAILED: generation held; inspect logs before proceeding',flush=True)
        raise


if __name__=='__main__':
    main()
