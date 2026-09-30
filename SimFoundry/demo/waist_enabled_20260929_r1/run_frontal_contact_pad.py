"""Blocked lateral geometry: physical frontal repositioning feasibility only."""
import os,json,hashlib,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
assert json.loads((root/'frontal_nearer5cm_r1/STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
out=root/'frontal_contact_pad_r1';out.mkdir(exist_ok=False)
parent=json.loads((root/'far_endpoint_pair_r1/PROTOCOL.json').read_text());settings=list(parent['settings']);settings[settings.index('--steps')+1]='320';settings+=['--expert-frontal-bypass','--expert-frontal-feedback','--expert-frontal-follow-y','--expert-frontal-tip-recontact']
settings[settings.index('--waist-limit-rad')+1]='1.0'
settings+=['--extended-waist-diagnostic','--expert-frontal-contact-pad']
preflight=json.loads((root/'waist98_probe_r1/RESULT.json').read_text());assert preflight['preflight_numeric_passed'] and preflight['actual_visual_review']!='pending'
paths=[str(root.parents[1]/'simfoundry/data/fingertip_bypass.py'),*[str(root.parents[1]/'third_party/unitree_ros/robots/g1_description/meshes'/f'{side}_wrist_roll_rubber_hand.STL') for side in ('left','right')],*parent['source_sha256'],str(root.parents[1]/'simfoundry/data/contact_load_control.py'),str(root.parents[1]/'simfoundry/data/frontal_bypass.py')];hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
(out/'PROTOCOL.json').write_text(json.dumps(dict(settings=settings,source_sha256=hashes,layout_id=62000,frames=320,hypothesis='Original62000 layout,320frames,waist1.0 as extended tip parent. Only active control vertex after rear clearance changes from max-X tip to actual STL vertex nearest measured contact patch. Sampled parent normals were all localX despite intended side push. Tests physical contact face, not just endpoint proximity. No object assistance or gate changes; camera remains original. Diagnostic only',training_ready=False),indent=2))
def status(stage,**kw):(out/'STATUS.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),training_ready=False,**kw),indent=2))
env=os.environ.copy();env['PATH']='/home/user/miniconda3/envs/env_isaaclab/bin:'+env['PATH'];env['CONDA_PREFIX']='/home/user/miniconda3/envs/env_isaaclab';env['OMNI_KIT_ACCEPT_EULA']='yes';env.setdefault('DISPLAY',':1')
try:
 for p,sha in hashes.items():
  if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=sha:raise RuntimeError('Frozen source changed')
 status('running',layout_id=62000)
 dest=out/'case_62000';cmd=['./isaaclab.sh','-p',str(root.parents[1]/'scripts/collect_paired_sorting.py'),*settings,'--layout-start','62000','--diagnostic-layout-json',str(root/'development_layouts/62000.json'),'--out-dir',str(dest)]
 with (out/'case_62000.log').open('w') as log:r=subprocess.run(cmd,cwd=root.parents[2]/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
 if r.returncode:raise RuntimeError(f'Collector exit {r.returncode}')
 for task in ['push_box_to_bin','nudge_mailer_to_bin']:
  ep=dest/f'layout_62000_{task}';q=json.loads((ep/'quality.json').read_text());assert q['frames']==320 and not q['training_ready'];assert (ep/'frontal_bypass.json').exists()
 for script in ['audit_contacts.py','review_diagnostics.py']:subprocess.run(['/home/user/miniconda3/envs/env_isaaclab/bin/python',str(root/script),str(dest)],check=True)
 status('numeric_complete_actual_visual_review_pending')
except BaseException as exc:status('runtime_failed',error=str(exc));raise
