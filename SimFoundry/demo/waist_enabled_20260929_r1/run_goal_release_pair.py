"""Matched viewer-instrumented goal-release development diagnostic."""
import os,json,subprocess,hashlib,shutil
from pathlib import Path
root=Path(__file__).resolve().parent
assert json.loads((root/'reach_sweep_pair_r1/STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
out=root/'goal_release_pair_r1';out.mkdir(exist_ok=False)
parent=json.loads((root/'reach_sweep_pair_r1/PROTOCOL.json').read_text());settings=parent['settings']+['--trace-viewer-every','5']
hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in parent['source_sha256']}
(out/'PROTOCOL.json').write_text(json.dumps(dict(source_sha256=hashes,common_settings=settings,variants={'baseline':[],'release':['--expert-goal-release']},cases=[['baseline',62005],['release',62004],['release',62005]],frames=160,hypothesis='Curved timed sweep presses after box crosses goal and tips it at frame108. Freeze measured palmXY and lift at measured object goal with .005m zone/.01m progress margin. Same160frames. Third-person observer identical across matched box baseline/release; images never enter policy.',training_ready=False),indent=2))
def status(stage,**kw):(out/'STATUS.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),training_ready=False,**kw),indent=2))
env=os.environ.copy();env['PATH']='/home/user/miniconda3/envs/env_isaaclab/bin:'+env['PATH'];env['CONDA_PREFIX']='/home/user/miniconda3/envs/env_isaaclab';env['OMNI_KIT_ACCEPT_EULA']='yes';env.setdefault('DISPLAY',':1')
try:
 for name,lid in [('baseline',62005),('release',62004),('release',62005)]:
  if shutil.disk_usage(out).free<30*2**30:raise RuntimeError('Insufficient disk reserve')
  for p,sha in hashes.items():
   if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=sha:raise RuntimeError('Frozen source changed')
  status('running',variant=name,layout_id=lid);dest=out/f'{name}_{lid}'
  cmd=['./isaaclab.sh','-p',str(root.parents[1]/'scripts/collect_paired_sorting.py'),*settings,'--layout-start',str(lid),'--diagnostic-layout-json',str(root/f'development_layouts/{lid}.json'),'--out-dir',str(dest)]
  if name=='release':cmd+=['--expert-goal-release']
  with (out/f'{name}_{lid}.log').open('w') as log:r=subprocess.run(cmd,cwd=root.parents[2]/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
  for task in ['push_box_to_bin','nudge_mailer_to_bin']:
   ep=dest/f'layout_{lid}_{task}';quality=json.loads((ep/'quality.json').read_text());assert quality['frames']==160 and not quality['training_ready'];viewer=json.loads((ep/'viewer_observer.json').read_text());assert len(viewer['frames'])==32
  for script in ['audit_contacts.py','review_diagnostics.py']:subprocess.run(['/home/user/miniconda3/envs/env_isaaclab/bin/python',str(root/script),str(dest)],check=True)
 status('numeric_complete_actual_visual_review_pending')
except BaseException as exc:status('runtime_failed',error=str(exc));raise
