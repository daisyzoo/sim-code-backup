"""Direct task IK fault checks on a real safe input needing geometry correction."""
from pathlib import Path
from types import SimpleNamespace
import json,sys,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_self_clearance_task_ik_probe';sys.path[:0]=[str(repo),str(stage),str(w/'staged_joint_edge_command')]
from articulated_hand_geometry import ArticulatedHandGeometry
from self_clearance import BilateralElbowClearance
import task_ik as mod
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report=json.loads((stage/'RECORD_INPUT_CHECK.json').read_text());episode,record=next((e,r) for e in report['episodes'] for r in e['records'] if r.get('override') and r['current_minimum_gap_m']>=.005);ep=next((w/'joint_edge_retry_groups_r1').glob('case_*/'+episode['episode']));t=record['step'];c=next(r for r in json.loads((ep/'coordination.json').read_text()) if r['step']==t);expert=next(r for r in json.loads((ep/'expert_control.json').read_text()) if r['step']==t);side=c['active_side'];J=np.array(c['control_jacobian_world'],dtype=np.float32);error=[]
for hand in ['left','right']:
 target=expert['target_xyz'] if hand==side else c['inactive_anchor'];point=np.array(c['control_point_positions'][hand],dtype=np.float32);error.extend(np.clip(np.float32(.72)*(np.array(target,dtype=np.float32)-point),np.float32(-.035),np.float32(.035)))
error=np.array(error,dtype=np.float32)
if c['contact_normal_tracking'] is not None:J=np.vstack([J,np.array(c['contact_normal_tracking']['jacobian'],dtype=np.float32)]);error=np.r_[error,np.array(c['contact_normal_tracking']['error'],dtype=np.float32)]
with np.load(ep/'raw.npz') as z:previous=z['action'][t-1,12:23]
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');geometry=BilateralElbowClearance(model,stage/'elbow_torso_hulls.json');lo=np.array(U1_JOINT_LIMIT_LO)[12:23];hi=np.array(U1_JOINT_LIMIT_HI)[12:23];lo[0]=-.98;hi[0]=.98;limits=np.full(11,.04);limits[0]=.015;penalty=np.full(11,np.float32(.045**2),dtype=np.float32);penalty[0]=np.float32(.12**2);prior=np.zeros(11,dtype=np.float32);prior[0]=c['preferred_waist_step_rad'];args=dict(enabled=True,jacobian=J,error=error,current=np.array(c['upper_q'],dtype=np.float32),previous=previous,lower=lo,upper=hi,step_limits=limits,damping=np.sqrt(penalty),geometry=geometry,preferred_step=prior)
real=mod.minimize;tests=[]
for label,success,endpoint in [('failed_status',False,np.array(record['command'])),('unsafe_parent_fake_success',True,np.array(record['parent_command'])),('out_of_bounds_fake_success',True,np.ones(11)*5),('nonfinite_fake_success',True,np.full(11,np.nan))]:
 invoked=[]
 def fake(*a,**kw):invoked.append(True);return SimpleNamespace(success=success,x=endpoint.copy(),status=0 if success else 9,nit=1)
 mod.minimize=fake;command,meta=mod.solve(**args);assert invoked and command is None and meta['accepted'] is False;tests.append(dict(case=label,outcome='no_command'))
mod.minimize=real
command,meta=mod.solve(**(args|dict(previous=np.ones(11)*5)));assert command is None and meta['reason']=='empty_measured_previous_bounds';tests.append(dict(case='inconsistent_previous',outcome='no_command'))
for label,change in [('invalid_enable_type',dict(enabled='true')),('nonfinite_input',dict(current=np.full(11,np.nan))),('invalid_step_limits',dict(step_limits=np.zeros(11)))]:
 try:mod.solve(**(args|change))
 except ValueError:tests.append(dict(case=label,outcome='rejected_no_command'))
 else:raise AssertionError(label)
out=dict(all_pass=True,real_episode=episode['episode'],real_step=t,tests=tests,source_sha256={p.name:sha(p) for p in [stage/'task_ik.py',stage/'self_clearance.py',stage/'RECORD_INPUT_CHECK.json']},checker_sha256=sha(Path(__file__)),training_ready=False);(stage/'FAILURE_CHECK.json').write_text(json.dumps(out,indent=2));print('passed',len(tests),'direct task IK fault checks')
