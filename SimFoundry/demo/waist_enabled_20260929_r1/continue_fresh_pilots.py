"""Serial fresh contracts after an existing live run; never retry or train.

Completed physical failures remain recorded and excluded from training. Only
runtime/integrity failures stop this collection queue. Actual review is separate.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, os, subprocess, sys, time
from run_fresh_waist_pilot import prepare

W=Path(__file__).resolve().parent
REPO=W.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def collector_processes():
    found=[]
    for proc in Path('/proc').glob('[0-9]*/cmdline'):
        try:parts=proc.read_bytes().split(b'\0')
        except (FileNotFoundError,PermissionError,ProcessLookupError):continue
        if any(Path(os.fsdecode(x)).name=='collect_paired_sorting.py' for x in parts if x):
            found.append(str(proc.parent))
    return found


def prior_live(pid,run):
    try:parts=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
    except FileNotFoundError:return False
    if not any(Path(os.fsdecode(x)).name=='run_fresh_waist_pilot.py' for x in parts if x):
        return False
    if os.fsencode(str(run.resolve())) not in parts:
        raise RuntimeError('Prior PID now names a different fresh run')
    return True


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--wait-run',type=Path,required=True)
    p.add_argument('--wait-pid',type=int,required=True)
    p.add_argument('--contracts',type=Path,nargs='+',required=True)
    p.add_argument('--state-file',type=Path,required=True)
    a=p.parse_args()
    if a.state_file.exists():raise ValueError('Fresh queue state path required')
    runner=W/'run_fresh_waist_pilot.py';watcher=W/'watch_fresh_pilot_controls.py'
    collector=REPO/'scripts/collect_paired_sorting.py'
    hashes={str(x):sha(x) for x in (runner,watcher,collector)}
    plan=[]
    for path in a.contracts:
        contract,digest,commands=prepare(path.resolve(),collector)
        out=W/(path.stem.removesuffix('_r2')+'_pilot_r1')
        if out.exists():raise ValueError('Queue output already exists: '+str(out))
        plan.append(dict(contract=str(path.resolve()),contract_sha256=digest,out=str(out),
            geometry_groups=sorted({d['geometry_group'] for d in contract['layouts']}),
            split=sorted({d['planned_split'] for d in contract['layouts']})))
    if len({x['out'] for x in plan})!=len(plan):raise ValueError('Duplicate queue output')
    completed=[]
    def status(stage,**kw):
        payload=dict(stage=stage,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            prior_run=str(a.wait_run.resolve()),prior_pid=a.wait_pid,plan=plan,completed=completed,
            source_sha256=hashes,training_ready=False,**kw)
        pending=a.state_file.with_suffix('.pending');pending.write_text(json.dumps(payload,indent=2));pending.replace(a.state_file)
    env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    try:
        status('waiting_for_existing_pilot')
        while prior_live(a.wait_pid,a.wait_run):time.sleep(10)
        end=json.loads((a.wait_run/'STATUS.json').read_text())
        if end.get('stage')!='numeric_complete_actual_visual_review_pending':
            raise RuntimeError('Prior run ended without complete physical records: '+str(end))
        for item in plan:
            for path,digest in hashes.items():
                if sha(path)!=digest:raise RuntimeError('Queue source changed: '+path)
            if sha(item['contract'])!=item['contract_sha256']:raise RuntimeError('Queued contract changed')
            survivors=collector_processes()
            if survivors:raise RuntimeError('Collector still alive; do not restart: '+str(survivors))
            out=Path(item['out'])
            with (W/(out.name+'_runner.log')).open('w') as log:
                child=subprocess.Popen([sys.executable,str(runner),'--contract',item['contract'],'--out',str(out)],
                    env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            status('starting_pilot',current_run=str(out),runner_pid=child.pid)
            for _ in range(120):
                if (out/'PROTOCOL.json').exists() and (out/'STATUS.json').exists():break
                if child.poll() is not None:raise RuntimeError('Fresh runner exited during initialization')
                time.sleep(.25)
            if not (out/'STATUS.json').exists():
                raise RuntimeError('Initialization observation timeout; inspect live PID, never auto-restart')
            with (W/(out.name+'_controls.log')).open('w') as log:
                control=subprocess.Popen([sys.executable,str(watcher),str(out)],env=env,
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            info=dict(pid=child.pid,scheduler_pid=os.getpid(),control_pid=control.pid,training_ready=False)
            (out/'RUNNING_PROCESS.json').write_text(json.dumps(info,indent=2))
            status('running_pilot',current_run=str(out),processes=info)
            rc=child.wait();end=json.loads((out/'STATUS.json').read_text())
            if rc or end.get('stage')!='numeric_complete_actual_visual_review_pending':
                raise RuntimeError('Fresh run runtime failure; no retry: '+str(end))
            completed.append(dict(**item,final_status=end,actual_review='pending'))
        status('collection_complete_actual_review_required')
    except BaseException as exc:
        status('stopped_requires_inspection',error=str(exc));raise


if __name__=='__main__':main()
