"""Unissued joint11 feasibility probe on saved actual front-bag contexts.
No runtime integration, counterfactual rollout, training admission or gate change.
Preserves original full9 task objective; reports task/normal change explicitly.
"""
from pathlib import Path
import sys,json,datetime,hashlib
import numpy as np
from scipy.optimize import minimize,Bounds
D=Path(__file__).resolve().parent;W=D.parent;S=W/'staged_inactive_transport_v2';ROOT=W.parents[1]
sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
G=ClearanceGuard(ROOT,S);EP=W/'inactive_transport_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin'
sources={}
def read(p):
 sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_text())
records=read(EP/'inactive_transport_clearance.json')['rows'];coords={r['step']:r for r in read(EP/'coordination.json')}
with np.load(EP/'raw.npz') as z:rawq=z['q'][:,12:23];rawu=z['action'][:,12:23]
sources[str(EP/'raw.npz')]=hashlib.sha256((EP/'raw.npz').read_bytes()).hexdigest()
results=[]
for step in [372,373]:
 r=records[step]['proposal'];q,qp,prev,parent,a=[np.array(r[k],float) for k in ['current','previous_q','previous_command','parent_command','decay']]
 np.testing.assert_allclose(q,rawq[step],atol=1e-7,rtol=0);np.testing.assert_array_equal(prev,rawu[step-1]);np.testing.assert_allclose(qp,rawq[step-1],atol=1e-7,rtol=0)
 z=r['scene'];scene=RecontactScene(G,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']);task=coords[step]['task_inputs'];J=np.array(task['jacobian']);e=np.array(task['error']);dam=np.array(task['damping']);prior=np.array(task['preferred_step']);assert J.shape==(9,11)
 np.testing.assert_allclose(task['current'],q,atol=1e-7,rtol=0);np.testing.assert_allclose(task['previous'],prev,atol=1e-7,rtol=0)
 bias=q-prev-a*(qp-prev);low=np.maximum.reduce([G.lower,q-G.limits,prev-.055]);high=np.minimum.reduce([G.upper,q+G.limits,prev+.055])
 def pred(u):return (1-a)*u+a*q+bias
 def objective(u):
  d=u-q;err=J@d-e;reg=d-prior
  return float(1e6*(err@err+np.sum(dam*dam*reg*reg))),2e6*(J.T@err+dam*dam*reg)
 def margins(state,floor):
  g=scene.details(state)
  return np.r_[g['inactive_z']-floor,g['gaps']['inactive_target']-.01,g['gaps']['inactive_other']-.01,g['gaps']['active_other']-.01,G.geometry.constraints(state)-.005]
 def constraints(u):
  v=pred(u);parts=[margins(u,.8415),margins(v,.8415),v-G.lower,G.upper-v]
  for end in [u,v]:
   for alpha in [.25,.5,.75]:parts.append(margins(q+alpha*(end-q),.84))
  return np.concatenate(parts)*1000
 print(json.dumps(dict(status='solving',step=step)),flush=True)
 fit=minimize(objective,parent.copy(),jac=True,bounds=Bounds(low,high),constraints=[dict(type='ineq',fun=constraints)],method='SLSQP',options=dict(maxiter=120,ftol=1e-11))
 u=fit.x.astype(np.float32).astype(float);v=pred(u);guard=G.command(u,q,prev);vals=constraints(u)/1000;pathrows=[]
 for name,end in [('nominal',u),('predicted',v)]:
  for alpha in np.linspace(0,1,17):
   state=q+alpha*(end-q);ms=margins(state,.84);pathrows.append(dict(path=name,alpha=float(alpha),minimum_margin_m=float(ms.min()),passed=bool(ms.min()>=-2e-7)))
 active0=scene.details(parent);active1=scene.details(u);physicalq=scene.details(q);er0=J@(parent-q)-e;er1=J@(u-q)-e
 result=dict(step=step,solver_success=bool(fit.success),solver_status=int(fit.status),iterations=int(fit.nit),message=str(fit.message),rounded_constraints_passed=bool(vals.min()>=-2e-7),min_constraint_margin_m=float(vals.min()),original_command_guard=guard,all_sampled_paths_passed=all(z['passed'] for z in pathrows),sampled_paths=pathrows,original_objective_parent=objective(parent)[0],original_objective_proposal=objective(u)[0],parent_task_error=er0.tolist(),proposal_task_error=er1.tolist(),active_position_error_norm_parent=float(np.linalg.norm(er0[:3])),active_position_error_norm_proposal=float(np.linalg.norm(er1[:3])),normal_error_norm_parent=float(np.linalg.norm(er0[6:9])),normal_error_norm_proposal=float(np.linalg.norm(er1[6:9])),active_contact_local_point_change_m=(active1['point']-active0['point']).tolist(),active_world_normal_change=(active1['normal_local_up']-active0['normal_local_up']).tolist(),max_command_delta_from_parent_rad=float(abs(u-parent).max()),waist_delta_from_parent_rad=float(u[0]-parent[0]),command=u.tolist(),parent_command=parent.tolist(),current=q.tolist(),previous_command=prev.tolist(),predicted_q=v.tolist(),predicted_elbow_gaps_mm=(G.geometry.constraints(v)*1000).tolist(),predicted_inactive_height_mm=scene.details(v)['inactive_z']*1000,scene=scene.record(),independent_stationarity_certificate=False,continuous_path_certificate=False,physical_command_issued=False,training_ready=False)
 results.append(result)
 with (D/f'STEP_{step}.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps({k:v for k,v in result.items() if k in ['step','solver_success','solver_status','iterations','rounded_constraints_passed','all_sampled_paths_passed','active_position_error_norm_parent','active_position_error_norm_proposal','normal_error_norm_parent','normal_error_norm_proposal','max_command_delta_from_parent_rad','predicted_elbow_gaps_mm','predicted_inactive_height_mm']}),flush=True)
for p in [Path(__file__),S/'self_clearance.py',S/'clearance_runtime.py',S/'recontact_scene.py',S/'articulated_hand_geometry.py',S/'elbow_torso_hulls.json']:sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,results=results,source_sha256=sources,physical_command_issued=False,training_ready=False,scope_limit='Solver/finite samples are preliminary feasibility evidence only. Active contact semantics, independent optimality/path checks and fresh recursive physics remain unproven. No old future states reused as new actions results.')
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2)
