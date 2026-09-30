"""Fresh complete swap diagnostic of0.5mm recovery hysteresis."""
import os,json,hashlib,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
parent=root/'projected_short_recontact_r1'
assert json.loads((parent/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
assert json.loads((parent/'TERMINAL_SOURCE_VERIFICATION.json').read_text())['all_frozen_sources_match']
old=json.loads((parent/'PROTOCOL.json').read_text())
collector=root.parents[1]/'scripts/collect_paired_sorting.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,h in old['source_sha256'].items():
    if Path(p).name not in ('collect_paired_sorting.py','front_top_route.py','front_clearance_progress.py'):assert sha(p)==h,p
settings=list(old['settings']);assert settings[settings.index('--steps')+1]=='960';settings.extend(['--expert-front-recovery-hysteresis-m','.0005'])
hashes={p:sha(p) for p in old['source_sha256']}
helper=root.parents[1]/'simfoundry/data/object_relative_push.py';hashes[str(helper)]=sha(helper)
integration=json.loads((root/'FRONT_CLEARANCE_HYSTERESIS_INTEGRATION.json').read_text())
for p,h in integration['source_sha256'].items():assert sha(p)==h,p
ids=(62008,62009)
layouts={str(i):sha(root/f'development_layouts/{i}.json') for i in ids}
from sys import path
path.insert(0,str(root.parents[1]))
from simfoundry.data.waist_group_audit import validate_complete_swap_layouts
validate_complete_swap_layouts([json.loads((root/f'development_layouts/{i}.json').read_text()) for i in ids])
out=root/'projected_clearance_hysteresis_r1';out.mkdir(exist_ok=False)
(out/'PROTOCOL.json').write_text(json.dumps(dict(settings=settings,source_sha256=hashes,layout_sha256=layouts,layout_ids=ids,frames=960,parent_run=str(parent),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),runner_sha256=sha(__file__),motion_protocol='waist_yaw_enabled_v1',training_ready=False,hypothesis='Complete diagonal_a62008/62009x2tasks at960frames, only0.5mm recovery hysteresis relative to prior short-recontact run. Initial and resumed lateral clearance still12mm confirmed3observations; return tofront below11.5mm, original10mm emergency/5mm hand/table unchanged. Keep0.86m recontact,0.91m initial and emergency lift,5N/3mm/zero/noassist/physics/camera/seed0 and originalquality gates. Prior box254.787mm with46recoveries; fixed recorded geometry replay predicts1recovery but is not actual dynamics/safety evidence. Retain all failures, diagnostic only.'),indent=2))
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
