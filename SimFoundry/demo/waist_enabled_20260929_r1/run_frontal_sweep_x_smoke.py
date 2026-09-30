"""Blocked lateral geometry: physical frontal repositioning feasibility only."""
import os,json,hashlib,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
assert json.loads((root/'frontal_recontact_smoke_r1/STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
out=root/'frontal_sweep_x_smoke_r1';out.mkdir(exist_ok=False)
parent=json.loads((root/'far_endpoint_pair_r1/PROTOCOL.json').read_text());settings=list(parent['settings']);settings[settings.index('--steps')+1]='320';settings+=['--expert-frontal-bypass','--expert-frontal-feedback','--expert-frontal-follow-y','--expert-frontal-recontact','--expert-frontal-sweep-x']
paths=[*parent['source_sha256'],str(root.parents[1]/'simfoundry/data/contact_load_control.py'),str(root.parents[1]/'simfoundry/data/frontal_bypass.py')];hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
(out/'PROTOCOL.json').write_text(json.dumps(dict(settings=settings,source_sha256=hashes,layout_id=62000,frames=320,hypothesis='Single change after recontact: blend sweepX from actual palm to planned flankX over30frames; do not freeze3cm tracking residual for whole sweep. Same320frames/layout/yaw limit/observer. Parent: Compound recontact route after measured rear clearance: lift at actualXY, cross to parcelX-.06/parcelY-direction*.06 atZ.92 then press towardZ.84; start sweep only on measured palm settling. No changed yaw limit, no assumption of arm clearance. Parent: Y tracking single-variable followup to feedback: follow measured parcelY during rear_push at2mm/frame instead of retaining initialY. This tests losing centering as object drifts; no deliberate diagonal lead yet. Parent: Rear endpoint feedback variant: same320frames/layout/observers; adaptive measured palm-object X offset, 2cm maximum tracking lead and3mm command change. All other frontal route parameters unchanged. Parent rationale: Blocked lateral route: approach torso-facing object face, push rearward using nominal fingertip contact offset; transition only after current oriented object envelopes have rear clearance. Then sweep from actual contact and release on measured goal. Additional inactive palm outward8cm prevents frontal approach palm overlap. Compound new planner diagnostic, not a waist-only or equal-budget model comparison. No object pose/force assistance.',training_ready=False),indent=2))
def status(stage,**kw):(out/'STATUS.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),training_ready=False,**kw),indent=2))
env=os.environ.copy();env['PATH']='/home/user/miniconda3/envs/env_isaaclab/bin:'+env['PATH'];env['CONDA_PREFIX']='/home/user/miniconda3/envs/env_isaaclab';env['OMNI_KIT_ACCEPT_EULA']='yes';env.setdefault('DISPLAY',':1')
try:
 for p,sha in hashes.items():
  if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=sha:raise RuntimeError('Frozen source changed')
 status('running',layout_id=62000)
 dest=out/'case_62000';cmd=['./isaaclab.sh','-p',str(root.parents[1]/'scripts/collect_paired_sorting.py'),*settings,'--layout-start','62000','--diagnostic-layout-json',str(root/'development_layouts/62000.json'),'--out-dir',str(dest)]
 with (out/'case_62000.log').open('w') as log:r=subprocess.run(cmd,cwd=root.parents[2]/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
 for task in ['push_box_to_bin','nudge_mailer_to_bin']:
  ep=dest/f'layout_62000_{task}';q=json.loads((ep/'quality.json').read_text());assert q['frames']==320 and not q['training_ready'];assert (ep/'frontal_bypass.json').exists()
 for script in ['audit_contacts.py','review_diagnostics.py']:subprocess.run(['/home/user/miniconda3/envs/env_isaaclab/bin/python',str(root/script),str(dest)],check=True)
 status('numeric_complete_actual_visual_review_pending')
except BaseException as exc:status('runtime_failed',error=str(exc));raise
