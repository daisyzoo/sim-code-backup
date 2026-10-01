"""Static exact hand-reference feasibility in six problematic recorded command poses.
Both point references are hard equalities; active up is an objective with joint prior.
No slew/path/hand-object/full-body/dynamics guarantee. Finite starts, no infeasibility proof.
"""
from pathlib import Path
import sys,json,hashlib,time
import numpy as np
from scipy.optimize import minimize,Bounds
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_self_clearance_faces_probe';sys.path[:0]=[str(repo),str(stage),str(w/'staged_joint_edge_command')]
from articulated_hand_geometry import ArticulatedHandGeometry
from self_clearance import BilateralElbowClearance
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');geom=BilateralElbowClearance(model,stage/'elbow_torso_hulls.json');lo=np.array(U1_JOINT_LIMIT_LO)[12:23];hi=np.array(U1_JOINT_LIMIT_HI)[12:23];lo[0]=-.98;hi[0]=.98;reports=[]
for cid,task,steps in [(840001,'nudge_mailer_to_bin',[340,540,800]),(840004,'push_box_to_bin',[180,400,800])]:
 ep=w/f'joint_edge_retry_groups_r1/case_{cid}/layout_{cid}_{task}';side='right' if task=='push_box_to_bin' else 'left'
 with np.load(ep/'raw.npz') as z:parent=z['action'][:,12:23].astype(float)
 history=w/'staged_self_clearance_probe/kinematic_replay_r1'/f'{ep.name}_commands.npz'
 with np.load(history) as z:projected=z['command'].astype(float)
 frames={f['step']:f for f in json.loads((ep/'frontal_bypass.json').read_text())['rows']};row=dict(episode=ep.name,source_sha256={n:sha(ep/n) for n in ['raw.npz','frontal_bypass.json']},projected_history_sha256=sha(history),poses=[]);reports.append(row)
 for t in steps:
  p=parent[t];offsets={s:np.array(frames[t].get('control_offset_local') or [.2,0,.007]) if s==side else np.array([.2,0,.007]) for s in ['left','right']}
  def points_jac(x):
   values=[];jac=[]
   for s in ['left','right']:
    T,jl,jw=model.fk(s,x);v=T[:3,:3]@offsets[s];skew=np.array([[0.,-v[2],v[1]],[v[2],0.,-v[0]],[-v[1],v[0],0.]]);values.extend(T[:3,3]+v);jac.append(jl-skew@jw)
   return np.array(values),np.vstack(jac)
  desired=points_jac(p)[0];T,_,_=model.fk(side,p);up=T[:3,:3].T@np.array([0.,0.,1.])
  def cost(x):
   T,_,jw=model.fk(side,x);normal=T[:3,:3].T@np.array([0.,0.,1.]);err=.15*(normal-up);ez=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,0.]]);jac=.15*T[:3,:3].T@ez@jw;delta=x-p;return float(err@err+.0002*(delta@delta)),2*jac.T@err+.0004*delta
  solutions=[]
  for label,initial in [('projected',projected[t]),('original',p)]:
   initial=np.clip(initial,lo,hi);result=minimize(cost,initial,jac=True,bounds=Bounds(lo,hi),constraints=[dict(type='eq',fun=lambda x:points_jac(x)[0]-desired,jac=lambda x:points_jac(x)[1]),dict(type='ineq',fun=lambda x:geom.constraints(x)-.005,jac=geom.jacobian)],method='SLSQP',options=dict(maxiter=300,ftol=1e-11));x=result.x;errors=points_jac(x)[0]-desired;gaps=geom.constraints(x);T,_,_=model.fk(side,x);normal=T[:3,:3].T@np.array([0.,0.,1.]);valid=bool(result.success and max(abs(errors))<1e-6 and min(gaps)>.005-1e-7);solution=dict(initializer=label,success=bool(result.success),status=int(result.status),static_feasible=valid,point_error_mm=float(max(abs(errors))*1000),active_up_angle_rad=float(np.arccos(np.clip(normal@up,-1,1))),minimum_gap_mm=float(min(gaps)*1000),max_joint_deviation_rad=float(max(abs(x-p))),command=x.tolist());solutions.append(solution);print(ep.name,t,label,valid,'position mm',solution['point_error_mm'],'normalrad',solution['active_up_angle_rad'],flush=True)
  row['poses'].append(dict(step=t,solutions=solutions))
out=dict(scope=__doc__,episodes=reports,checker_sha256=sha(Path(__file__)),source_sha256={p.name:sha(p) for p in [stage/'self_clearance.py',stage/'elbow_torso_hulls.json']},training_ready=False,collector_wired=False)
(w/'SELF_CLEARANCE_EXACT_REFERENCE_SCREEN.json').write_text(json.dumps(out,indent=2))
