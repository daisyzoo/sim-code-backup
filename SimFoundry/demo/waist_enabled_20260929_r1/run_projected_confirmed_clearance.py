"""Fresh complete swap group with declared longer diagnostic budget."""
import os,json,hashlib,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
parent=root/'projected_recovery_xhold_long_r1'
assert json.loads((parent/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
assert json.loads((parent/'TERMINAL_SOURCE_VERIFICATION.json').read_text())['all_frozen_sources_match']
old=json.loads((parent/'PROTOCOL.json').read_text())
collector=root.parents[1]/'scripts/collect_paired_sorting.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,h in old['source_sha256'].items():
    if Path(p).name not in ('collect_paired_sorting.py','front_top_route.py','front_clearance_progress.py'):assert sha(p)==h,p
settings=list(old['settings']);idx=settings.index('--steps')+1;assert settings[idx]=='1440';settings[idx]='960';settings.append('--expert-front-confirm-nominal-clearance')
hashes={p:sha(p) for p in old['source_sha256']}
ids=(62008,62009)
layouts={str(i):sha(root/f'development_layouts/{i}.json') for i in ids}
from sys import path
path.insert(0,str(root.parents[1]))
from simfoundry.data.waist_group_audit import validate_complete_swap_layouts
validate_complete_swap_layouts([json.loads((root/f'development_layouts/{i}.json').read_text()) for i in ids])
out=root/'projected_confirmed_clearance_r1';out.mkdir(exist_ok=False)
(out/'PROTOCOL.json').write_text(json.dumps(dict(settings=settings,source_sha256=hashes,layout_sha256=layouts,layout_ids=ids,frames=960,parent_run=str(parent),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),runner_sha256=sha(__file__),motion_protocol='waist_yaw_enabled_v1',training_ready=False,hypothesis='Complete diagonal_a swap group back to960frames. Compare to projected_recovery_xhold_r1 at same960 budget: only optional front stage change permits3 consecutive actual gap>=nominal12mm to resume lateral motion; immediate12.5mm path preserved. No timeout exit below required clearance;10mm emergency/5mm hand/table/force/zero/noassist and all original quality gates unchanged. Long1440 evidence showed loaded gap12.459..12.490mm plateau below12.5mm, physical stall. Fixed-pose shadow is not physical proof. Same configured seed does not promise identical dynamics prefix. Retain all four outcomes, diagnostic only, no held-out geometry.'),indent=2))
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
