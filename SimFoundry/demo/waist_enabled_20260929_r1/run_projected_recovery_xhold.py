"""Fresh whole diagonal swap group for optional front top-contact routing."""
import os,json,hashlib,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
parent=root/'projected_clearance12_alignment10_r1'
assert json.loads((parent/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
assert json.loads((parent/'TERMINAL_SOURCE_VERIFICATION.json').read_text())['all_frozen_sources_match']
old=json.loads((parent/'PROTOCOL.json').read_text())
collector=root.parents[1]/'scripts/collect_paired_sorting.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,h in old['source_sha256'].items():
    if Path(p) not in (collector, root.parents[1]/'simfoundry/data/front_top_route.py', root.parents[1]/'simfoundry/data/top_contact_bypass.py'):assert sha(p)==h,p
assert '--expert-top-hold-established-x' in collector.read_text()
settings=old['settings']+['--expert-front-recover-clearance','--expert-top-hold-established-x','--expert-top-nearer-far-contact']
paths=list(old['source_sha256'])+[str(root.parents[1]/'simfoundry/data'/n) for n in ('front_clearance_progress.py',)]
hashes={p:sha(p) for p in paths}
ids=(62008,62009)
layouts={str(i):sha(root/f'development_layouts/{i}.json') for i in ids}
from sys import path
path.insert(0,str(root.parents[1]))
from simfoundry.data.waist_group_audit import validate_complete_swap_layouts
validate_complete_swap_layouts([json.loads((root/f'development_layouts/{i}.json').read_text()) for i in ids])
out=root/'projected_recovery_xhold_r1';out.mkdir(exist_ok=False)
(out/'PROTOCOL.json').write_text(json.dumps(dict(settings=settings,source_sha256=hashes,layout_sha256=layouts,layout_ids=ids,frames=960,parent_run=str(parent),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),runner_sha256=sha(__file__),motion_protocol='waist_yaw_enabled_v1',training_ready=False,hypothesis='Complete diagonal_a swap group. Front route restores clearance below12mm before unchanged10mm emergency stop, resumes at12.5mm; correction holds current objectY rather than originalY. Non-front projected top drag latches first established surface commandX across recontacts instead of following targetX drift. Front own objectX feedback unchanged. For initial targetX>=0.48m use20mm front-inset contact with projected reference; near objects retain center. Registered offline far bag/box candidates had lower waist demand and positive actual near-support core margin; real visibility/force success unproven. Same960/seed0/5N/3mm/center reference/10mm approach tolerance, original quality/pose/initialzero/noassist/non-target gates unchanged. Combined targeted controller changes; all failures retained, diagnostic only, no held-out geometry.'),indent=2))
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
