"""Source-bound offline screen with independent primal/KKT verification.
Every applicable loaded top_push state in both selected archived front episodes; all8 push conditions remain in the report. Finite-difference
checks independently verify the new analytic hand-up derivative. The original
support-vertex certificate explicitly includes Z equality as two signed normals,
linear attitude and exact attitude inequalities. Original certificate thresholds
are unchanged. This certificate does not replace native execution/contact
checks; old states are not candidate rollouts, and solver failures remain logged.
"""
from pathlib import Path
import json,hashlib,datetime,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from front_loaded_z_priority_clearance_probe_solver import solve,up_and_jacobian
from audit_unloaded_wrist_prior_live import HandModel
from audit_self_clearance_task_optimality import IndependentElbows
from screen_bag_vertical_priority_geometry import Geometry
from support_vertex_stationarity import certificate
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();C=W/'front_initial_physical_r1';P=W/'FRONT_LOADED_Z_PRIORITY_CLEARANCE_PROBE.json';previous=json.loads(P.read_text());sources={str(P):sha(P)};episodes=[]
for old in previous['episodes']:
 if not old['selected']:episodes.append(dict(episode=old['episode'],selected=False,applied=False));continue
 ep=next(C.glob('case_*/'+old['episode']));cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};g=Geometry(ep.parent);sources.update(g.sources)
 def archived(name):
  ps=[Path(p) for p in g.sources if p.endswith('/'+name)];assert len(ps)==1;return ps[0]
 hand=HandModel(archived('g1_23dof_rev_1_0_u1_black.urdf'),archived('g1_hand_support_vertices.json'));elbows=IndependentElbows(archived('elbow_torso_hulls.json'),archived('g1_23dof_rev_1_0_u1_black.urdf'));side='right' if 'push_box' in ep.name else 'left';pos=[3,4,5] if side=='right' else [0,1,2];rs=[]
 with np.load(ep/'raw.npz') as z:actual=z['action'][:,12:23].astype(float)
 frontal=json.loads((ep/'frontal_bypass.json').read_text())['rows'];selected_rows=[];excluded=[]
 for f in frontal:
  t=f['step'];c=cs[t];a=c.get('task_inputs');reason=None
  if f['mode']!='top_push':reason='not_top_push'
  elif f['contact_load']['observed_vertical_load_n']<.3:reason='last_observed_vertical_load_below0.3N'
  elif f.get('hand_guard_saturated'):reason='original_hand_guard_saturated'
  elif c.get('terminal_joint_hold'):reason='original_terminal_hold'
  elif a is None or c.get('contact_normal_tracking') is None:reason='no_original_task_or_normal'
  elif a['error'][pos[2]]>=0:reason='no_original_downward_task_request'
  elif any(isinstance(v,dict) and (v.get('override') is True or v.get('changed') is True) for k,v in c.items() if k not in ['task_inputs','self_clearance_task']):reason='other_actual_post_task_override'
  if reason:excluded.append(dict(step=t,reason=reason));continue
  selected_rows.append(dict(step=t,bout=f['recontacts']+1,parent_command=actual[t].tolist()))
 for count,r in enumerate(selected_rows):
  t=r['step'];c=cs[t];a=c['task_inputs'];q=np.asarray(a['current']);J=np.asarray(a['jacobian']);e=np.asarray(a['error']);D=np.asarray(a['damping'])**2;prior=np.asarray(a['preferred_step']);parent=np.asarray(r['parent_command']).astype(np.float32).astype(float);target=np.array(c['contact_normal_tracking']['target_local_up']);target/=np.linalg.norm(target)
  obs,analytic=up_and_jacobian(hand,q,side);np.testing.assert_allclose(obs,hand.fk(q,side)[:3,:3][2],atol=1e-12,rtol=0);np.testing.assert_allclose(obs,c['contact_normal_tracking']['current_local_up'],atol=2e-6,rtol=0)
  h=2e-7;fd=np.stack([(hand.fk(q+np.eye(11)[j]*h,side)[:3,:3][2]-hand.fk(q-np.eye(11)[j]*h,side)[:3,:3][2])/(2*h) for j in range(11)],axis=1);derr=float(np.max(abs(fd-analytic)));assert derr<1e-7,derr
  if count%50==0:print(json.dumps(dict(episode=ep.name,completed=count,total=len(selected_rows))),flush=True)
  x,m=solve(a,parent=parent,side=side,target_up=target,hand=hand,elbows=elbows);delta=x-q;A=J[6:];v=e[6:];res=A@delta-v;pn=float(np.linalg.norm(A@(parent-q)-v));rn=float(np.linalg.norm(res));up=hand.fk(x,side)[:3,:3][2];pu=hand.fk(parent,side)[:3,:3][2];pe=float(np.linalg.norm(pu-target));ce=float(np.linalg.norm(up-target));ze=float(J[pos[2]]@delta-e[pos[2]])
  # Independent central differences of the exact residual norm, not the solver's derivative.
  def angle_res(z):return float(np.linalg.norm(hand.fk(z,side)[:3,:3][2]-target))
  Gexact=np.array([-(angle_res(x+np.eye(11)[j]*h)-angle_res(x-np.eye(11)[j]*h))/(2*h) for j in range(11)])
  extra=np.array([ze,-ze,pn-rn,pe-ce]);G=np.vstack([J[pos[2]],-J[pos[2]],-res@A/max(rn,1e-15),Gexact]);lo=np.maximum.reduce([a['lower'],q-a['step_limits'],np.array(a['previous'])-.055]);hi=np.minimum.reduce([a['upper'],q+a['step_limits'],np.array(a['previous'])+.055]);gradient=J.T@(J@delta-e)+D*(delta-prior);cert=certificate(geometry=elbows,x=x,gradient=gradient,lower=lo,upper=hi,extra_values=extra,extra_jacobian=G)
  poses=g.fk(x);gaps=g.elbow_gaps(poses);np.testing.assert_allclose(gaps,elbows.gap(x),atol=1e-12,rtol=0);margins=g.table_margins(poses);req=e[pos[:2]];axis=req/(np.linalg.norm(req) or 1.)
  independent_pass=bool(cert['passed'] and min(margins)>=0 and abs(ze)<=2e-7 and ce<=pe+1e-6 and rn<=pn+2e-7)
  rs.append(dict(step=t,bout=r['bout'],**m,analytic_derivative_max_error=derr,certificate=cert,nominal_table_margins_m=margins,nominal_elbow_gaps_m=gaps,requested_z_mm=float(e[pos[2]]*1000),candidate_linear_z_mm=float(J[pos[2]]@delta*1000),parent_linear_z_mm=float(J[pos[2]]@(parent-q)*1000),parent_linear_attitude_residual_mm=pn*1000,candidate_linear_attitude_residual_mm=rn*1000,parent_exact_attitude_chord=pe,candidate_exact_attitude_chord=ce,candidate_xy_along_request_mm=float((J[pos[:2]]@delta)@axis*1000),independent_nominal_primal_and_kkt_passed=independent_pass))
 episodes.append(dict(episode=ep.name,selected=True,original_episode_frames=1200,original_controller_rows=len(frontal),eligible_loaded_rows=len(selected_rows),excluded=excluded,samples=len(rs),solver_success=sum(r['solver_success'] for r in rs),independent_nominal_primal_and_kkt_passed=sum(r['independent_nominal_primal_and_kkt_passed'] for r in rs),solver_failed_but_independent_certificate_passed=sum(not r['solver_success'] and r['independent_nominal_primal_and_kkt_passed'] for r in rs),rows=rs));sources.update({str(ep/n):sha(ep/n) for n in ['coordination.json','frontal_bypass.json','raw.npz','FRONT_LOADED_TRACKING_RESIDUAL_V2_DIAGNOSTIC.json']})
for n in ['front_loaded_z_priority_clearance_probe_solver.py','probe_front_loaded_z_priority_clearance_full.py','audit_unloaded_wrist_prior_live.py','audit_self_clearance_task_optimality.py','screen_bag_vertical_priority_geometry.py','support_vertex_stationarity.py']:sources[str(W/n)]=sha(W/n)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=episodes,source_sha256=sources,independent_nominal_certificate_only=True,physical_success_proven=False,swept_non_target_clearance_verified=False,controller_integrated=False,training_ready=False)
p=W/'FRONT_LOADED_Z_PRIORITY_CLEARANCE_FULL_OBSERVATIONS_PROBE.json'
with p.open('x') as f:json.dump(out,f,indent=2)
for e in episodes:print(json.dumps({k:v for k,v in e.items() if k not in ['rows','excluded']}),flush=True)
