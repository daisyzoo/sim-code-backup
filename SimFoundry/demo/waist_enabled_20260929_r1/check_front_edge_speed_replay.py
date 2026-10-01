"""Full recorded-input controller replay plus guard tests; no dynamics prediction."""
from pathlib import Path
import sys,json,copy,hashlib,collections
import numpy as np
w=Path(__file__).resolve().parent;stage=w/'staged_front_edge_speed_probe';sys.path[:0]=[str(stage),str(w.parents[1])]
from front_cop_route import FrontCopRouteState
import importlib.util
_spec=importlib.util.spec_from_file_location("parent_front_cop_route",w/"staged_front_drive_increment/front_cop_route.py");_parent=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=_parent;_spec.loader.exec_module(_parent)
ParentCopRouteState=_parent.FrontCopRouteState
from simfoundry.data.front_top_route import FrontTopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
from simfoundry.data.contact_load_control import hand_target_vertical_load
from simfoundry.data.tabletop_route_candidates import footprint_radii
paths=[w/run/f'case_{cid}/layout_{cid}_{task}' for run in ['rear_core_slice_groups_r1','front_drive_increment_groups_r1'] for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]];reports=[]
encode=lambda x:json.dumps(x,sort_keys=True,default=lambda v:v.tolist() if isinstance(v,np.ndarray) else float(v))
for ep in paths:
 log=json.loads((ep/'frontal_bypass.json').read_text());plan=log['plan'];cfg=json.loads((ep.parent/'provenance.json').read_text())['args'];side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';actor='parcel_box' if side=='right' else 'mailer';size=(.14,.09,.045) if side=='right' else (.15,.145,.04);osize=(.15,.145,.04) if side=='right' else (.14,.09,.045)
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 packets={x['after_action_step']:x for x in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
 def make(cls,**extra):
  state=cls(FrontalBypassState(plan,staging_z=.92,press_z=.822,feedback_rear_endpoint=True,follow_target_y=True),side,size,guarded_descent=True,continuous_drag=True,drag_step_m=.003,alignment_tolerance_m=.01,tilt_recontact_rad=.03,confirm_terminal_release=True,front_inset_fraction=.9,obstacle_size=osize,route_clearance_m=.012,recover_clearance=True,confirm_nominal_clearance=True,recontact_travel_z=.86,recovery_hysteresis_m=.0005,**extra);state.load.desired_n=5.;return state
 original=make(ParentCopRouteState,cop_drive_step_m=.002,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True);off=make(FrontCopRouteState,cop_drive_step_m=.002,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True);on=make(FrontCopRouteState,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True,cop_drive_step_m=.002,edge_speed_enabled=True,edge_core_size=tuple(np.array(size)*([.96,.96,1.] if key=='box' else [.90,.88,1.])));records=[];guard_fixture=None;maxstep=0.;override=0
 for raw in log['rows']:
  t=raw['step'];packet=packets.get(t-1)
  if packet:assert np.max(abs(np.asarray(packet['post_action_pose'][key])-tr[key][t]))<1e-6
  load=hand_target_vertical_load(packet,side,actor);contact=loaded_forward_margin(packet,side,actor,tr[key][t],ori[key][t],size,-1 if side=='right' else 1)
  args=(tr['palm_'+side][t],tr[key][t],tr[other][t],footprint_radii(size,ori[key][t])[0],footprint_radii(osize,ori[other][t])[0]);kw=dict(tip=raw['observed_support_xyz'],quat=ori[key][t],obstacle_quat=ori[other][t],control_offset_local=raw.get('control_offset_local') or (.2,0,.007),load_n=load,hand_obstacle_gap_m=raw['hand_obstacle_gap_m'])
  a=original.update(*args,slip_contact=contact,**kw);b=off.update(*args,slip_contact=contact,**kw);assert encode(a)==encode(b),(ep,t,'default differs')
  before=copy.deepcopy(on);previous=on.last_emitted_xy;c=on.update(*args,slip_contact=contact,**kw)
  assert a['mode']==c['mode'] and abs(a['target_xyz'][2]-c['target_xyz'][2])<1e-12,(ep,t,'mode/Z change on identical observations')
  f=c['cop_slip_following']
  if f['override']:
   if f['route_anchor_reset']:
    assert np.max(abs(np.array(f['anchor_local'])-np.array(f['measured_cop_local'])))<1e-12
    # Recorded float32 quaternion round-trip can leave sub-nanometer correction.
    assert np.max(np.abs(f['slip_correction_xy']))<1e-8 and np.max(np.abs(f['object_anchor_translation_xy']))<1e-12, (str(ep),t,f['slip_correction_xy'],f['object_anchor_translation_xy'])
   assert abs(np.dot(f['slip_correction_xy'],f['drive_direction_xy']))<1e-12,(ep,t,'feedback cancels drive')
   goal_y=c['clearance_progress']['front_hold_y'] if c['route_stage']=='front_x' else on.route_report['goal_y']
   error=np.array([c['route_goal_x'],goal_y])-tr[key][t,:2];distance=np.linalg.norm(error)
   R=np.asarray(__import__('simfoundry.data.top_contact_bypass',fromlist=['rotation_xyzw']).rotation_xyzw(ori[key][t]));local=np.asarray(contact['weighted_contact_local']);half=np.asarray(on.edge_core_size)[:2]/2;active_axis=0 if c['route_stage']=='front_x' else 1;sign=-1 if active_axis==0 or side=='right' else 1;v=sign*R[active_axis];ends=[]
   if np.all(abs(local[:2])<=half):
    ends=[((half[j] if v[j]>0 else -half[j])-local[j])/v[j] for j in range(2) if abs(v[j])>1e-10]
   forward=max(0.,min(ends)) if ends else 0.;expected_step=.001+.001*min(1.,forward/.01)
   assert abs(f['edge_speed']['drive_step_m']-expected_step)<1e-12
   expected_drive=error*(min(expected_step,distance)/distance) if distance else np.zeros(2)
   assert np.max(abs(expected_drive-f['drive_xy']))<1e-10
   rot=np.asarray(__import__('simfoundry.data.top_contact_bypass',fromlist=['rotation_xyzw']).rotation_xyzw(ori[key][t]))
   expected_raw=.05*(rot@(np.array(f['anchor_local'])-np.array(f['measured_cop_local'])))[:2]
   assert np.max(abs(expected_raw-f['raw_slip_correction_xy']))<1e-9

   assert c['mode']=='top_push' and contact['valid'] and contact['normal_load_n']>=.3
   mixed=f['route_axis_control'];axis=mixed['active_axis'];assert axis==(0 if c['route_stage']=='front_x' else 1)
   assert c['target_xyz'][axis]==mixed['original_cop_xy'][axis]
   expected_cross=previous[1-axis]+np.clip(mixed['parent_xy'][1-axis]-previous[1-axis],-.003,.003)
   assert c['target_xyz'][1-axis]==expected_cross
   assert mixed['emitted_xy']==list(c['target_xyz'][:2])
   step=float(np.max(abs(np.array(c['target_xyz'][:2])-previous)));assert step<=.003000001,(str(ep),t,step,previous,c['target_xyz'],f['route_axis_control']);maxstep=max(maxstep,step);override+=1
   if guard_fixture is None:guard_fixture=(before,args,kw,contact,t)
  elif c['mode']!='top_push':assert on.cop_slip.local_anchor is None
  records.append(dict(step=t,mode=c['mode'],feedback=f,counterfactual_row=json.loads(encode(c))))
 assert guard_fixture is not None,'No loaded fixture; do not silently skip this case'
 state,args,kw,contact,fixture_t=guard_fixture;checks=[]
 for label in ['hand_gap','other_motion','target_table','tilt','missing_cop','lost_contact','terminal_release']:
  a=copy.deepcopy(state);b=copy.deepcopy(state);a.cop_slip_enabled=False;a.edge_speed_enabled=False;aa=list(args);kk=dict(kw);cc=contact
  if label=='hand_gap':kk['hand_obstacle_gap_m']=.004
  elif label=='other_motion':aa[2]=np.array(args[2])+[.021,0,0]
  elif label=='target_table':aa[1]=np.array(args[1]);aa[1][0]=.25
  elif label=='tilt':kk['quat']=[np.sin(.06/2),0,0,np.cos(.06/2)]
  elif label=='missing_cop':cc=None
  elif label=='lost_contact':
   kk['load_n']=0.;cc=None;a.lost_contact_steps=b.lost_contact_steps=2;a.top_mode=b.top_mode='top_push';a.command=b.command=(*state.last_emitted_xy,kw['tip'][2])
  else:
   aa[1]=np.array(args[1]);aa[1][1]=.35 if side=='left' else -.35;a.top_mode=b.top_mode='top_push';a.command=b.command=(*state.last_emitted_xy,kw['tip'][2])
  baseline=a.update(*aa,**kk);candidate=b.update(*aa,slip_contact=cc,**kk);f=candidate.pop('cop_slip_following');assert not f['override'],(label,'override bypasses guard');assert encode(baseline)==encode(candidate),(label,'guard changed')
  if label=='terminal_release':assert candidate['mode']=='top_release',(label,'fixture must actually release')
  if label!='missing_cop':assert candidate['mode']!='top_push',(label,'fixture did not activate protection')
  checks.append(dict(case=label,mode=candidate['mode'],reason=candidate.get('route_stop_reason') or candidate.get('last_recontact_reason') or candidate.get('release_reason')))
 # No-load replay must not invent contact confirmation.
 empty=copy.deepcopy(state);empty.top_mode='top_press';empty.settled=0;empty.load.filtered_n=0.;empty.cop_slip.reset()
 for _ in range(12):
  zero=empty.update(*args,slip_contact=None,**dict(kw,load_n=0.));assert zero['mode']!='top_push' and not zero['cop_slip_following']['override']
 reports.append(dict(episode=str(ep),zero_load_press_steps_without_push=12,default_exact_frames=len(records),fixed_observation_mode_and_z_equal=True,override_frames=override,loaded_route_resets=sum(r['feedback'].get('override',False) and r['feedback'].get('route_anchor_reset',False) for r in records),max_xy_step_m=maxstep,guard_or_missing_contact_checks=checks,records=records,source_sha256={f:hashlib.sha256((ep/f).read_bytes()).hexdigest() for f in ['raw.npz','frontal_bypass.json','solved_contact_forces.json','trace.npz','parcel_orientation.npz']}));print({k:v for k,v in reports[-1].items() if k not in {'records','source_sha256'}},flush=True)
negative=[]
for bad in [True,False,None,float('nan'),float('inf'),.0009,.0031]:
 test=copy.deepcopy(state);test.cop_drive_step_m=bad
 try:test.update(*args,slip_contact=contact,**kw)
 except ValueError:negative.append(str(bad))
 else:raise AssertionError('Invalid increment accepted')
out=dict(passed=True,negative_increments_rejected=negative,rows=reports,source_sha256={f:hashlib.sha256((stage/f).read_bytes()).hexdigest() for f in ['front_cop_route.py','contact_slip_following.py','front_edge_speed.py']},checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Four complete recorded-input streams. Disabled edge governor equals parent2mm exactly. Enabled governor interpolates1..2mm within10mm forward collision-core edge; independently reconstructed geometric distance/drive, original route-axis mix/Z/mode/load/guards preserved. No collector wiring or actual command auditor yet; synthetic output is not physical success.',training_ready=False)
(stage/'EDGE_SPEED_REPLAY_CHECK.json').write_text(json.dumps(out,indent=2))
