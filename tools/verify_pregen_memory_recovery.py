"""Bounded native-DH progress/heap-error verification after the recovery job."""
import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT=Path('/srv/drewcraft')
sys.path.insert(0,str(ROOT/'bin'))


def radius(response):
    match=re.search(r'Generated radius:\s*([\d.]+)\s*/',response)
    return float(match.group(1)) if match else None


def verify():
    import serverctl
    from deploy_fuel_patch import rcon
    deadline=time.monotonic()+5400
    while True:
        journal=subprocess.check_output(['journalctl','-u','drewcraft-pregen-memory-recovery-20261014','-n','45','--no-pager'],text=True)
        if 'PREGEN_MEMORY_RECOVERY_FAILED' in journal or 'Traceback (most recent call last)' in journal:
            raise RuntimeError('Recovery job failed; verification/deployment held')
        if 'PREGEN_MEMORY_RECOVERY_COMPLETE' in journal:
            break
        if time.monotonic()>deadline:
            raise TimeoutError('Recovery did not complete within verification budget')
        time.sleep(30)
    directory=re.search(r'RECOVERY_DIRECTORY (/srv/drewcraft/state/pregen-memory-recovery-[A-Za-z0-9]+)',journal)
    assert directory, 'Missing saved pre-recovery checkpoint'
    before=json.loads((Path(directory.group(1))/'pregen.json').read_text())
    completed=before.get('dhCompletedJobs',0)
    first=None
    first_response=None
    started=time.monotonic()
    while time.monotonic()-started<3600:
        text=(ROOT/'logs/latest.log').read_text()
        state=json.loads((ROOT/'state/pregen.json').read_text())
        if 'OutOfMemoryError' in text or state.get('phase')=='fault_paused':
            raise RuntimeError('Generation fault or memory error recurred; rollout remains held')
        response=rcon('dh pregen status')
        current=radius(response)
        print('NATIVE_DH',response.strip(),flush=True)
        complete=state.get('dhCompletedJobs',0)>completed
        advancing=first is not None and current is not None and current>first and time.monotonic()-started>=60
        if complete or advancing:
            group=subprocess.check_output(['systemctl','show','drewcraft','--property=ControlGroup','--value'],text=True).strip()
            java=[int(pid) for pid in (Path('/sys/fs/cgroup')/group.lstrip('/')/'cgroup.procs').read_text().split()
                  if (Path('/proc')/pid/'comm').read_text().strip()=='java']
            assert len(java)==1
            jcmd='/opt/drewcraft/runtime/java-21-jdk/jdk-21.0.12.1+1/bin/jcmd'
            properties=subprocess.check_output(['sudo','-u','drewcraft',jcmd,str(java[0]),'VM.system_properties'],text=True,timeout=30)
            assert re.search(r'(?m)^chunky\.maxWorkingCount=2$',properties), 'Concurrency limit not active in JVM'
            import tomllib
            assert tomllib.loads((ROOT/'current/config/linear-server.toml').read_text())['regionCacheSize']==8
            stat=(ROOT/'logs/latest.log').stat()
            evidence={'status':'pass','verifiedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      'logIdentity':[stat.st_dev,stat.st_ino], 'javaPid':java[0],
                      'firstDhStatus':first_response,'verifiedDhStatus':response,
                      'completedJobsBefore':completed,'completedJobsAfter':state.get('dhCompletedJobs',0),
                      'regionCacheSize':8,'chunkyMaxWorkingCount':2,
                      'confirmedCompletedRadius':state['continuousCompletedRadius'],
                      'unfinishedTargetRadius':state['continuousTargetRadius'],
                      'scope':'Native saved-world DH advancement and clean post-recovery log, not a full-world completion or gameplay soak'}
            serverctl._atomic_json(ROOT/'state/pregen-memory-verification.json',evidence)
            print('PREGEN_MEMORY_RUNTIME_VERIFIED',json.dumps(evidence),flush=True)
            return
        if first is None and current is not None:
            first,first_response=current,response
        time.sleep(30)
    raise TimeoutError('No native DH advancement verified; players may have paused generation')


if __name__=='__main__':
    verify()
