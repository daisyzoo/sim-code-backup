"""Fresh whole diagonal swap group for optional front top-contact routing."""
import os,json,hashlib,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
parent=root/'front_route_group_r1'
assert json.loads((parent/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
assert json.loads((parent/'TERMINAL_SOURCE_VERIFICATION.json').read_text())['all_frozen_sources_match']
old=json.loads((parent/'PROTOCOL.json').read_text())
collector=root.parents[1]/'scripts/collect_paired_sorting.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,h in old['source_sha256'].items():
    if Path(p) not in (collector, root.parents[1]/'simfoundry/data/waist_coordination.py'):assert sha(p)==h,p
assert '--expert-top-projected-support' in collector.read_text()
settings=old['settings']+['--expert-top-projected-support','--expert-frontal-top-inset-fraction','1.']
paths=list(old['source_sha256'])+[str(root.parents[1]/'simfoundry/data'/n) for n in ('projected_support_reference.py',)]
hashes={p:sha(p) for p in paths}
ids=(62008,62009)
layouts={str(i):sha(root/f'development_layouts/{i}.json') for i in ids}
from sys import path
path.insert(0,str(root.parents[1]))
from simfoundry.data.waist_group_audit import validate_complete_swap_layouts
validate_complete_swap_layouts([json.loads((root/f'development_layouts/{i}.json').read_text()) for i in ids])
out=root/'projected_support_group_r1';out.mkdir(exist_ok=False)
(out/'PROTOCOL.json').write_text(json.dumps(dict(settings=settings,source_sha256=hashes,layout_sha256=layouts,layout_ids=ids,frames=960,parent_run=str(parent),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),runner_sha256=sha(__file__),motion_protocol='waist_yaw_enabled_v1',training_ready=False,hypothesis='Continuous virtual hand-support plane reference with exact tangent-center/normal-support hybrid Jacobian and centered top target. Complete diagonal_a swap group; existing front/rear selection retained. Offline kinematic convergence is not physical success; near-box real support core-edge margin can be under2mm, inspect actual loads/tilt/slip/whole-hand interference. No mesh/material/camera/parcel assistance or quality-gate changes. Same960frames/environment seed0/5N; diagnostic only, all failures retained.'),indent=2))
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OMNI_KIT_ACCEPT_EULA='yes');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH'];env.setdefault('DISPLAY',':1')
def status(stage,**kw):(out/'STATUS.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),training_ready=False,**kw),indent=2))
try:
 for i in ids:
  for p,h in hashes.items():assert sha(p)==h,p
  assert sha(root/f'development_layouts/{i}.json')==layouts[str(i)]
  status('running',layout_id=i)
  cmd=['./isaaclab.sh','-p',str(collector),*settings,'--layout-start',str(i),'--diagnostic-layout-json',str(root/f'development_layouts/{i}.json'),'--out-dir',str(out/f'case_{i}')]
  with (out/f'case_{i}.log').open('w') as log:r=subprocess.run(cmd,cwd=root.parents[2]/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
  if r.returncode:raise RuntimeError(f'Collector {i} exit {r.returncode}')
  for script in ('audit_contacts.py','review_diagnostics.py'):
   with (out/f'{i}_{script}.log').open('w') as log:subprocess.run([env['CONDA_PREFIX']+'/bin/python',str(root/script),str(out/f'case_{i}')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 for p,h in hashes.items():assert sha(p)==h,p
 (out/'TERMINAL_SOURCE_VERIFICATION.json').write_text(json.dumps(dict(all_frozen_sources_match=True,training_ready=False)))
 status('numeric_complete_actual_visual_review_pending')
except BaseException as exc:status('runtime_failed',error=str(exc));raise
