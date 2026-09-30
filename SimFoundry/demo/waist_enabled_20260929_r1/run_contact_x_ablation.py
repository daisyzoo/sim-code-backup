"""Queue a matched contact-X comparison after the frozen development batch."""
import os,json,subprocess,time,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
out=root/'contact_x_ablation_r1';out.mkdir(exist_ok=False)
protocol=json.loads((root/'development32_r1/PROTOCOL.json').read_text())
(out/'PROTOCOL.json').write_text(json.dumps(dict(parent='development32_r1',layout_id=62004,variants={'capped':.50,'uncapped':0.},frames=160,source_sha256=protocol['source_sha256'],hypothesis='The .50m contact target cap may prevent sustained contact with the .60m object. Compare same initial layout, tasks, physics, full force observer and all other expert settings.',training_ready=False),indent=2))
def status(stage,**kw):
 (out/'STATUS.json').write_text(json.dumps(dict(stage=stage,training_ready=False,**kw),indent=2))
status('waiting_for_development_batch')
try:
 for _ in range(720):
  parent=json.loads((root/'development32_r1/STATUS.json').read_text())
  if parent['stage']=='runtime_failed':raise RuntimeError('Parent batch failed; do not restart')
  if parent['stage']=='numeric_pose_complete_actual_visual_review_pending':break
  # Validate the exact live process, not merely a status file.
  command=Path('/proc/344981/cmdline').read_bytes().replace(b'\0',b' ')
  if b'run_waist_development_feasibility.py' not in command:raise RuntimeError('Expected parent process missing/mismatched')
  time.sleep(5)
 else:raise TimeoutError('Parent batch exceeded one-hour dependency wait')
 env=os.environ.copy();env['PATH']='/home/user/miniconda3/envs/env_isaaclab/bin:'+env['PATH'];env['CONDA_PREFIX']='/home/user/miniconda3/envs/env_isaaclab';env['OMNI_KIT_ACCEPT_EULA']='yes';env.setdefault('DISPLAY',':1')
 for name,cap in [('capped','.50'),('uncapped','0')]:
  for path,sha in protocol['source_sha256'].items():
   if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=sha:raise RuntimeError('Frozen source changed before comparison')
  status('running',variant=name)
  settings=list(protocol['settings']);settings[settings.index('--expert-max-contact-x')+1]=cap
  cmd=['./isaaclab.sh','-p',str(root.parents[1]/'scripts/collect_paired_sorting.py'),*settings,'--layout-start','62004','--diagnostic-layout-json',str(root/'development_layouts/62004.json'),'--trace-episode-contacts','--trace-solved-contact-forces','--out-dir',str(out/name)]
  with (out/f'{name}.log').open('w') as log:r=subprocess.run(cmd,cwd=root.parents[2]/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
  for task in ['push_box_to_bin','nudge_mailer_to_bin']:
   ep=out/name/f'layout_62004_{task}'
   report=json.loads((ep/'quality.json').read_text());assert report['frames']==160 and not report['training_ready']
  subprocess.run(['/home/user/miniconda3/envs/env_isaaclab/bin/python',str(root/'audit_contacts.py'),str(out/name)],check=True)
 status('numeric_complete_actual_visual_review_pending')
except BaseException as exc:
 status('runtime_or_dependency_failed',error=str(exc));raise
