"""Micro-repair contact-retention fixed-record input replay; not a physical counterfactual or data.
Default-off must equal current front controller and actual emitted references.
On first/large/edge turns keep existing lift/recontact; preserve original guards.
"""
from pathlib import Path
import sys,json,copy,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_micro_clearance_probe';sys.path[:0]=[str(stage),str(w/'staged_front_diagonal_entry'),str(w),str(repo)]
from front_cop_route_diagonal import FrontCopRouteState as Parent
from front_cop_route_micro import FrontCopRouteState as Candidate
from audit_micro_clearance_return import verify_stream
from audit_front_diagonal_entry_live import reconstruct
from simfoundry.data.frontal_bypass import FrontalBypassState
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
from simfoundry.data.contact_load_control import hand_target_vertical_load
from simfoundry.data.tabletop_route_candidates import footprint_radii
encode=lambda x:json.dumps(x,sort_keys=True,default=lambda v:v.tolist() if isinstance(v,np.ndarray) else float(v));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[];fixtures=[];independent_reports=[];tamper_checks=[]
for run in ['front_diagonal_entry_groups_r1']:
 for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];assert plan['front_route_selected'];side='right' if 'push_box' in task else 'left';key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';actor='parcel_box' if side=='right' else 'mailer';size=(.14,.09,.045) if side=='right' else (.15,.145,.04);osize=(.15,.145,.04) if side=='right' else (.14,.09,.045)
  # Runtime collector uses .numpy().tolist(), hence Python doubles on exact
  # float32 observations; avoid NumPy float32 arithmetic inside scalar helpers.
  with np.load(ep/'trace.npz') as z:tr={k:z[k].astype(float) for k in z.files}
  with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k].astype(float) for k in z.files}
  packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
  def make(cls,**extra):
   s=cls(FrontalBypassState(plan,staging_z=.92,press_z=.822,feedback_rear_endpoint=True,follow_target_y=True),side,size,guarded_descent=True,continuous_drag=True,drag_step_m=.003,alignment_tolerance_m=.01,tilt_recontact_rad=.03,confirm_terminal_release=True,front_inset_fraction=.9,obstacle_size=osize,route_clearance_m=.012,recover_clearance=True,confirm_nominal_clearance=True,recontact_travel_z=.86,recovery_hysteresis_m=.0005,cop_drive_step_m=.002,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True,edge_speed_enabled=True,edge_core_size=tuple(plan['front_cop_slip_following']['edge_speed']['actual_core_size_xyz']),recontact_on_route_change=True,diagonal_entry=True,**extra);s.load.desired_n=5.;return s
  parent=make(Parent);off=make(Candidate);on=make(Candidate,retain_micro_repair_contact=True);events=[];records=[];fullrows=[];maxraw=0.
  for r in fr['rows']:
   t=r['step'];packet=packets[t-1];assert np.max(abs(np.array(packet['post_action_pose'][key])-tr[key][t]))<1e-6;load=hand_target_vertical_load(packet,side,actor);contact=loaded_forward_margin(packet,side,actor,tr[key][t],ori[key][t],size,-1 if side=='right' else 1)
   args=(tr['palm_'+side][t],tr[key][t],tr[other][t],footprint_radii(size,ori[key][t])[0],footprint_radii(osize,ori[other][t])[0]);kw=dict(tip=r['observed_support_xyz'],quat=ori[key][t],obstacle_quat=ori[other][t],control_offset_local=r['control_offset_local'],load_n=load,hand_obstacle_gap_m=r['hand_obstacle_gap_m'],slip_contact=contact)
   a=parent.update(*args,**kw);b=off.update(*args,**kw);assert encode(a)==encode(b),(ep,t,'off differs')
   assert a['mode']==r['mode'] and a['route_stage']==r['route_stage'] and a.get('route_stop_reason')==r.get('route_stop_reason'),(ep,t,'raw mode mismatch')
   err=float(np.max(abs(np.array(a['target_xyz'])-np.array(r['target_xyz']))));maxraw=max(maxraw,err);assert err<2e-7,(ep,t,err)
   before=copy.deepcopy(on);c=on.update(*args,**kw);event=c.get('direction_change_recontact')
   c.update(step=t,observed_support_xyz=r['observed_support_xyz']);fullrows.append(copy.deepcopy(c))
   diagonal=c.get('front_diagonal_entry')
   if diagonal and diagonal['selected']:
    assert c['mode']=='top_push' and c['route_stage']=='front_x' and load>=.3
    assert diagonal['proposal']['minimum_axis_gap_m']>=.012-1e-10 and diagonal['proposal']['minimum_table_margin_m']>=.005-1e-10
    feedback=c['cop_slip_following']
    if feedback['override']:
     assert feedback['diagonal_entry_control']['both_xy_from_cop'] and 'route_axis_control' not in feedback
     assert np.max(abs(np.array(c['target_xyz'][:2])-feedback['command_xy']))<1e-12
     assert np.max(abs(np.array(feedback['command_delta_xy'])))<=.003+1e-12
    pass
   if event and event.get('micro_repair_retention',{}).get('retained'):fixtures.append((before,args,kw,ep.name,t))
   if event and event['restarted']:
    assert event['stage_changed'] and event['previous_top_mode']=='top_push' and event['measured_vertical_load_n']>=.3
    assert c['mode'] in ('top_lift','top_cross') and c['last_recontact_reason']=='front_route_direction_change' and c['contact_load']['applied_z_bias_m']==0
    assert not c['cop_slip_following']['override'] and on.cop_slip.local_anchor is None
    if c['mode']=='top_lift':assert np.max(abs(np.array(c['target_xyz'][:2])-np.array(kw['tip'][:2])))<1e-12
    events.append(dict(step=t,record=event,mode=c['mode'],target_xyz=c['target_xyz']))
   if c['mode']!='top_push':assert not c['cop_slip_following']['override']
   records.append(dict(step=t,mode=c['mode'],route_stage=c['route_stage'],recontact=event,diagonal=diagonal,target_xyz=c['target_xyz'],stop=c.get('route_stop_reason')))
  independently_checked,errors=reconstruct(fullrows,plan,tr,ori,packets,key);assert not errors,(str(ep),errors[:10])
  events_independent=verify_stream(fullrows,plan,tr,ori,packets,key,True)
  independent_reports.append(dict(episode=str(ep),frames=len(fullrows),loaded_frames=len(independently_checked),events=events_independent,passed=True))
  if not tamper_checks:
   selected=next(i for i,c in enumerate(fullrows) if c.get('direction_change_recontact',{}).get('micro_repair_retention',{}).get('retained'))
   for name in ['retained','normal','excursion','margin','counter','mode']:
    changed=copy.deepcopy(fullrows);c=changed[selected];m=c['direction_change_recontact']['micro_repair_retention']
    if name=='retained':m['retained']=False
    elif name=='normal':m['normal_load_n']+=1.
    elif name=='excursion':m['maximum_excursion_m']+=.01
    elif name=='margin':m['current_core_margin_m']+=.01
    elif name=='counter':c['recontacts']+=1
    else:c['mode']='top_lift'
    try:verify_stream(changed,plan,tr,ori,packets,key,True)
    except AssertionError:tamper_checks.append(dict(case=name,rejected=True))
    else:raise AssertionError((name,'tamper accepted'))
  reports.append(dict(episode=str(ep),frames=len(records),default_off_exact=True,max_reference_reconstruction_error=maxraw,recontact_events=events,counterfactual_rows=records,source_sha256={n:sha(ep/n) for n in ['frontal_bypass.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json']}));print(ep,'frames',len(records),'events',[e['step'] for e in events],flush=True)
