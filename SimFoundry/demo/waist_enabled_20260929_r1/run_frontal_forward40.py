"""Blocked lateral geometry: physical frontal repositioning feasibility only."""
import os,json,hashlib,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
assert json.loads((root/'frontal_cross_admittance_r1/STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
out=root/'frontal_forward40_r1';out.mkdir(exist_ok=False)
parent=json.loads((root/'far_endpoint_pair_r1/PROTOCOL.json').read_text());settings=list(parent['settings']);settings[settings.index('--steps')+1]='960';settings+=['--expert-frontal-bypass','--expert-frontal-feedback','--expert-frontal-follow-y','--expert-frontal-top-recontact','--expert-frontal-top-guarded-descent','--expert-frontal-top-continuous-drag','--expert-frontal-top-drag-step-m','.003','--expert-frontal-top-load-n','5.','--expert-frontal-top-visible-corner','--expert-frontal-top-approach-compensation','--expert-frontal-top-collision-core','--expert-frontal-top-support-hysteresis-m','.0001','--expert-frontal-top-forward-margin-m','.04','--expert-frontal-top-edge-guard-m','.012','--expert-frontal-top-recovery-clearance-m','.05','--trace-arm-contact-forces','--expert-frontal-top-hold-push-x','--expert-frontal-top-cross-admittance']
settings[settings.index('--waist-limit-rad')+1]='1.0'
settings+=['--extended-waist-diagnostic','--trace-control-jacobian-every','20','--trace-hand-contact-forces','--expert-frontal-press-z','.822']
preflight=json.loads((root/'waist98_probe_r1/RESULT.json').read_text());assert preflight['preflight_numeric_passed'] and preflight['actual_visual_review']!='pending'
paths=[str(root.parents[1]/'simfoundry/data/cross_axis_admittance.py'),str(root.parents[1]/'simfoundry/data/top_contact_load_geometry.py'),str(root.parents[1]/'simfoundry/data/top_push_contact_geometry.py'),str(root.parents[1]/'simfoundry/data/support_vertex_hysteresis.py'),str(root.parents[1]/'simfoundry/data/parcel_collision_geometry.py'),str(root.parents[1]/'simfoundry/scene_bridge/isaac_cfg.py'),str(root.parents[1]/'scenes/sorting_station_g1_23/twin/layout.json'),str(root.parents[1]/'simfoundry/data/top_contact_visibility.py'),str(root.parents[1]/'simfoundry/data/bounded_ik.py'),str(root.parents[1]/'simfoundry/data/waist_coordination.py'),str(root.parents[1]/'simfoundry/data/top_contact_bypass.py'),str(root.parents[1]/'assets/robots/g1_hand_support_vertices.json'),str(root.parents[1]/'assets/robots/g1_23dof_u1_rubber/g1_23dof_rev_1_0_u1_black/payloads/hand_collision.usda'),str(root.parents[1]/'simfoundry/data/solved_contact_trace.py'),str(root.parents[1]/'simfoundry/data/fingertip_bypass.py'),*[str(root.parents[1]/'third_party/unitree_ros/robots/g1_description/meshes'/f'{side}_wrist_roll_rubber_hand.STL') for side in ('left','right')],*parent['source_sha256'],str(root.parents[1]/'simfoundry/data/contact_load_control.py'),str(root.parents[1]/'simfoundry/data/frontal_bypass.py')];hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
(out/'PROTOCOL.json').write_text(json.dumps(dict(settings=settings,source_sha256=hashes,layout_id=62000,frames=960,hypothesis='Same bounded cross-admittance960/5N/3mm; only initial forward contact margin25mm to40mm. Both prior episodes stable/zero whole-bbox-outside but0/2; bag progress regressed and10 repeated edge recoveries. Independent static endpoints at current actual first/middle/late poses with unchanged camera >=50percent projected coverage checked40mm endpoints before launch. Static feasibility is not dynamic/collision guarantee. Keep edgeguard12mm, physics, camera, original gates and all other controls unchanged',training_ready=False),indent=2))
def status(stage,**kw):(out/'STATUS.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),training_ready=False,**kw),indent=2))
env=os.environ.copy();env['PATH']='/home/user/miniconda3/envs/env_isaaclab/bin:'+env['PATH'];env['CONDA_PREFIX']='/home/user/miniconda3/envs/env_isaaclab';env['OMNI_KIT_ACCEPT_EULA']='yes';env.setdefault('DISPLAY',':1')
try:
 for p,sha in hashes.items():
  if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=sha:raise RuntimeError('Frozen source changed')
 status('running',layout_id=62000)
 dest=out/'case_62000';cmd=['./isaaclab.sh','-p',str(root.parents[1]/'scripts/collect_paired_sorting.py'),*settings,'--layout-start','62000','--diagnostic-layout-json',str(root/'development_layouts/62000.json'),'--out-dir',str(dest)]
 with (out/'case_62000.log').open('w') as log:r=subprocess.run(cmd,cwd=root.parents[2]/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
 if r.returncode:raise RuntimeError(f'Collector exit {r.returncode}')
 for task in ['push_box_to_bin','nudge_mailer_to_bin']:
  ep=dest/f'layout_62000_{task}';q=json.loads((ep/'quality.json').read_text());assert q['frames']==960 and not q['training_ready'];assert (ep/'frontal_bypass.json').exists()
 for script in ['audit_contacts.py','review_diagnostics.py']:subprocess.run(['/home/user/miniconda3/envs/env_isaaclab/bin/python',str(root/script),str(dest)],check=True)
 status('numeric_complete_actual_visual_review_pending')
except BaseException as exc:status('runtime_failed',error=str(exc));raise
