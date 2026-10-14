"""Uninstalled finite front-bag preload waypoint transaction, default off.
A held waypoint is NOT a stationary-hand/force certificate. Caller must recompute
and independently audit the complete joint solve, final guard and real dynamics.
Parent pressure, phase guards and physical material parameters are unchanged.
"""
from copy import deepcopy
import numpy as np

class FrontBagPreload:
 def __init__(self,*,enabled=False):
  if type(enabled) is not bool:raise ValueError('Explicit boolean required')
  self.enabled=enabled;self.state=dict(generation=0,last_step=None,phase='idle',epoch=None,anchor_xy=None,held_frames=0,ready_frames=0);self.pending=None
 def propose(self,*,step,selected,side,row,previous_waypoint_xy,core_size,desired_n,min_bias_m):
  if type(step) is not int or step<1 or type(selected) is not bool or side not in ('left','right'):raise ValueError('Invalid selection/step')
  if self.state['last_step'] is not None and step!=self.state['last_step']+1:raise ValueError('Noncontinuous observation history')
  if row.get('step')!=step:raise ValueError('Stale row')
  target=np.asarray(row['target_xyz'],float)
  if target.shape!=(3,) or not np.isfinite(target).all():raise ValueError('Invalid parent target')
  nxt=deepcopy(self.state);nxt.update(generation=nxt['generation']+1,last_step=step)
  record=dict(step=step,generation=self.state['generation'],enabled=self.enabled,selected=selected,side=side,kind='pass',parent_target_xyz=target.tolist(),output_target_xyz=target.tolist(),requires_stop=False,reset_cop_on_commit=False,training_ready=False)
  def finish(reason,**extra):
   record.update(reason=reason,**extra);out=dict(record=record,next_state=nxt);self.pending=deepcopy(out);return deepcopy(out)
  def reset():nxt.update(phase='idle',epoch=None,anchor_xy=None,held_frames=0,ready_frames=0)
  if not self.enabled:reset();return finish('disabled')
  if not selected or side!='left':reset();return finish('outside_front_bag')
  if row['mode']!='top_push' or row.get('route_stop_reason') or row.get('hand_guard_saturated') or row.get('terminal_position_confirmed'):
   reset();return finish('original_phase_guard_precedence')
  if desired_n!=5. or min_bias_m!=-.006:raise ValueError('Original pressure domain required')
  epoch=row['recontacts']
  if type(epoch) is not int or epoch<0:raise ValueError('Invalid contact epoch')
  if nxt['epoch']!=epoch:reset();nxt['epoch']=epoch
  if nxt['phase']=='ready':return finish('preload_completed_for_current_contact')
  f=row.get('cop_slip_following',{});load=row['contact_load'];observed=float(load['observed_vertical_load_n']);filtered=float(load['filtered_vertical_load_n'])
  if not np.isfinite([observed,filtered]).all() or min(observed,filtered)<0:raise ValueError('Invalid observed load')
  bias=float(load['stored_z_bias_m'])
  if not np.isfinite(bias) or not -.006<=bias<=.025:raise ValueError('Original current pressure bias required')
  record.update(observed_load_n=observed,filtered_load_n=filtered,pressure_bias_m=bias,load_ready_n=.8*desired_n,ready_observations_required=3,maximum_hold_frames=24,original_z_preserved=True)
  def stop(reason):return finish(reason,kind='stop',requires_stop=True,output_target_xyz=None)
  if not f.get('override') or observed<.3:return stop('preload_current_contact_unverified')
  cop=np.asarray(f['measured_cop_local'],float);core=np.asarray(core_size,float);ref=np.asarray(row['observed_support_xyz'],float);prev=np.asarray(previous_waypoint_xy,float)
  if cop.shape!=(3,) or core.shape!=(3,) or ref.shape!=(3,) or prev.shape!=(2,) or not all(np.isfinite(x).all() for x in [cop,core,ref,prev]) or min(core)<=.02:raise ValueError('Invalid current geometry')
  if not np.array_equal(prev,np.asarray(f['previous_command_xy'],float)):raise ValueError('Parent waypoint history mismatch')
  margin=float(np.min(core[:2]/2-abs(cop[:2])));record['current_core_margin_m']=margin
  if margin<.010:return stop('preload_requires_interior_current_contact')
  if nxt['phase']=='idle':nxt.update(phase='acquiring',anchor_xy=ref[:2].tolist(),held_frames=0,ready_frames=0)
  if nxt['held_frames']>=24:return stop('preload_budget_exhausted_without_admitted_load')
  anchor=np.asarray(nxt['anchor_xy']);xy=prev+np.clip(anchor-prev,-.003,.003)
  nxt['held_frames']+=1;nxt['ready_frames']=nxt['ready_frames']+1 if observed>=.8*desired_n and filtered>=.8*desired_n else 0
  ready=nxt['ready_frames']>=3
  if ready:nxt['phase']='ready'
  output=np.r_[xy,target[2]];record.update(kind='hold',output_target_xyz=output.tolist(),anchor_xy=anchor.tolist(),anchor_slew_pending=bool(np.max(abs(xy-anchor))>1e-12),held_frames=nxt['held_frames'],ready_frames=nxt['ready_frames'],epoch=epoch,reset_cop_on_commit=ready)
  return finish('load_ready_hold_then_reset_cop' if ready else 'bounded_explicit_xy_anchor')
 def commit_after_final_guard(self,proposal,*,final_guard,actual_command,expert_state):
  """Commit bookkeeping ONLY after caller computed the new target's full solve.
  This method checks admission binding; it cannot prove that solve's mathematics.
  """
  if self.pending is None or proposal!=self.pending or proposal['record']['generation']!=self.state['generation']:raise ValueError('Missing/stale/tampered or duplicate proposal')
  r=proposal['record'];u=np.asarray(actual_command,float)
  if r['requires_stop'] or not final_guard.get('accepted') or u.shape!=(11,) or not np.isfinite(u).all() or not np.array_equal(u,u.astype(np.float32)) or not np.array_equal(u,np.asarray(final_guard.get('command'),float)):raise ValueError('Final command not admitted')
  if r['kind']=='hold':
   if expert_state.side!='left' or expert_state.top_mode!='top_push' or expert_state.recontacts!=r['epoch'] or expert_state.load.desired_n!=5. or expert_state.load.min_bias_m!=-.006:raise ValueError('Stale expert phase/pressure')
   if expert_state.load.filtered_n!=r['filtered_load_n'] or expert_state.load.bias_m!=r['pressure_bias_m']:raise ValueError('Pressure state changed after proposal')
   if not np.allclose(expert_state.command,r['parent_target_xyz'],rtol=0,atol=1e-12) or not np.allclose(expert_state.last_emitted_xy,r['parent_target_xyz'][:2],rtol=0,atol=1e-12):raise ValueError('Competing parent waypoint mutation')
   if not callable(expert_state.cop_slip.reset):raise ValueError('Missing original COP state')
  # All rejection checks precede state mutations. Pressure state is never touched.
  if r['kind']=='hold':
   expert_state.command=tuple(r['output_target_xyz']);expert_state.last_emitted_xy=tuple(r['output_target_xyz'][:2])
   if r['reset_cop_on_commit']:expert_state.cop_slip.reset()
  self.state=deepcopy(proposal['next_state']);self.pending=None
  return deepcopy(self.state)