assert fixtures,'No actual transition fixtures'
checks=[]
state,args,kw,ep,t=fixtures[0]
for label in ['hand_gap','other_motion','table_margin','tilt','terminal','no_load','non_push','already_release','invalid_flag']:
 a=copy.deepcopy(state);b=copy.deepcopy(state);a.retain_micro_repair_contact=False;aa=list(copy.deepcopy(args));kk=copy.deepcopy(kw)
 if label=='hand_gap':kk['hand_obstacle_gap_m']=.004
 elif label=='other_motion':aa[2]=np.array(aa[2])+[.021,0,0]
 elif label=='table_margin':aa[1]=np.array(aa[1]);aa[1][0]=.25
 elif label=='tilt':kk['quat']=[np.sin(.06/2),0,0,np.cos(.06/2)]
 elif label=='terminal':aa[1]=np.array(aa[1]);aa[1][1]=.35 if state.side=='left' else -.35
 elif label=='no_load':kk['load_n']=0.;kk['slip_contact']=None
 elif label=='non_push':a.top_mode=b.top_mode='top_descend';a.descent_z=b.descent_z=.84
 elif label=='already_release':a.top_mode=b.top_mode='top_release';a.release=b.release=tuple(kk['tip'])
 else:
  b.retain_micro_repair_contact=1
  try:b.update(*aa,**kk)
  except ValueError:checks.append(dict(case=label,rejected=True));continue
  raise AssertionError('Invalid enable type accepted')
 parent=a.update(*aa,**kk);candidate=b.update(*aa,**kk);event=candidate.get('direction_change_recontact');micro=event.pop('micro_repair_retention',None) if event else None;assert not micro or not micro['retained'],label;assert encode(parent)==encode(candidate),(label,'original protection changed');checks.append(dict(case=label,mode=candidate['mode'],original_equal=True))
out=dict(passed=True,scope=__doc__,episodes=reports,guard_checks=checks,independent_replay=independent_reports,tamper_checks=tamper_checks,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'front_top_route_micro.py',stage/'front_cop_route_micro.py',stage/'micro_clearance_return.py',w/'audit_micro_clearance_return.py',w/'audit_front_diagonal_entry_live.py',w/'staged_front_diagonal_entry/front_cop_route_diagonal.py',repo/'simfoundry/data/front_top_route.py']},training_ready=False);(stage/'RECORDED_INPUT_REPLAY.json').write_text(json.dumps(out,indent=2));print('passed all',sum(e['frames'] for e in reports),'frames',len(checks),'guard branches')
