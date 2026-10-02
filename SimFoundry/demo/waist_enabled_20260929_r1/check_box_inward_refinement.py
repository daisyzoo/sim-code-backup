"""Independent URDF finite-difference Jacobian, primal and original1e-6 KKT checks.
No candidate optimizer is imported. Applies only to recorded-input offline probes.
"""
from pathlib import Path
import sys,json,hashlib,copy
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_unloaded_wrist_prior_live import HandModel
from audit_self_clearance_task_optimality import IndependentElbows
from audit_box_inward_refinement import verify_refinement,normalized_trace,verify_plan
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
r=w/'box_entry_lift_groups_r1';src=r/'INWARD_COMMAND_SCREEN.json';data=json.loads(src.read_text());assert data['complete'] and len(data['rows'])==189;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n,h in data['source_sha256'].items():assert sha(Path(n))==h,n
ep=r/'case_840001/layout_840001_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());fs={x['step']:x for x in fr['rows']};cs={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};core=np.array(fr['plan']['rear_cop_centering']['actual_core_size_xyz']);urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';hand=HandModel(urdf,repo/'assets/robots/g1_hand_support_vertices.json');elbows=IndependentElbows(w/'staged_box_entry_lift/elbow_torso_hulls.json',urdf)
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].copy()
with np.load(ep/'trace.npz') as z:xyz=z['box'].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z['box']).as_matrix()
lo=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;limits=np.r_[.015,np.full(10,.04)];damp=np.sqrt(np.array([np.float32(.12**2)]+[np.float32(.045**2)]*10)).astype(float);records=[];negative=[]

for row in [x for x in data['rows'] if x['inward_step_m']==.0005]:
 t=row['step'];f=fs[t];c=cs[t];tr=row['trace'];cmd=np.array(tr['final_upper_command'],dtype=np.float32);parent=np.array(tr['parent_final_upper_command'],dtype=np.float32);offset=np.array(f['control_offset_local']);local=R[t].T@(np.array(f['rear_cop_centering']['cop_world'])-xyz[t]);J=np.vstack([np.array(c['control_jacobian_world'],dtype=np.float32),np.array(c['contact_normal_tracking']['jacobian'],dtype=np.float32)]).astype(float);errors=[]
 for side in ['left','right']:
  goal=f['target_xyz'] if side=='right' else c['inactive_anchor'];errors.extend(np.clip(np.float32(.72)*(np.array(goal,dtype=np.float32)-np.array(c['control_point_positions'][side],dtype=np.float32)),np.float32(-.035),np.float32(.035)).tolist())
 E=np.r_[np.array(errors,dtype=np.float32),np.array(c['contact_normal_tracking']['error'],dtype=np.float32)].astype(float)
 def point(v):
  T=hand.fk(v,'right');return T[:3,3]+T[:3,:3]@offset
 def pj(v):
  cols=[]
  for j in range(11):
   delta=np.zeros(11);delta[j]=1e-6;cols.append((point(v+delta)-point(v-delta))/(2e-6))
  return point(v),np.array(cols).T
 args=(tr,parent,cmd,u[t-1],q[t],J,E,damp,lo,hi,limits,pj,R[t],local,core,-1,[3,4,5])
 tr=copy.deepcopy(tr)
 tr.update(nominal_inward_requirement_m=.0005,physical_motion_prediction=False)
 for actual,residual in [('parent_nominal_edge_inward_m','parent_edge_constraint_residual_m'),('nominal_edge_inward_m','edge_constraint_residual_m')]:
  if actual in tr:tr[residual]=tr[actual];tr[actual]=[x+.0005 for x in tr[actual]]
 args=(tr,*args[1:]);check=verify_refinement(*args,inward_enabled=True);records.append(dict(step=t,**check))
 if t==303:
  corruptions={
   'wrong_requirement':lambda d:d.update(nominal_inward_requirement_m=.001),
   'missing_requirement':lambda d:d.pop('nominal_inward_requirement_m'),
   'false_dynamics_claim':lambda d:d.update(physical_motion_prediction=True),
   'missing_residual':lambda d:d.pop('edge_constraint_residual_m'),
   'changed_actual':lambda d:d['nominal_edge_inward_m'].__setitem__(0,d['nominal_edge_inward_m'][0]+.0001),
   'changed_residual':lambda d:d['edge_constraint_residual_m'].__setitem__(0,d['edge_constraint_residual_m'][0]+.0001),
   'nonfinite_actual':lambda d:d['nominal_edge_inward_m'].__setitem__(0,float('nan')),
   'changed_command':lambda d:d['final_upper_command'].__setitem__(0,d['final_upper_command'][0]+.001),
   'fake_guarded':lambda d:d.update(override=False,reason='original_mode_guard'),
  }
  for name,mutate in corruptions.items():
   bad=copy.deepcopy(tr);mutate(bad)
   try:verify_refinement(bad,*args[1:],inward_enabled=True)
   except AssertionError:negative.append(name)
   else:raise AssertionError(('corruption admitted',name))
  try:normalized_trace(tr,False)
  except AssertionError:negative.append('metadata_on_left')
  else:raise AssertionError('wrong side admitted')
  local_center=np.zeros(3);idle=dict(override=False,reason='no_threatened_core_edge',nominal_inward_requirement_m=.0005,physical_motion_prediction=False,parent_final_upper_command=parent.tolist(),final_upper_command=parent.tolist(),previous_upper_command=u[t-1].tolist())
  verify_refinement(idle,parent,parent,u[t-1],q[t],J,E,damp,lo,hi,limits,pj,R[t],local_center,core,-1,[3,4,5],inward_enabled=True)
  ordinary=copy.deepcopy(idle);ordinary.pop('nominal_inward_requirement_m');ordinary.pop('physical_motion_prediction')
  verify_refinement(ordinary,parent,parent,u[t-1],q[t],J,E,damp,lo,hi,limits,pj,R[t],local_center,core,1,[0,1,2],inward_enabled=False)
assert len(records)==63 and len(negative)==10
expected=dict(enabled=True,side='right',nominal_inward_requirement_m=.0005,existing_joint_xy_eligibility=True,original_task_objective=True,original_bounds_and_guards=True,physical_motion_prediction=False,training_ready=False)
pa=dict(rear_box_inward_correction=True);pm=dict(rear_box_inward_correction=True);plan=dict(rear_joint_edge_command=dict(enabled=True),direction=-1,rear_box_inward_correction=expected)
assert verify_plan(pa,plan,pm)
plan['direction']=1;plan.pop('rear_box_inward_correction');assert not verify_plan(pa,plan,pm)
plan['rear_box_inward_correction']=expected
try:verify_plan(pa,plan,pm)
except AssertionError:negative.append('plan_on_left')
else:raise AssertionError('left plan admitted')
files=[Path(__file__),w/'audit_box_inward_refinement.py',w/'audit_inward_command_probe.py',w/'audit_box_entry_pose_loaded_execution.py',w/'audit_unloaded_wrist_prior_live.py',src]
out=dict(passed=True,scope='Independent native trace metadata, original1e-6 KKT and same63 real inputs; not physical trajectories.',records=records,negative_corruptions_rejected=negative,no_edge_guard_cases=2,source_sha256={str(p):sha(p) for p in files},physical_validation=False,training_ready=False)
(w/'staged_box_inward_correction/REFINEMENT_AUDIT_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS63 independent,11corruptions,2 noedge')
