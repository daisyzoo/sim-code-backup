"""Prepare recorded box force diagnostic using actual diagonal command direction.
Original signed force/momentum computations preserved. Adds observed command
lead/COP position and transverse torque; no changed control or causal claim.
"""
from pathlib import Path
import ast,hashlib,json
w=Path(__file__).resolve().parent;p=w/'analyze_front_box_substep_phase_balance.py';s=p.read_text()
a="direction=np.array([-1.,0.,0.]) if r['route_stage']=='front_x' else np.array([0.,-1.,0.]);idx=ix[t]"
b="""feedback=r.get('cop_slip_following',{});direction_xy=feedback.get('drive_direction_xy')
  if direction_xy is None:
   if r.get('front_diagonal_entry',{}).get('selected'):
    delta=np.array([r['route_goal_x'],r['front_diagonal_entry']['goal_y']])-np.array(r['observed_target'][:2]);direction_xy=delta/np.linalg.norm(delta)
   else:direction_xy=np.array([-1.,0.]) if r['route_stage']=='front_x' else np.array([0.,-1.])
  direction=np.r_[direction_xy,0.];assert abs(np.linalg.norm(direction)-1)<1e-8;transverse=np.cross([0.,0.,1.],direction);idx=ix[t]"""
assert s.count(a)==1;s=s.replace(a,b)
a=' summaries={}';b="""  measured=measurements[-1];measured['drive_direction_xy']=direction[:2].tolist();measured['diagonal_command']=bool(r.get('front_diagonal_entry',{}).get('selected'))
  measured['command_lead_along_drive_mm']=float((np.array(r['target_xyz'])-r['observed_support_xyz'])@direction*1000)
  measured['support_ahead_of_target_mm']=float((np.array(r['observed_support_xyz'])-r['observed_target'])@direction*1000)
  measured['hand_transverse_torque_mean_nm']=float(ctx['torques']['start_com'][idx,target,0].mean(axis=0)@transverse)
  measured['table_transverse_torque_mean_nm']=float(ctx['torques']['start_com'][idx,target,1].mean(axis=0)@transverse)
  measured['net_transverse_torque_mean_nm']=float(ctx['torques']['start_com'][idx,target].sum(axis=1).mean(axis=0)@transverse)
  measured['next_mode']=modes[t+1]['mode'];measured['next_recontact_reason']=modes[t+1].get('last_recontact_reason')
  measured['observed_before_action_tilt_rad']=r['observed_parcel_tilt_rad']
  measured['current_cop_local_mm']=None if feedback.get('measured_cop_local') is None else (np.array(feedback['measured_cop_local'])*1000).tolist()
 summaries={} """
assert s.count(a)==1;s=s.replace(a,b);s=s.replace('SUBSTEP_PHASE_FORCE_BALANCE_DIAGNOSTIC.json','FRONT_BOX_DIRECTED_FORCE_DIAGNOSTIC.json');ast.parse(s)
d=w/'analyze_front_box_directed_force.py'
with d.open('x') as f:f.write(s)
print('prepared original-math diagnostic, observed diagonal direction fixed')
