"""Fault-injection checks for hard-reference geometric projection; no simulator."""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_self_clearance_exact_probe';sys.path[:0]=[str(repo),str(stage),str(w/'staged_joint_edge_command')]
from articulated_hand_geometry import ArticulatedHandGeometry
from self_clearance import BilateralElbowClearance
import pose_projection as mod
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');geom=BilateralElbowClearance(model,stage/'elbow_torso_hulls.json');lo=np.array(U1_JOINT_LIMIT_LO)[12:23];hi=np.array(U1_JOINT_LIMIT_HI)[12:23];lo[0]=-.98;hi[0]=.98
name='layout_840001_nudge_mailer_to_bin';ep=w/'joint_edge_retry_groups_r1/case_840001'/name;replay=stage/'kinematic_replay_r1';r=json.loads((replay/(name+'.json')).read_text());t=next(x['step'] for x in r['records'] if x['reason']=='projected')
with np.load(ep/'raw.npz') as z:parent=z['action'][t,12:23].astype(np.float32)
with np.load(replay/(name+'_commands.npz')) as z:previous=z['command'][t-1].astype(np.float32)
f=next(x for x in json.loads((ep/'frontal_bypass.json').read_text())['rows'] if x['step']==t);args=dict(enabled=True,parent=parent,previous=previous,model=model,geometry=geom,lo=lo,hi=hi,side='left',offset=f.get('control_offset_local') or [.2,0,.007]);original=mod.minimize;tests=[]
for label,success,endpoint in [('failed_status',False,previous),('unsafe_parent_claimed_success',True,parent),('bounds_claimed_success',True,previous+1.),('wrong_reference_claimed_success',True,previous),('nonfinite_endpoint',True,np.full(11,np.nan))]:
 called=[]
 def fake(*a,**kw):called.append(True);return SimpleNamespace(success=success,x=endpoint.copy(),status=0 if success else 9,nit=1)
 mod.minimize=fake
 try:
  out,trace=mod.project(**args);assert called;assert np.array_equal(out,previous);assert trace['reason']=='hold_verified_previous';tests.append(dict(case=label,outcome='verified_previous_held'))
 except ValueError:
  assert label=='nonfinite_endpoint';tests.append(dict(case=label,outcome='rejected_no_command'))
mod.minimize=original
for label,changes in [('nonzero_first',dict(first=True)),('invalid_side',dict(side='wrong')),('invalid_parent_shape',dict(parent=np.zeros(10))),('nonfinite_previous',dict(previous=np.full(11,np.nan))),('unsafe_previous',dict(previous=parent))]:
 try:mod.project(**(args|changes))
 except ValueError:tests.append(dict(case=label,outcome='rejected_no_command'))
 else:raise AssertionError(label)
out=dict(tests=tests,all_pass=True,real_input_step=t,source_sha256={p.name:sha(p) for p in [stage/'self_clearance.py',stage/'pose_projection.py',ep/'raw.npz',replay/(name+'_commands.npz')]},checker_sha256=sha(Path(__file__)),training_ready=False);(stage/'FAILURE_CHECK.json').write_text(json.dumps(out,indent=2));print('passed',len(tests),'fault cases')
