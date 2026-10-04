"""Independent loss-branch lifecycle reconstruction across complete front episodes.
Reconstructs pressure-entry phase, pre-loss tilt/terminal/route guards, loss count,
and actual initial/recovery adapter resets. Other native motion transitions,
route geometry, planner event validity, force/geometry truth and task success
remain obligations of the enclosing independent audits. No controller import.
"""
import math
import numpy as np
from scipy.spatial.transform import Rotation

def verify_stream(*,rows,pressure,initial,recovery,xyz,quats,loads,args,plan,intervals=None,additional=None):
 n=len(xyz);assert [r['step'] for r in rows]==list(range(1,n));by={r['step']:r for r in rows}
 assert args['expert_frontal_top_guarded_descent'] and args['expert_frontal_top_continuous_drag'] and args['expert_top_confirmed_release'] and args['terminal_release_margin']
 # These are actual frozen front-window settings. Do not silently skip any guard.
 assert args['expert_frontal_top_hand_obstacle_guard_m']==args['expert_frontal_top_edge_guard_m']==0
 assert args['expert_top_tilt_recontact_rad']==.03 and plan['front_route_selected']
 assert set(pressure).issubset(range(1,n));assert set(loads)==set(range(1,n))
 if intervals is not None:assert set(intervals)==set(range(1,n)) and additional is not None and set(additional)==set(range(1,n))
 phase=None;counter=0;recontacts=0;window=[];out=[];direction=plan['direction'];start_y=plan['initial_target_xyz'][1]
 for t in range(1,n):
  r=by[t];i=None if intervals is None else intervals[t];events=[ev for ev in [initial.get(t),recovery.get(t)] if ev and ev['kind'] in ('command','handover')];assert len(events)<=1
  event=events[0] if events else None
  native_mode=event['context']['parent_mode'] if event else r['mode'];entry_phase=phase
  if i is not None:
   assert i['action_step']==t and i['observed_phase']==entry_phase
   assert i['output_mode']==native_mode
  outer=native_mode=='front_guard_lift';p=pressure.get(t);restart=False;tilted=False;confirmed=False;loss=False;extra=False
  if entry_phase is None:assert t==1;phase='top_lift'
  if outer:
   assert p is None and r['route_stop_reason'] and not event
  else:
   assert p is not None and p['action_step']==t
   transition=r.get('direction_change_recontact',{})
   if transition:
    assert transition['previous_top_mode']==phase
    restart=bool(transition['restarted'])
    if restart:
     assert transition['stage_changed'] and phase=='top_push' and loads[t]>=.3 and not transition['terminal_precedence'] and not transition['tilt_precedence']
     phase='top_lift';counter=0;recontacts+=1
   assert p['phase_at_update']==phase,('pressure phase',t,p['phase_at_update'],phase)
   assert p['active']==(phase in ('top_press','top_push'))
   assert abs(p['observed_vertical_load_n']-loads[t])<=1e-8
   rot=Rotation.from_quat(quats[t]).as_matrix();tilt=math.acos(max(-1.,min(1.,rot[2,2])))
   assert abs(tilt-r['observed_parcel_tilt_rad'])<=1e-8
   tilted=bool(phase in ('top_press','top_push') and tilt>.03)
   point=tuple(float(v) for v in xyz[t]);window.append(point);window=window[-10:]
   ready=direction*point[1]>=max(.205,direction*start_y+.16)
   confirmed=bool(len(window)==10 and direction*(point[1]-start_y)>=.15 and all(direction*v[1]>=.20 for v in window) and math.hypot(point[0]-window[0][0],point[1]-window[0][1])<=.01 and ready)
   assert r['terminal_position_confirmed'] is confirmed
   if tilted:
    phase='top_lift';counter=0;recontacts+=1
   elif confirmed:phase='top_release'
   loss=phase=='top_push'
   if loss:
    if intervals is not None:assert type(additional[t]) is bool;extra=additional[t]
    present=loads[t]>=.2 or extra;counter=0 if present else counter+1
    if ready:phase='top_release'
    elif counter>=3:phase='top_lift';counter=0;recontacts+=1
    assert native_mode==phase,('loss result phase',t,native_mode,phase)
   elif confirmed and not tilted:assert native_mode=='top_release'
   # Independent loss audit does not certify unloaded motion transitions.
   # Their native phase is bound to original pressure and planner event streams.
   assert r['recontacts']==recontacts,('recontact count',t,r['recontacts'],recontacts)
   phase=native_mode
  if i is not None:
   assert i['final_phase']==phase,('native final phase',t)
   assert (i['evidence'] is not None)==loss,('missing/invented loss evidence',t)
   assert i['disposition']==('loss_counter_evaluated' if loss else 'original_guard_or_nonpush_no_loss_update')
  native_phase=phase
  if event:
   assert event['context']['recontacts']==recontacts
   phase='top_cross' if event['kind']=='command' else 'top_press';counter=0
   assert r['mode']==phase
  out.append(dict(step=t,observed_phase=entry_phase,pressure_phase=None if p is None else p['phase_at_update'],native_final_phase=native_phase,native_output_mode=native_mode,after_adapter_phase=phase,loss_invoked=loss,additional_contact=extra,lost_counter_after_adapter=counter,recontacts=recontacts,outer_guard=outer,route_restart=restart,tilt_guard=tilted,confirmed_release=confirmed,adapter=None if event is None else event['kind']))
 return out
