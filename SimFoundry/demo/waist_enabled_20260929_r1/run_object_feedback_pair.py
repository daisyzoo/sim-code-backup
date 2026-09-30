"""Matched development comparison: object-following vs timed lateral sweep."""
import os,json,subprocess,time,hashlib,shutil
from pathlib import Path
root=Path(__file__).resolve().parent
assert json.loads((root/'contact_x_ablation_r1/STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
out=root/'object_feedback_pair_r1';out.mkdir(exist_ok=False)
parent=json.loads((root/'development32_r1/PROTOCOL.json').read_text())
settings=list(parent['settings']);settings[settings.index('--expert-max-contact-x')+1]='0';settings+=['--trace-episode-contacts','--trace-solved-contact-forces']
(out/'PROTOCOL.json').write_text(json.dumps(dict(source_sha256=parent['source_sha256'],common_settings=settings,variants={'baseline':[],'feedback':['--expert-object-feedback-lead','.04']},reused_baseline_62004=str(root/'contact_x_ablation_r1/uncapped'),frames=160,layout_ids=[62004,62005],hypothesis='Uncapped far target establishes contact but timed sweep moves hand away before object reaches goal. Object-feedback Y limits outrunning the target. Fixed budget, same full category-swapped group; no release by one successful task.',training_ready=False),indent=2))
def status(stage,**kw):(out/'STATUS.json').write_text(json.dumps(dict(stage=stage,training_ready=False,pid=os.getpid(),**kw),indent=2))
env=os.environ.copy();env['PATH']='/home/user/miniconda3/envs/env_isaaclab/bin:'+env['PATH'];env['CONDA_PREFIX']='/home/user/miniconda3/envs/env_isaaclab';env['OMNI_KIT_ACCEPT_EULA']='yes';env.setdefault('DISPLAY',':1')
try:
 for name,lid in [('feedback',62004),('baseline',62005),('feedback',62005)]:
  if shutil.disk_usage(out).free<30*2**30:raise RuntimeError('Less than30GiB free')
  for path,sha in parent['source_sha256'].items():
   if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=sha:raise RuntimeError('Frozen source changed')
  status('running',variant=name,layout_id=lid)
  dest=out/f'{name}_{lid}'
  cmd=['./isaaclab.sh','-p',str(root.parents[1]/'scripts/collect_paired_sorting.py'),*settings,'--layout-start',str(lid),'--diagnostic-layout-json',str(root/f'development_layouts/{lid}.json'),'--out-dir',str(dest)]
  if name=='feedback':cmd+=['--expert-object-feedback-lead','.04']
  with (out/f'{name}_{lid}.log').open('w') as log:r=subprocess.run(cmd,cwd=root.parents[2]/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
  for task in ['push_box_to_bin','nudge_mailer_to_bin']:
   ep=dest/f'layout_{lid}_{task}';quality=json.loads((ep/'quality.json').read_text());assert quality['frames']==160 and not quality['training_ready']
  for script in ['audit_contacts.py','review_diagnostics.py']:subprocess.run(['/home/user/miniconda3/envs/env_isaaclab/bin/python',str(root/script),str(dest)],check=True)
 status('numeric_complete_actual_visual_review_pending')
except BaseException as exc:status('runtime_failed',error=str(exc));raise
