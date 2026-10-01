"""Complete fixed-record input replay; not a physical counterfactual or data.
Default-off must equal current front controller and actual emitted references.
On direction changes, reuse existing lift/recontact; preserve original guards.
"""
from pathlib import Path
import sys,json,copy,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_front_direction_recontact_probe';sys.path[:0]=[str(stage),str(w/'staged_self_clearance_task_ik'),str(repo)]
from front_cop_route import FrontCopRouteState as Parent
from front_cop_route_recontact import FrontCopRouteState as Candidate
from simfoundry.data.frontal_bypass import FrontalBypassState
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
from simfoundry.data.contact_load_control import hand_target_vertical_load
from simfoundry.data.tabletop_route_candidates import footprint_radii
encode=lambda x:json.dumps(x,sort_keys=True,default=lambda v:v.tolist() if isinstance(v,np.ndarray) else float(v));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[];fixtures=[]
for run in ['joint_edge_retry_groups_r1','self_clearance_groups_r1']:
 for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];assert plan['front_route_selected'];side='right' if 'push_box' in task else 'left';key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';actor='parcel_box' if side=='right' else 'mailer';size=(.14,.09,.045) if side=='right' else (.15,.145,.04);osize=(.15,.145,.04) if side=='right' else (.14,.09,.045)
  with np.load(ep/'trace.npz') as z:tr={k:z[k].copy() for k in z.files}
  with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k].copy() for k in z.files}
  packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
  def make(cls,**extra):
   s=cls(FrontalBypassState(plan,staging_z=.92,press_z=.822,feedback_rear_endpoint=True,follow_target_y=True),side,size,guarded_descent=True,continuous_drag=True,drag_step_m=.003,alignment_tolerance_m=.01,tilt_recontact_rad=.03,confirm_terminal_release=True,front_inset_fraction=.9,obstacle_size=osize,route_clearance_m=.012,recover_clearance=True,confirm_nominal_clearance=True,recontact_travel_z=.86,recovery_hysteresis_m=.0005,cop_drive_step_m=.002,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True,edge_speed_enabled=True,edge_core_size=tuple(plan['front_cop_slip_following']['edge_speed']['actual_core_size_xyz']),**extra);s.load.desired_n=5.;return s
  parent=make(Parent);off=make(Candidate);on=make(Candidate,recontact_on_route_change=True);events=[];records=[];maxraw=0.
  for r in fr['rows']:
   t=r['step'];packet=packets[t-1];assert np.max(abs(np.array(packet['post_action_pose'][key])-tr[key][t]))<1e-6;load=hand_target_vertical_load(packet,side,actor);contact=loaded_forward_margin(packet,side,actor,tr[key][t],ori[key][t],size,-1 if side=='right' else 1)
   args=(tr['palm_'+side][t],tr[key][t],tr[other][t],footprint_radii(size,ori[key][t])[0],footprint_radii(osize,ori[other][t])[0]);kw=dict(tip=r['observed_support_xyz'],quat=ori[key][t],obstacle_quat=ori[other][t],control_offset_local=r['control_offset_local'],load_n=load,hand_obstacle_gap_m=r['hand_obstacle_gap_m'],slip_contact=contact)
   a=parent.update(*args,**kw);b=off.update(*args,**kw);assert encode(a)==encode(b),(ep,t,'off differs')
   assert a['mode']==r['mode'] and a['route_stage']==r['route_stage'] and a.get('route_stop_reason')==r.get('route_stop_reason'),(ep,t,'raw mode mismatch')
   err=float(np.max(abs(np.array(a['target_xyz'])-np.array(r['target_xyz']))));maxraw=max(maxraw,err);assert err<2e-7,(ep,t,err)
   before=copy.deepcopy(on);c=on.update(*args,**kw);event=c.get('direction_change_recontact')
   if event and event['restarted']:
    assert event['stage_changed'] and event['previous_top_mode']=='top_push' and event['measured_vertical_load_n']>=.3
    assert c['mode'] in ('top_lift','top_cross') and c['last_recontact_reason']=='front_route_direction_change' and c['contact_load']['applied_z_bias_m']==0
    assert not c['cop_slip_following']['override'] and on.cop_slip.local_anchor is None
    if c['mode']=='top_lift':assert np.max(abs(np.array(c['target_xyz'][:2])-np.array(kw['tip'][:2])))<1e-12
    events.append(dict(step=t,record=event,mode=c['mode'],target_xyz=c['target_xyz']));fixtures.append((before,args,kw,ep.name,t))
   if c['mode']!='top_push':assert not c['cop_slip_following']['override']
   records.append(dict(step=t,mode=c['mode'],route_stage=c['route_stage'],recontact=event,target_xyz=c['target_xyz'],stop=c.get('route_stop_reason')))
  reports.append(dict(episode=str(ep),frames=len(records),default_off_exact=True,max_reference_reconstruction_error=maxraw,recontact_events=events,counterfactual_rows=records,source_sha256={n:sha(ep/n) for n in ['frontal_bypass.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json']}));print(ep,'frames',len(records),'events',[e['step'] for e in events],flush=True)
assert fixtures,'No actual transition fixtures'
checks=[]
state,args,kw,ep,t=fixtures[0]
for label in ['hand_gap','other_motion','table_margin','tilt','terminal','no_load','non_push','already_release','invalid_flag']:
 a=copy.deepcopy(state);b=copy.deepcopy(state);a.recontact_on_route_change=False;aa=list(copy.deepcopy(args));kk=copy.deepcopy(kw)
 if label=='hand_gap':kk['hand_obstacle_gap_m']=.004
 elif label=='other_motion':aa[2]=np.array(aa[2])+[.021,0,0]
 elif label=='table_margin':aa[1]=np.array(aa[1]);aa[1][0]=.25
 elif label=='tilt':kk['quat']=[np.sin(.06/2),0,0,np.cos(.06/2)]
 elif label=='terminal':aa[1]=np.array(aa[1]);aa[1][1]=.35 if state.side=='left' else -.35
 elif label=='no_load':kk['load_n']=0.;kk['slip_contact']=None
 elif label=='non_push':a.top_mode=b.top_mode='top_descend';a.descent_z=b.descent_z=.84
 elif label=='already_release':a.top_mode=b.top_mode='top_release';a.release=b.release=tuple(kk['tip'])
 else:
  b.recontact_on_route_change=1
  try:b.update(*aa,**kk)
  except ValueError:checks.append(dict(case=label,rejected=True));continue
  raise AssertionError('Invalid enable type accepted')
 parent=a.update(*aa,**kk);candidate=b.update(*aa,**kk);event=candidate.pop('direction_change_recontact',None);assert not event or not event['restarted'],label;assert encode(parent)==encode(candidate),(label,'original protection changed');checks.append(dict(case=label,mode=candidate['mode'],original_equal=True))
out=dict(passed=True,scope=__doc__,episodes=reports,guard_checks=checks,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'front_top_route_recontact.py',stage/'front_cop_route_recontact.py',w/'staged_self_clearance_task_ik/front_cop_route.py',repo/'simfoundry/data/front_top_route.py']},training_ready=False);(stage/'RECORDED_INPUT_REPLAY.json').write_text(json.dumps(out,indent=2));print('passed all',sum(e['frames'] for e in reports),'frames',len(checks),'guard branches')
