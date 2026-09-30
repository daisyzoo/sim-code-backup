"""Run one explicit next full group after a verified prior collector exits.
No training, data promotion, core edits or automatic retries.
"""
from pathlib import Path
import argparse,datetime,json,os,subprocess,sys,time
W=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--wait-run',type=Path,required=True);p.add_argument('--wait-pid',type=int,required=True);p.add_argument('--group',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--state-file',type=Path,required=True);a=p.parse_args()
if a.out.exists() or a.state_file.exists():raise ValueError('Fresh output/state paths required')
def status(stage,**kw):
    a.state_file.write_text(json.dumps(dict(stage=stage,pid=os.getpid(),prior_run=str(a.wait_run.resolve()),prior_pid=a.wait_pid,next_group=a.group,out=str(a.out.resolve()),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw),indent=2))
status('waiting_for_existing_collector')
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
try:
    # Settings/source/layout validation has no output side effects.
    subprocess.run([sys.executable,str(W/'run_normal_return_group.py'),'--group',a.group,'--validate-only'],stdout=subprocess.DEVNULL,env=env,check=True)
    while True:
        state=json.loads((a.wait_run/'STATUS.json').read_text())
        proc=Path(f'/proc/{a.wait_pid}/cmdline')
        if proc.exists():
            try:args=proc.read_bytes().split(b'\0')
            except FileNotFoundError:args=[]
            live=any(Path(x.decode()).name=='run_normal_return_group.py' for x in args if x)
        else:live=False
        if live:
            time.sleep(10);continue
        if state.get('stage')!='numeric_complete_actual_visual_review_pending':raise RuntimeError('Prior process ended without complete diagnostic result: '+str(state))
        break
    # No surviving Isaac wrapper/collector is allowed even after parent exit.
    for proc in Path('/proc').glob('[0-9]*/cmdline'):
        try:tokens=proc.read_bytes().split(b'\0')
        except (FileNotFoundError,PermissionError,ProcessLookupError):continue
        if any(Path(x.decode(errors='replace')).name=='collect_paired_sorting.py' for x in tokens if x):raise RuntimeError('An Isaac collector still exists: '+str(proc))
    with (W/(a.out.name+'_runner.log')).open('w') as log:
        runner=subprocess.Popen([sys.executable,str(W/'run_normal_return_group.py'),'--group',a.group,'--out',str(a.out.resolve())],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    status('starting_next_group',runner_pid=runner.pid)
    for _ in range(120):
        if (a.out/'PROTOCOL.json').exists() and (a.out/'STATUS.json').exists():break
        if runner.poll() is not None:raise RuntimeError('Next runner exited during initialization')
        time.sleep(.25)
    if not (a.out/'STATUS.json').exists():raise RuntimeError('Runner initialization observation timed out; inspect live PID, never restart automatically')
    processes=dict(runner_pid=runner.pid,scheduler_pid=os.getpid(),output=str(a.out.resolve()),training_ready=False)
    for name,script in [('complete_audits','complete_swap_audits.py'),('control_audits','watch_bounded_top_lead_evidence.py')]:
        with (W/(a.out.name+'_'+name+'.log')).open('w') as log:child=subprocess.Popen([sys.executable,str(W/script),str(a.out.resolve())],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        processes[name+'_pid']=child.pid
    (a.out/'RUNNING_PROCESS.json').write_text(json.dumps(processes,indent=2));status('running_next_group',processes=processes)
    rc=runner.wait();end=json.loads((a.out/'STATUS.json').read_text())
    if rc or end.get('stage')!='numeric_complete_actual_visual_review_pending':raise RuntimeError('Next group runtime failure; no retries: '+str(end))
    status('next_group_numeric_complete_review_pending',processes=processes)
except BaseException as exc:
    status('stopped_requires_inspection',error=str(exc));raise
