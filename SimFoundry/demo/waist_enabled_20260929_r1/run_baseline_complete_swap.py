"""Fresh complete development swap group, old successful configuration retest."""
import os,json,hashlib,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
out=root/'baseline_complete_swap_r1';out.mkdir(exist_ok=False)
parent=json.loads((root/'frontal_hand_guard_r1/PROTOCOL.json').read_text())
for p,sha in parent['source_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha,p
settings=list(json.loads((root/'frontal_top_load5_long_r1/PROTOCOL.json').read_text())['settings'])
settings+=['--environment-seed','0','--trace-arm-contact-forces']
hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in parent['source_sha256']}
layouts={str(i):hashlib.sha256((root/f'development_layouts/{i}.json').read_bytes()).hexdigest() for i in (62000,62001)}
(out/'PROTOCOL.json').write_text(json.dumps(dict(settings=settings,source_sha256=hashes,layout_sha256=layouts,layout_ids=[62000,62001],frames=960,motion_protocol='waist_yaw_enabled_v1',runtime_environment=dict(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'),hypothesis='Retest previously2/2 task+pose successful5N/3mm/960-frame configuration over COMPLETE lateral_a category-swap group. Explicit environment seed0/current backward-compatible code and full arm contact tracing: not exact historical bitwise reproduction or single-variable comparison. All4conditions retained even on failure. Camera unchanged, original task/pose/non-target/zero/no-assist gates unchanged. Known camera loss risk explicitly reported; no new all-frame visibility prerequisite. Diagnostic only; no historical data promotion or model success claim.',training_ready=False),indent=2))
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OMNI_KIT_ACCEPT_EULA='yes');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH'];env.setdefault('DISPLAY',':1')
def status(stage,**kw):(out/'STATUS.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),training_ready=False,**kw),indent=2))
try:
 for i in (62000,62001):
  for p,sha in hashes.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha,p
  assert hashlib.sha256((root/f'development_layouts/{i}.json').read_bytes()).hexdigest()==layouts[str(i)]
  status('running',layout_id=i)
  case=out/f'case_{i}';cmd=['./isaaclab.sh','-p',str(root.parents[1]/'scripts/collect_paired_sorting.py'),*settings,'--layout-start',str(i),'--diagnostic-layout-json',str(root/f'development_layouts/{i}.json'),'--out-dir',str(case)]
  with (out/f'case_{i}.log').open('w') as log:result=subprocess.run(cmd,cwd=root.parents[2]/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
  if result.returncode:raise RuntimeError(f'Collector {i} exit {result.returncode}')
  for script in ['audit_contacts.py','review_diagnostics.py']:
   with (out/f'{i}_{script}.log').open('w') as log:subprocess.run([env['CONDA_PREFIX']+'/bin/python',str(root/script),str(case)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 for p,sha in hashes.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha,p
 status('numeric_complete_actual_visual_review_pending')
except BaseException as exc:status('runtime_failed',error=str(exc));raise
