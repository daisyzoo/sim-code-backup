"""Two assignments, two tasks each; one curved-X path intervention."""
import os,json,subprocess,hashlib,shutil
from pathlib import Path
root=Path(__file__).resolve().parent
assert json.loads((root/'object_feedback_pair_r1/STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
out=root/'reach_sweep_pair_r1';out.mkdir(exist_ok=False)
parent=json.loads((root/'object_feedback_pair_r1/PROTOCOL.json').read_text());settings=parent['common_settings']+['--expert-far-sweep-retreat-m','.08']
paths=[*parent['source_sha256'],str(root.parents[1]/'simfoundry/data/reach_sweep.py')];hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
(out/'PROTOCOL.json').write_text(json.dumps(dict(source_sha256=hashes,settings=settings,baseline_62004=str(root/'contact_x_ablation_r1/uncapped'),baseline_62005=str(root/'object_feedback_pair_r1/baseline_62005'),frames=160,layout_ids=[62004,62005],hypothesis='Uncapped timed sweep loses low-height reach late. Smoothly retreat contact X by at most .08m after goal-side Y=.08, floor X=.50, preserving near-target path. Compare complete depth_a group. Offline IK evidence in TERMINAL_REACH_AUDIT; physical success not assumed.',training_ready=False),indent=2))
def status(stage,**kw):(out/'STATUS.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),training_ready=False,**kw),indent=2))
env=os.environ.copy();env['PATH']='/home/user/miniconda3/envs/env_isaaclab/bin:'+env['PATH'];env['CONDA_PREFIX']='/home/user/miniconda3/envs/env_isaaclab';env['OMNI_KIT_ACCEPT_EULA']='yes';env.setdefault('DISPLAY',':1')
try:
 for lid in [62004,62005]:
  if shutil.disk_usage(out).free<30*2**30:raise RuntimeError('Insufficient disk reserve')
  for p,sha in hashes.items():
   if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=sha:raise RuntimeError('Frozen source changed')
  status('running',layout_id=lid);dest=out/f'case_{lid}'
  cmd=['./isaaclab.sh','-p',str(root.parents[1]/'scripts/collect_paired_sorting.py'),*settings,'--layout-start',str(lid),'--diagnostic-layout-json',str(root/f'development_layouts/{lid}.json'),'--out-dir',str(dest)]
  with (out/f'case_{lid}.log').open('w') as log:r=subprocess.run(cmd,cwd=root.parents[2]/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
  for task in ['push_box_to_bin','nudge_mailer_to_bin']:
   quality=json.loads((dest/f'layout_{lid}_{task}/quality.json').read_text());assert quality['frames']==160 and not quality['training_ready']
  for script in ['audit_contacts.py','review_diagnostics.py']:subprocess.run(['/home/user/miniconda3/envs/env_isaaclab/bin/python',str(root/script),str(dest)],check=True)
 status('numeric_complete_actual_visual_review_pending')
except BaseException as exc:status('runtime_failed',error=str(exc));raise
