"""Fresh three complete development groups; all failures retained, no admission."""
import os,json,hashlib,subprocess,datetime,sys
from pathlib import Path
root=Path(__file__).resolve().parent;repo=root.parents[1]
sys.path.insert(0,str(repo))
from simfoundry.data.waist_group_audit import validate_complete_swap_layouts
from simfoundry.data.waist_pilot_protocol import REQUIRED_SOURCES
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
parent=root/'normal_contact_groups_r1';old=json.loads((parent/'PROTOCOL.json').read_text())
integration=json.loads((root/'CONTACT_CENTER_INTEGRATION.json').read_text())
for row in integration['changes']:assert sha(row['path'])==row['sha256'],row['path']
settings=list(old['settings'])+['--expert-top-contact-center-calibration']
paths=set(old['source_sha256'])|{str(repo/p) for p in REQUIRED_SOURCES}
hashes={p:sha(p) for p in sorted(paths)}
ids=(62013,62012,62005,62004,62008,62009)
layouts={str(i):sha(root/f'development_layouts/{i}.json') for i in ids}
validate_complete_swap_layouts([json.loads((root/f'development_layouts/{i}.json').read_text()) for i in ids])
out=root/'contact_center_groups_r1';out.mkdir(exist_ok=False)
(out/'PROTOCOL.json').write_text(json.dumps(dict(settings=settings,source_sha256=hashes,layout_sha256=layouts,layout_ids=ids,frames=1200,parent_run=str(parent),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),runner_sha256=sha(__file__),motion_protocol='waist_yaw_enabled_v1',training_ready=False,hypothesis='Only new contact-center calibration: first three stable loaded press packets, fixed local reference, guard-first lift at current reference XY, unloaded top-center recenter. Retain normal hold, original physics/camera/quality, full12/1200frames/seed0. Not physical success or training admission.'),indent=2))
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OMNI_KIT_ACCEPT_EULA='yes');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH'];env.setdefault('DISPLAY',':1')
def status(stage,**kw):(out/'STATUS.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),training_ready=False,updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw),indent=2))
try:
 for i in ids:
  for p,h in hashes.items():assert sha(p)==h,p
  assert sha(root/f'development_layouts/{i}.json')==layouts[str(i)]
  status('running',layout_id=i)
  cmd=['./isaaclab.sh','-p',str(repo/'scripts/collect_paired_sorting.py'),*settings,'--layout-start',str(i),'--diagnostic-layout-json',str(root/f'development_layouts/{i}.json'),'--out-dir',str(out/f'case_{i}')]
  with (out/f'case_{i}.log').open('w') as log:r=subprocess.run(cmd,cwd=repo.parent/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
  if r.returncode:raise RuntimeError(f'Collector {i} exit {r.returncode}')
  for script in ('audit_contacts.py','review_diagnostics.py'):
   with (out/f'{i}_{script}.log').open('w') as log:subprocess.run([env['CONDA_PREFIX']+'/bin/python',str(root/script),str(out/f'case_{i}')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 for p,h in hashes.items():assert sha(p)==h,p
 (out/'TERMINAL_SOURCE_VERIFICATION.json').write_text(json.dumps(dict(all_frozen_sources_match=True,verified_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False)))
 status('numeric_complete_actual_visual_review_pending')
except BaseException as exc:status('runtime_failed',error=str(exc));raise
