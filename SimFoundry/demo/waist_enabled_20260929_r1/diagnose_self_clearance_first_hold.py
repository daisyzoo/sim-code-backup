"""Reproduce first exact-reference holds and inspect local equality feasibility.
No acceptance of failed solver endpoints, no changed replay or control commands.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.optimize import linprog
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_self_clearance_exact_probe';sys.path[:0]=[str(repo),str(stage),str(w/'staged_joint_edge_command')]
from articulated_hand_geometry import ArticulatedHandGeometry
from self_clearance import BilateralElbowClearance
import pose_projection as mod
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');geom=BilateralElbowClearance(model,stage/'elbow_torso_hulls.json');lo=np.array(U1_JOINT_LIMIT_LO)[12:23];hi=np.array(U1_JOINT_LIMIT_HI)[12:23];lo[0]=-.98;hi[0]=.98
name='layout_840001_nudge_mailer_to_bin';episode=w/'joint_edge_retry_groups_r1/case_840001'/name;replay=stage/'kinematic_replay_r1';r=json.loads((replay/(name+'.json')).read_text());selected=[x['step'] for x in r['records'] if x['reason']=='hold_verified_previous'][:3]
with np.load(episode/'raw.npz') as z:parents=z['action'][:,12:23].astype(np.float32)
with np.load(replay/(name+'_commands.npz')) as z:commands=z['command']
frames={f['step']:f for f in json.loads((episode/'frontal_bypass.json').read_text())['rows']};original=mod.minimize;records=[]
for t in selected:
 record=dict(step=t)
 def inspect_minimize(fun,x0,**kwargs):
  eq,ineq=kwargs['constraints'];Aeq=eq['jac'](x0);beq=-eq['fun'](x0);Aub=-ineq['jac'](x0);bub=ineq['fun'](x0);bounds=kwargs['bounds'];lp=linprog(np.zeros(11),A_ub=Aub,b_ub=bub,A_eq=Aeq,b_eq=beq,bounds=list(zip(bounds.lb-x0,bounds.ub-x0)),method='highs');record['local_linear_feasible']=bool(lp.success);record['local_linear_status']=int(lp.status)
  if lp.success:
   initial=x0+lp.x;record['linear_initializer_true_eq_residual_m']=float(np.max(abs(eq['fun'](initial))));record['linear_initializer_true_min_gap_residual_m']=float(np.min(ineq['fun'](initial)))
  result=original(fun,x0,**kwargs);record.update(solver_success=bool(result.success),status=int(result.status),endpoint_max_reference_residual_m=float(np.max(abs(eq['fun'](result.x)))),endpoint_min_gap_residual_m=float(np.min(ineq['fun'](result.x))),endpoint_bound_violation_rad=float(max(np.max(bounds.lb-result.x),np.max(result.x-bounds.ub),0.)),left_previous_branch=geom.evaluate(x0,'left')['branch'],left_endpoint_branch=geom.evaluate(result.x,'left')['branch'],endpoint_command=result.x.tolist())
  if lp.success:
   retry=original(fun,initial,**kwargs);record['diagnostic_linear_initializer_solve']=dict(success=bool(retry.success),status=int(retry.status),max_reference_residual_m=float(np.max(abs(eq['fun'](retry.x)))),min_gap_residual_m=float(np.min(ineq['fun'](retry.x))),command=retry.x.tolist())
  return result
 mod.minimize=inspect_minimize;command,trace=mod.project(enabled=True,parent=parents[t],previous=commands[t-1],model=model,geometry=geom,lo=lo,hi=hi,side='left',offset=frames[t].get('control_offset_local') or [.2,0,.007]);assert np.array_equal(command,commands[t]);record['returned_previous_unchanged']=True;records.append(record);print(t,record,flush=True)
mod.minimize=original
out=dict(scope=__doc__,records=records,checker_sha256=sha(Path(__file__)),source_sha256={p.name:sha(p) for p in [stage/'self_clearance.py',stage/'pose_projection.py',replay/(name+'.json'),replay/(name+'_commands.npz')]},training_ready=False)
(stage/'FIRST_HOLD_DIAGNOSIS.json').write_text(json.dumps(out,indent=2))
