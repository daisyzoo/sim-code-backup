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
from audit_inward_command_probe import verify_refinement
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
r=w/'box_entry_lift_groups_r1';src=r/'INWARD_COMMAND_SCREEN.json';data=json.loads(src.read_text());assert data['complete'] and len(data['rows'])==189;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n,h in data['source_sha256'].items():assert sha(Path(n))==h,n
ep=r/'case_840001/layout_840001_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());fs={x['step']:x for x in fr['rows']};cs={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};core=np.array(fr['plan']['rear_cop_centering']['actual_core_size_xyz']);urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';hand=HandModel(urdf,repo/'assets/robots/g1_hand_support_vertices.json');elbows=IndependentElbows(w/'staged_box_entry_lift/elbow_torso_hulls.json',urdf)
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].copy()
with np.load(ep/'trace.npz') as z:xyz=z['box'].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z['box']).as_matrix()
lo=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;limits=np.r_[.015,np.full(10,.04)];damp=np.sqrt(np.array([np.float32(.12**2)]+[np.float32(.045**2)]*10)).astype(float);records=[];negative=[]
for row in data['rows']:
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
 try:check=dict(verify_refinement(*args,inward_step_m=row['inward_step_m']),validation_passed=True)
 except AssertionError as exc:
  assert isinstance(exc.args[0],tuple) and exc.args[0][0]=='stationarity',repr(exc)
  check=dict(refined=True,reason=tr['reason'],validation_passed=False,stationarity_residual=exc.args[0][1],nominal_forward_m=tr['nominal_forward_m']);print('KKT_REJECTED',t,row['inward_step_m'],exc.args[0][1],flush=True)
 gap=elbows.gap(cmd);assert min(gap)>=.005-2e-7
 axes=tr['threatened_axes'];normals=np.array([-np.sign(local[k])*R[t,:,k] for k in axes]);move=point(cmd)-point(q[t]);inward=normals@move;assert min(inward)>=row['inward_step_m']-1e-7 and -move[1]>=-1e-7
 records.append(dict(step=t,inward_step_m=row['inward_step_m'],min_nominal_inward_m=float(min(inward)),min_elbow_gap_m=float(min(gap)),**check))
 if t==data['rows'][0]['step']:
  broken=copy.deepcopy(tr);broken['nominal_edge_inward_m'][0]+=.0001
  try:verify_refinement(broken,*args[1:],inward_step_m=row['inward_step_m'])
  except AssertionError:negative.append(row['inward_step_m'])
  else:raise AssertionError('Accepted corrupted residual')
summary={}
for margin in [0.,.0005,.001]:
 rows=[x for x in records if x['inward_step_m']==margin];summary[str(margin)]=dict(n=len(rows),independent_passed=sum(x['validation_passed'] for x in rows),min_inward_mm=min(x['min_nominal_inward_m'] for x in rows)*1000,mean_forward_mm=float(np.mean([x['nominal_forward_m'] for x in rows])*1000),min_forward_mm=min(x['nominal_forward_m'] for x in rows)*1000,max_kkt=max(x['stationarity_residual'] for x in rows),min_elbow_gap_mm=min(x['min_elbow_gap_m'] for x in rows)*1000)
files=[Path(__file__),w/'audit_inward_command_probe.py',w/'audit_box_entry_pose_loaded_execution.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_self_clearance_task_optimality.py',src];(r/'INWARD_COMMAND_INDEPENDENT_CHECK.json').write_text(json.dumps(dict(passed=all(x['validation_passed'] for x in records),complete=True,scope=__doc__,records=records,summary=summary,negative_corruptions_rejected=len(negative),source_sha256={str(p):sha(p) for p in files},physical_validation=False,training_ready=False),indent=2));print('COMPLETE189',summary,flush=True)
