"""Full recorded-input controller replay plus guard tests; no dynamics prediction."""
from pathlib import Path
import sys,json,copy,hashlib,collections
import numpy as np
w=Path(__file__).resolve().parent;stage=w/'staged_front_cop_transverse';sys.path[:0]=[str(stage),str(w.parents[1])]
from front_cop_route import FrontCopRouteState
from simfoundry.data.front_top_route import FrontTopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
from simfoundry.data.contact_load_control import hand_target_vertical_load
from simfoundry.data.tabletop_route_candidates import footprint_radii
paths=[w/'region_continuity_groups_r1/case_840001/layout_840001_nudge_mailer_to_bin',w/'projected_object_relative_r1/case_62008/layout_62008_push_box_to_bin',w/'front_cop_groups_r1/case_840001/layout_840001_nudge_mailer_to_bin',w/'front_cop_groups_r1/case_840004/layout_840004_push_box_to_bin'];reports=[]
encode=lambda x:json.dumps(x,sort_keys=True,default=lambda v:v.tolist() if isinstance(v,np.ndarray) else float(v))
for ep in paths:
 log=json.loads((ep/'frontal_bypass.json').read_text());plan=log['plan'];cfg=json.loads((ep.parent/'provenance.json').read_text())['args'];side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';actor='parcel_box' if side=='right' else 'mailer';size=(.14,.09,.045) if side=='right' else (.15,.145,.04);osize=(.15,.145,.04) if side=='right' else (.14,.09,.045)
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 packets={x['after_action_step']:x for x in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
 def make(cls,**extra):
  state=cls(FrontalBypassState(plan,staging_z=.92,press_z=.822,feedback_rear_endpoint=True,follow_target_y=True),side,size,guarded_descent=True,continuous_drag=True,drag_step_m=.003,alignment_tolerance_m=.01,tilt_recontact_rad=.03,confirm_terminal_release=True,front_inset_fraction=.9,obstacle_size=osize,route_clearance_m=.012,recover_clearance=True,confirm_nominal_clearance=True,recontact_travel_z=.86,recovery_hysteresis_m=.0005,**extra);state.load.desired_n=5.;return state
 original=make(FrontTopRouteState);off=make(FrontCopRouteState);on=make(FrontCopRouteState,cop_slip_enabled=True);records=[];guard_fixture=None;maxstep=0.;override=0
 for raw in log['rows']:
  t=raw['step'];packet=packets.get(t-1)
  if packet:assert np.max(abs(np.asarray(packet['post_action_pose'][key])-tr[key][t]))<1e-6
  load=hand_target_vertical_load(packet,side,actor);contact=loaded_forward_margin(packet,side,actor,tr[key][t],ori[key][t],size,-1 if side=='right' else 1)
  args=(tr['palm_'+side][t],tr[key][t],tr[other][t],footprint_radii(size,ori[key][t])[0],footprint_radii(osize,ori[other][t])[0]);kw=dict(tip=raw['observed_support_xyz'],quat=ori[key][t],obstacle_quat=ori[other][t],control_offset_local=raw.get('control_offset_local') or (.2,0,.007),load_n=load,hand_obstacle_gap_m=raw['hand_obstacle_gap_m'])
  a=original.update(*args,**kw);b=off.update(*args,**kw);assert encode(a)==encode(b),(ep,t,'default differs')
  before=copy.deepcopy(on);previous=on.last_emitted_xy;c=on.update(*args,slip_contact=contact,**kw)
  assert a['mode']==c['mode'] and abs(a['target_xyz'][2]-c['target_xyz'][2])<1e-12,(ep,t,'mode/Z change on identical observations')
  f=c['cop_slip_following']
  if f['override']:
   assert abs(np.dot(f['slip_correction_xy'],f['drive_direction_xy']))<1e-12,(ep,t,'feedback cancels drive')
   assert c['mode']=='top_push' and contact['valid'] and contact['normal_load_n']>=.3
   step=float(np.max(abs(np.array(c['target_xyz'][:2])-previous)));assert step<=.003000001;maxstep=max(maxstep,step);override+=1
   if guard_fixture is None:guard_fixture=(before,args,kw,contact,t)
  elif c['mode']!='top_push':assert on.cop_slip.local_anchor is None
  records.append(dict(step=t,mode=c['mode'],feedback=f,counterfactual_row=json.loads(encode(c))))
 assert guard_fixture is not None,'No loaded fixture; do not silently skip this case'
 state,args,kw,contact,fixture_t=guard_fixture;checks=[]
 for label in ['hand_gap','other_motion','target_table','tilt','missing_cop','lost_contact','terminal_release']:
  a=copy.deepcopy(state);b=copy.deepcopy(state);a.cop_slip_enabled=False;aa=list(args);kk=dict(kw);cc=contact
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
 reports.append(dict(episode=str(ep),zero_load_press_steps_without_push=12,default_exact_frames=len(records),fixed_observation_mode_and_z_equal=True,override_frames=override,max_xy_step_m=maxstep,guard_or_missing_contact_checks=checks,records=records,source_sha256={f:hashlib.sha256((ep/f).read_bytes()).hexdigest() for f in ['raw.npz','frontal_bypass.json','solved_contact_forces.json','trace.npz','parcel_orientation.npz']}));print({k:v for k,v in reports[-1].items() if k not in {'records','source_sha256'}},flush=True)
out=dict(passed=True,rows=reports,source_sha256={f:hashlib.sha256((stage/f).read_bytes()).hexdigest() for f in ['front_cop_route.py','contact_slip_following.py']},checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Controller replay on complete FAILED parent front bag, old12mm box, and both current physical COP-stall task input streams under explicit candidate profile; no counterfactual dynamics. Disabled wrapper exactly equals original current controller with identical explicit settings; not a reconstruction claim for historic controller settings. Enabled modes/Z unchanged on fixed observations, original guards/load fallback tested. No physical or training admission.',training_ready=False)
(stage/'FRONT_ROUTE_REPLAY_CHECK.json').write_text(json.dumps(out,indent=2))
