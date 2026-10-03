"""Independently reconstruct a loaded original command before Z refinement.
Caller supplies measured current state and previous ACTUALLY emitted command.
This row interface never rewrites an episode action history. It checks original
9-row task inputs, original nonlinear elbow correction, then float32 slew/limits.
Source/scene/Jacobian/contact and whole-episode audits are separate requirements.
No new refinement solver or runtime module is imported.
"""
from pathlib import Path
import sys
import numpy as np
W=Path(__file__).resolve().parent
sys.path[:0]=[str(W),str(W.parents[1])]
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
from support_vertex_stationarity import certificate


def near(a,b,tol=0):
 a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float)
 assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all(), 'invalid values'
 assert np.max(abs(a-b),initial=0)<=tol, 'mismatched values'


def verify_parent(*,coordinate,row,expert,current,previous_actual,parent,side,elbows,bounded_solver):
 c=coordinate;t=c['step'];assert type(t) is int and t>0 and row['step']==expert['step']==t
 q=np.asarray(current,dtype=float);previous=np.asarray(previous_actual,dtype=float);parent=np.asarray(parent,dtype=float)
 for value in [q,previous,parent]:
  assert value.shape==(11,) and np.isfinite(value).all()
  near(value,value.astype(np.float32))
 assert side in ['left','right']
 if 'active_side' in c:assert c['active_side']==side
 assert row['mode']==expert['mode']=='top_push'
 assert not c.get('region_joint_override') and not c.get('terminal_joint_hold')
 assert c['bounded_solver'] is True and c['contact_bout_yaw_tracking'] is None and c['waist_preference_rad'] is None
 # New metadata describes this very refinement; it must not be confused with an
 # earlier command override. All other post-task overrides forbid this interface.
 for k,v in c.items():
  if k not in ['task_inputs','self_clearance_task','front_loaded_z_priority'] and isinstance(v,dict):
   assert v.get('override') is not True and v.get('changed') is not True, ('other override',k)
 a=c['task_inputs'];tr=c['self_clearance_task'];normal=c['contact_normal_tracking']
 if 'upper_q' in c:near(c['upper_q'],q)
 near(a['current'],q);near(a['previous'],previous)
 lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98
 limits=np.r_[.015,np.full(10,.04)];damping=np.sqrt(np.array([np.float32(.12**2)]+[np.float32(.045**2)]*10)).astype(float)
 for name,value in [('lower',lo),('upper',hi),('step_limits',limits),('damping',damping)]:near(a[name],value)
 J=np.asarray(a['jacobian'],dtype=float);E=np.asarray(a['error'],dtype=float)
 assert J.shape==(9,11) and E.shape==(9,) and np.isfinite(J).all() and np.isfinite(E).all()
 if 'control_jacobian_world' in c:near(J[:6],c['control_jacobian_world'])
 near(J[6:],np.asarray(normal['jacobian'],dtype=np.float32))
 errors=[]
 near(row['target_xyz'],expert['target_xyz'])
 for hand in ['left','right']:
  target=expert['target_xyz'] if hand==side else c['inactive_anchor']
  errors.extend(np.clip(np.float32(.72)*(np.asarray(target,dtype=np.float32)-np.asarray(c['control_point_positions'][hand],dtype=np.float32)),np.float32(-.035),np.float32(.035)).tolist())
 errors.extend(np.asarray(normal['error'],dtype=np.float32).tolist());near(E,errors)
 prior=np.zeros(11);assert c['preferred_waist_step_rad']==0;near(a['preferred_step'],prior)
 baseline=(q+bounded_solver(J,E,q,lo,hi,limits,damping,preferred_step=prior)).astype(np.float32).astype(float)
 low=np.maximum.reduce([lo,q-limits,previous-.055]);high=np.minimum.reduce([hi,q+limits,previous+.055]);assert np.all(low<high)
 baseline_valid=bool(np.all(baseline>=low-2e-7) and np.all(baseline<=high+2e-7) and min(elbows.gap(baseline))>=.005-2e-7)
 assert tr['accepted'] is True and type(tr['override']) is bool
 proof=None
 if not tr['override']:
  assert baseline_valid and tr['reason']=='original_task_solution_clear'
  task_command=baseline
 else:
  assert not baseline_valid and tr['solver_success'] is True and tr['status']==0 and 0<tr['iterations']<=150
  candidate=np.asarray(tr['candidate_command'],dtype=float);near(candidate,candidate.astype(np.float32));near(tr['parent_command'],baseline);near(tr['previous_command'],previous)
  gap=elbows.gap(candidate);near(gap,tr['candidate_gaps_m'],2e-10)
  assert min(gap)>=.005-2e-7 and np.all(candidate>=low-2e-7) and np.all(candidate<=high+2e-7)
  delta=candidate-q;near(tr['task_residual_m'],J@delta-E,1e-10)
  proof=certificate(geometry=elbows,x=candidate,gradient=J.T@(J@delta-E)+damping*damping*(delta-prior),lower=low,upper=high)
  assert proof['passed'] and proof['stationarity_residual']<=1e-6
  task_command=candidate
 # The original clearance solve returns an absolute float32 target directly.
 # Sparse Jacobian tracing must not change this reconstruction or fill in logs.
 assigned=np.asarray(task_command,dtype=np.float32).copy();assigned[0]=np.clip(assigned[0],-.98,.98)
 recorded_waist=c.get('unexecuted_parent_waist_target_rad',c['waist_target_rad'])
 near(recorded_waist,assigned[0])
 previous32=previous.astype(np.float32)
 slewed=np.clip(assigned,previous32-np.float32(.055),previous32+np.float32(.055))
 command=np.clip(slewed,np.asarray(U1_JOINT_LIMIT_LO)[12:23],np.asarray(U1_JOINT_LIMIT_HI)[12:23]).astype(np.float32)
 near(command,parent,1.2e-7)
 result=dict(step=t,max_action_error_rad=float(np.max(abs(command-parent))),reconstructed_upper_action=command.tolist())
 return dict(passed=True,step=t,parent_reconstruction=result,original_task_override=tr['override'],original_task_certificate=proof,history='measured_current_and_previous_actual_action',independent_geometry_inputs_still_required=True)
