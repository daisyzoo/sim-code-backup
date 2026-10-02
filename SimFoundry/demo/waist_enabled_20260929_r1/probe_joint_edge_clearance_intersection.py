"""Offline joint edge/clearance intersection at an actually blocked final command.
Reconstruct the stopped command from the original adapter and final substep body
pose, then solve the original task objective with BOTH original edge and elbow
constraints. No simulator mutation, runtime installation, gate change or admission.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
import numpy as np
from scipy.optimize import minimize,Bounds,nnls
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];STAGE=W/'staged_closed_peak_trial';sys.path[:0]=[str(STAGE),str(ROOT),str(W)]
from clearance_runtime import ClearanceGuard
from joint_edge_inward_adapter import refine_record
from articulated_hand_geometry import skew
from audit_self_clearance_task_optimality import IndependentElbows
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(ep):
 ep=Path(ep).resolve();out=ep/'JOINT_EDGE_CLEARANCE_INTERSECTION_PROBE.json';assert not out.exists()
 sc=json.loads((ep/'self_clearance.json').read_text());failure=sc['failure'];assert failure['reason']=='final_override_not_verified';step=failure['step'];c=json.loads((ep/'coordination.json').read_text())[-1];fr=json.loads((ep/'frontal_bypass.json').read_text());f=fr['rows'][-1];assert c['step']==f['step']==step==sc['recorded_frames'];assert sc['requested_frames']==1200
 guard=ClearanceGuard(ROOT,STAGE);urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';ind=IndependentElbows(STAGE/'elbow_torso_hulls.json',urdf);hand=HandModel(urdf,ROOT/'assets/robots/g1_hand_support_vertices.json')
 tr=c['joint_edge_refinement'];q=np.array(c['upper_q']);prev=np.array(tr['previous_upper_command']);parent=np.array(tr['parent_final_upper_command']);bad=np.array(tr['final_upper_command']);core=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']);offset=np.array(f['control_offset_local']);inp=c['task_inputs'];J=np.array(inp['jacobian']);error=np.array(inp['error']);damp=np.array(inp['damping']);assert np.all(np.array(inp['preferred_step'])==0)
 with np.load(ep/'substep_contacts.npz') as z:
  rows=np.flatnonzero(z['action_step']==step-1);assert len(rows)==32;last=int(rows[-1]);pose=z['body_q'][last,0].astype(float);kind=int(z['kind'][last]);tick=int(z['substep_tick'][last])
 assert max(abs(pose[:3]-f['observed_target']))<1e-7
 R=Rotation.from_quat(pose[3:]).as_matrix();local=R.T@(np.array(f['rear_cop_centering']['cop_world'])-pose[:3]);axes=[k for k in [0,1] if core[k]/2-abs(local[k])<=.01];assert axes==tr['threatened_axes'];normals=np.array([-np.sign(local[k])*R[:,k] for k in axes]);assert c['active_side']=='right'
 def point(x):
  T,jl,jw=guard.model.fk('right',x);off=T[:3,:3]@offset;return T[:3,3]+off,jl-skew(off)@jw
 p0,_=point(q);assert max(abs(p0-f['observed_support_xyz']))<2e-6
 # Replay is evidence only if the rejected float32 command is reproduced.
 repro,rt=refine_record(enabled=True,row=f,coordinate=c,current=q,previous=prev,parent_command=parent,object_xyz=pose[:3],object_rotation=R,core_size=core,model=guard.model,side='right',analytic_retry=True,parent_seed_retry=True)
 replay_error=float(max(abs(repro-bad)));assert replay_error<1e-7,replay_error
 original=guard.command(bad,q,prev);assert not original['accepted'] and not original['checks']['nominal_margin'];assert guard.command(parent,q,prev)['accepted'];assert max(abs(ind.gap(bad)-original['gaps_m']))<1e-12
 lo=np.maximum.reduce([guard.lower,q-guard.limits,prev-.055]);hi=np.minimum.reduce([guard.upper,q+guard.limits,prev+.055])
 def edge(x):
  p,j=point(x);v=p-p0;return np.r_[normals@v-.0005,-v[1]],np.vstack([normals@j,-j[1]])
 def obj(x):
  d=x-q;v=J@d-error;return 5000*float(v@v+sum((damp*d)**2)),10000*(J.T@v+damp*damp*d)
 def cons(x):
  e,g=edge(x);return np.r_[e,guard.geometry.constraints(x)-.005],np.vstack([g,guard.geometry.jacobian(x)])
 records=[]
 for name,seed in [('rejected_edge',bad),('safe_parent',parent)]:
  fit=minimize(obj,np.clip(seed,lo,hi),jac=True,bounds=Bounds(lo,hi),constraints=[dict(type='ineq',fun=lambda x:cons(x)[0],jac=lambda x:cons(x)[1])],method='SLSQP',options=dict(maxiter=300,ftol=1e-11));x=fit.x.astype(np.float32).astype(float);edge_values,edge_jac=edge(x);gc=guard.command(x,q,prev);indgap=ind.gap(x)
  # Independently reconstructed hand pose and central finite difference KKT.
  def ipoint(y):
   T=hand.fk(y,'right');return T[:3,3]+T[:3,:3]@offset
  imove=ipoint(x)-ipoint(q);iv=np.r_[normals@imove-.0005,-imove[1]];assert max(abs(iv-edge_values))<1e-10;assert max(abs(indgap-gc['gaps_m']))<1e-12
  constraints=[];h=2e-7
  for i,v in enumerate(iv):
   if v<=1e-6:
    G=np.zeros(11)
    for j in range(11):
     dx=np.eye(11)[j]*h;pm=ipoint(x+dx)-ipoint(x-dx);G[j]=float(normals[i]@pm if i<len(normals) else -pm[1])/(2*h)
    constraints.append(G)
  for i,g in enumerate(indgap):
   if g-.005<=1e-6:constraints.append(ind.gradient(x)[i])
  for j in range(11):
   if x[j]-lo[j]<=2e-6:constraints.append(np.eye(11)[j])
   if hi[j]-x[j]<=2e-6:constraints.append(-np.eye(11)[j])
  grad=J.T@(J@(x-q)-error)+damp*damp*(x-q)
  if constraints:
   A=np.array(constraints);n=np.linalg.norm(A,axis=1);A=A[n>1e-12]/n[n>1e-12,None];res=float(nnls(A.T,grad,maxiter=1000)[1])
  else:res=float(np.linalg.norm(grad))
  records.append(dict(seed=name,solver_success=bool(fit.success),status=int(fit.status),iterations=int(fit.nit),candidate_q=x.tolist(),original_final_guard=gc,independent_elbow_gaps_m=indgap.tolist(),independent_edge_residual_m=iv.tolist(),stationarity_residual=res,passed=bool(fit.success and gc['accepted'] and min(iv)>=-1e-7 and res<=1e-6),max_change_from_rejected_rad=float(max(abs(x-bad)))))
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=ep.name,step=step,recorded_frames=sc['recorded_frames'],requested_frames=sc['requested_frames'],rejected_command_was_executed=False,substep_pose_record=dict(index=last,action_step=step-1,kind=kind,tick=tick,pose=pose.tolist()),original_replay_max_error_rad=replay_error,parent_elbow_gaps_m=ind.gap(parent).tolist(),rejected_elbow_gaps_m=ind.gap(bad).tolist(),original_guard=original,records=records,source_sha256={str(p):sha(p) for p in [Path(__file__),ep/'self_clearance.json',ep/'coordination.json',ep/'frontal_bypass.json',ep/'substep_contacts.npz',STAGE/'joint_edge_inward_adapter.py',STAGE/'joint_edge_inward_command.py',STAGE/'clearance_runtime.py',STAGE/'self_clearance.py',STAGE/'articulated_hand_geometry.py',STAGE/'elbow_torso_hulls.json',W/'audit_self_clearance_task_optimality.py',W/'audit_unloaded_wrist_prior_live.py',*map(Path,guard.model.source_sha256)]},runtime_changed=False,training_ready=False)
 with out.open('x') as stream:json.dump(report,stream,indent=2)
 print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','scope']},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('episode');main(p.parse_args().episode)
