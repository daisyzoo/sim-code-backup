"""Fresh complete swap group with declared longer diagnostic budget."""
import os,json,hashlib,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
parent=root/'projected_clearance_hysteresis_r1'
assert json.loads((parent/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
assert json.loads((parent/'TERMINAL_SOURCE_VERIFICATION.json').read_text())['all_frozen_sources_match']
old=json.loads((parent/'PROTOCOL.json').read_text())
collector=root.parents[1]/'scripts/collect_paired_sorting.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,h in old['source_sha256'].items():assert sha(p)==h,p
settings=list(old['settings']);idx=settings.index('--steps')+1;assert settings[idx]=='960';settings[idx]='1200'
hashes=dict(old['source_sha256'])
ids=(62008,62009)
layouts={str(i):sha(root/f'development_layouts/{i}.json') for i in ids}
from sys import path
path.insert(0,str(root.parents[1]))
from simfoundry.data.waist_group_audit import validate_complete_swap_layouts
validate_complete_swap_layouts([json.loads((root/f'development_layouts/{i}.json').read_text()) for i in ids])
out=root/'projected_clearance_hysteresis_1200_r1';out.mkdir(exist_ok=False)
(out/'PROTOCOL.json').write_text(json.dumps(dict(settings=settings,source_sha256=hashes,layout_sha256=layouts,layout_ids=ids,frames=1200,parent_run=str(parent),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),runner_sha256=sha(__file__),motion_protocol='waist_yaw_enabled_v1',training_ready=False,hypothesis='Duration-only complete diagonal_a62008/62009x2tasks at1200frames vs prior960 hysteresis controller. Prior difficult box first crosses original0.20m zone at953 and has only7final zone frames vs required10; progress321.245mm, finaltop_push/lateral_y, no guard and non-target0. Retain originaltask/pose gates and controller release goal0.205. Add bounded240frames for completion/release/stability, rather than modifying pass thresholds. Frozen0.5mm hysteresis,0.86m recovery,5N/3mm/zero/noassist/physics/camera/seed0 unchanged. Same configuredseed is not identical dynamics prefix; report own959frame prefix and final separately. All outcomes retained, no training admission.'),indent=2))
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
