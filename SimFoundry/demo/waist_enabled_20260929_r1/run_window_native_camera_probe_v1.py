"""One quarantined 150-frame-per-task camera crash probe, not a task acceptance run.
Uses the failed case's unmodified collector and exact arguments except output and
steps. Both tasks run, no repeated attempts. The reduced environment timeout is
recorded as a limitation; absence of a crash cannot prove a fix or determinism.
Full experiment still requires 1200/70 frames, all ten conditions and >30GiB launch.
"""
from pathlib import Path
import os,json,hashlib,datetime,subprocess,shutil
W=Path(__file__).resolve().parent; ROOT=W.parents[1]; R=W/'front_contact_window_physical_r1'; D=W/'window_native_camera_probe_r1'; sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
assert not D.exists()
assert json.loads((R/'STATUS.json').read_text())['status']=='runtime_or_audit_failed'
assert not Path('/proc/605996').exists() and not Path('/proc/613652').exists()
plan=json.loads((W/'front_contact_window_physical_preparation_r1/PLAN.json').read_text()); item=next(c for c in plan['commands'] if c['layout_id']==840023)
frozen=json.loads((R/'PROTOCOL.json').read_text())['frozen_files_sha256']
for p,h in frozen.items():assert sha(p)==h,p
assert not subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],check=True,capture_output=True,text=True).stdout.strip()
free=shutil.disk_usage(W).free/2**30; assert free>26.,('short diagnostic requires 25GiB reserve plus full one-case 1GiB budget',free)
args=list(item['args']); original=list(args);args[args.index('--out-dir')+1]=str(D/'case_840023');args[args.index('--steps')+1]='150'
assert [i for i,(a,b) in enumerate(zip(original,args)) if a!=b]==sorted([original.index('--out-dir')+1,original.index('--steps')+1])
D.mkdir(); sources={**frozen,str(Path(__file__)):sha(__file__),str(R/'NATIVE_CRASH_DIAGNOSIS_V2.json'):sha(R/'NATIVE_CRASH_DIAGNOSIS_V2.json')}
protocol=dict(created_at_utc=now(),scope=__doc__,producer_pid=os.getpid(),command=[os.sys.executable,plan['collector'],*args],changed_arguments={'--out-dir':str(D/'case_840023'),'--steps':150},original_failed_run=str(R),free_gib=free,case_budget_gib=1,protected_reserve_gib=25,full_experiment_launch_gate_gib=30,original_quality_gates_changed=False,frozen_files_sha256=sources,training_ready=False)
(D/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2))
def save(**kw):
 p=D/'STATUS.tmp';p.write_text(json.dumps(dict(updated_at_utc=now(),producer_pid=os.getpid(),training_ready=False,**kw),indent=2));p.replace(D/'STATUS.json')
env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',DISPLAY=':1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',EXP_PATH='/home/user/miniconda3/envs/env_isaaclab/lib/python3.12/site-packages/isaacsim/apps');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH']
with (D/'case_840023.log').open('x') as log:
 child=subprocess.Popen(protocol['command'],cwd=ROOT.parent,env=env,stdout=log,stderr=subprocess.STDOUT)
 save(status='diagnostic_running',collector_pid=child.pid);code=child.wait()
for p,h in sources.items():assert sha(p)==h,p
raws=list((D/'case_840023').glob('layout_*/raw.npz'))
save(status='diagnostic_terminal',collector_returncode=code,raw_episodes_saved=len(raws),native_crash_observed=('A crash has occurred' in (D/'case_840023.log').read_text()),full_experiment_complete=False)
