"""Unwired one-step feasibility screen, not a new physical rollout.
At first/middle/last loaded eligible observation of every recorded front bout,
meet the ORIGINAL active-Z task request while preventing an increase in the
linearized AND exact nominal hand-attitude task residuals. Keep the original objective, original
joint/measured-step/previous-command bounds. Independently inspect nominal
elbow/table geometry and nonlinear hand attitude after solving. No extra force,
pressure bias, threshold relaxation, integrated dynamics or training admission.
Six non-selected controls are explicitly unchanged/inapplicable, not positive
candidate trials. Samples after first intervention remain old-policy states.
"""
from pathlib import Path
import sys,hashlib,datetime,json
import numpy as np
from scipy.optimize import minimize,Bounds
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from screen_bag_vertical_priority_geometry import Geometry
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
D=W/'FRONT_LOADED_TASK_COUPLING_FULL8_DIAGNOSTIC.json';decomp=json.loads(D.read_text());C=W/'front_initial_physical_r1';episodes=[];sources={str(D):sha(D),str(Path(__file__)):sha(__file__),str(W/'screen_bag_vertical_priority_geometry.py'):sha(W/'screen_bag_vertical_priority_geometry.py')}
for entry in decomp['episodes']:
 ep=next(C.glob('case_*/'+entry['episode']));sel=json.loads((ep/'front_initial_center.json').read_text());sources[str(ep/'front_initial_center.json')]=sha(ep/'front_initial_center.json')
 if not sel['selected']:
  episodes.append(dict(episode=ep.name,selected=False,applied=False,physical_success_proven=False));continue
 for p,h in entry['source_sha256'].items():assert sha(p)==h,p
 coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};side='right' if 'push_box' in ep.name else 'left';pos=[3,4,5] if side=='right' else [0,1,2];g=Geometry(ep.parent);sources.update(g.sources);hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');records=[];chosen=[]
 for b in entry['bouts']:
  eligible=[r for r in entry['rows'] if r['bout']==b['bout'] and r['observed_previous24_load_mean_N']>=.3 and r['requested_active_xyz_mm'][2]<0]
  if eligible:chosen.extend(eligible[i] for i in sorted(set([0,len(eligible)//2,len(eligible)-1])))
 for r in chosen:
  t=r['step'];c=coords[t];a=c['task_inputs'];q=np.asarray(a['current']);prev=np.asarray(a['previous']);J=np.asarray(a['jacobian']);e=np.asarray(a['error']);dam=np.asarray(a['damping']);prior=np.asarray(a['preferred_step']);H=J.T@J+np.diag(dam*dam);d0=np.linalg.solve(H,J.T@e+dam*dam*prior);parent=q+d0
  lo=np.maximum.reduce([a['lower'],q-a['step_limits'],prev-.055])-q;hi=np.minimum.reduce([a['upper'],q+a['step_limits'],prev+.055])-q
  assert np.all(d0>=lo-2e-7) and np.all(d0<=hi+2e-7)
  A=J[6:]*1000;v=e[6:]*1000;assert len(A)==3;oldnorm=float(np.linalg.norm(A@d0-v));az=J[pos[2]]*1000;ez=e[pos[2]]*1000
  target_normal=np.asarray(c['contact_normal_tracking']['target_local_up']);target_normal/=np.linalg.norm(target_normal)
  def exact_attitude_cost(d):
   up=hand.fk(q+d,side)[:3,:3][2];return float(1e6*np.sum((up-target_normal)**2))
  old_exact=exact_attitude_cost(parent.astype(np.float32).astype(float)-q)
  def fun(d):
   err=J@d-e;reg=d-prior;return float(1e6*(err@err+np.sum(dam*dam*reg*reg))),2e6*(J.T@err+dam*dam*reg)
  result=minimize(fun,d0,jac=True,bounds=Bounds(lo,hi),constraints=[dict(type='eq',fun=lambda d:az@d-ez,jac=lambda d:az),dict(type='ineq',fun=lambda d:oldnorm**2-np.sum((A@d-v)**2),jac=lambda d:-2*A.T@(A@d-v)),dict(type='ineq',fun=lambda d:old_exact-exact_attitude_cost(d))],method='SLSQP',options=dict(maxiter=150,ftol=1e-11))
  cmd=(q+result.x).astype(np.float32).astype(float);delta=cmd-q;pred=J@delta;norm=float(np.linalg.norm(A@delta-v));errz=float(az@delta-ez)
  candidate=g.fk(cmd);parent_pose=g.fk(parent.astype(np.float32));current=g.fk(q);normal=c['contact_normal_tracking'];np.testing.assert_allclose(current[side+'_wrist_roll_rubber_hand'][:3,:3][2],normal['current_local_up'],atol=2e-6,rtol=0)
  def angle(poses):
   up=poses[side+'_wrist_roll_rubber_hand'][:3,:3][2];target=np.asarray(normal['target_local_up']);return float(np.arctan2(np.linalg.norm(np.cross(up,target)),up@target))
  pg=g.elbow_gaps(parent_pose);cg=g.elbow_gaps(candidate);pt=g.table_margins(parent_pose);ct=g.table_margins(candidate)
  boxcheck=bool(np.all(delta>=lo-2e-7) and np.all(delta<=hi+2e-7));linear=bool(result.success and boxcheck and abs(errz)<=.0002 and norm<=oldnorm+.0002)
  nonlinear=bool(min(cg)>=.005-2e-7 and min(ct)>=0 and angle(candidate)<=angle(parent_pose)+1e-6)
  parent_xy=J[pos[:2]]@d0;candidate_xy=pred[pos[:2]];request_xy=e[pos[:2]];unit=request_xy/(np.linalg.norm(request_xy) or 1.)
  records.append(dict(step=t,bout=r['bout'],solver_success=bool(result.success),solver_status=int(result.status),solver_message=str(result.message),verified_linear_feasible=linear,nominal_elbow_table_and_no_worse_attitude=nonlinear,original_requested_z_mm=ez,parent_linear_z_mm=float(az@d0),candidate_linear_z_mm=float(pred[pos[2]]*1000),candidate_z_error_mm=errz,parent_attitude_task_residual_mm=oldnorm,candidate_attitude_task_residual_mm=norm,parent_attitude_angle_rad=angle(parent_pose),candidate_attitude_angle_rad=angle(candidate),parent_elbow_gaps_m=pg,candidate_elbow_gaps_m=cg,parent_table_margins_m=pt,candidate_table_margins_m=ct,parent_xy_along_requested_mm=float(parent_xy@unit*1000),candidate_xy_along_requested_mm=float(candidate_xy@unit*1000),parent_active_xy_residual_mm=float(np.linalg.norm(parent_xy-request_xy)*1000),candidate_active_xy_residual_mm=float(np.linalg.norm(candidate_xy-request_xy)*1000),candidate_previous_slew_max_rad=float(max(abs(cmd-prev))),candidate_command=cmd.tolist(),parent_command=parent.tolist()))
 episodes.append(dict(episode=ep.name,selected=True,sampling='first/middle/last qualifying original observation per bout',sample_count=len(records),linear_feasible=sum(x['verified_linear_feasible'] for x in records),nominal_no_worse_attitude_and_geometry=sum(x['verified_linear_feasible'] and x['nominal_elbow_table_and_no_worse_attitude'] for x in records),rows=records))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=episodes,source_sha256=sources,non_target_swept_path_checked=False,nominal_optimality_independently_certified=False,physical_success_proven=False,controller_implemented=False,linear_probe_sha256=sha(W/'FRONT_LOADED_Z_ATTITUDE_PRIORITY_ONE_STEP_PROBE.json'),extra_exact_attitude_constraint=True,training_ready=False)
p=W/'FRONT_LOADED_Z_ATTITUDE_PRIORITY_NONLINEAR_ONE_STEP_PROBE.json'
with p.open('x') as f:json.dump(out,f,indent=2)
for r in episodes:print(json.dumps({k:v for k,v in r.items() if k!='rows'}))
