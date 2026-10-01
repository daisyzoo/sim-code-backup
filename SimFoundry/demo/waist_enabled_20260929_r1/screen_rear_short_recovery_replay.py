"""Recorded-input rear recovery-height probe using the existing unchanged controller.
Candidate .86m only affects subsequent recontacts; initial approach/release .91m,
load/tilt guards and all loaded control formulas remain unchanged. This is not
recursive physics: future observations are fixed recordings. No collector edits.
"""
from pathlib import Path
import sys,json,hashlib,copy,collections
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_micro_clearance_return';sys.path[:0]=[str(stage),str(repo)]
from rear_cop_route import RearCopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState,extent_x_from_quat
from simfoundry.data.contact_load_control import hand_target_vertical_load
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
reports=[]
specs=[('front_diagonal_entry_groups_r1',840001,'push_box_to_bin'),('front_diagonal_entry_groups_r1',840004,'nudge_mailer_to_bin'),('micro_clearance_groups_r1',840001,'push_box_to_bin'),('micro_clearance_groups_r1',840004,'nudge_mailer_to_bin')]
for run,cid,task in specs:
 ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];assert not plan['front_route_selected'] and not plan['initial_top_selected'];side='right' if 'push_box' in task else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';actor='parcel_box' if key=='box' else 'mailer';size=tuple(plan['top_recontact']['contact_size_xyz']);osize=(.15,.145,.04) if key=='box' else (.14,.09,.045)
 with np.load(ep/'trace.npz') as z:tr={k:z[k].astype(float) for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k].astype(float) for k in z.files}
 packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};regions={r['step']:r for r in json.loads((ep/'region_approach.json').read_text())['rows']}
 def make(height):
  s=RearCopRouteState(FrontalBypassState(plan,staging_z=.92,press_z=.822,feedback_rear_endpoint=True,follow_target_y=True),side,size,guarded_descent=True,continuous_drag=True,alignment_tolerance_m=.01,tilt_recontact_rad=.03,confirm_terminal_release=True,hold_established_x=True,recontact_travel_z=height,rear_cop_enabled=True,rear_core_slice_enabled=True,rear_coupled_progress_enabled=True,rear_joint_xy_enabled=True,rear_cop_core_size=plan['rear_cop_centering']['actual_core_size_xyz']);s.load.desired_n=5.;return s
 off=make(.91);on=make(.86);changed=[];errors=[];maxerr=0.;on_modes=collections.Counter();fixtures=[]
 for record in fr['rows']:
  t=record['step'];packet=packets[t-1];load=hand_target_vertical_load(packet,side,actor);contact=loaded_forward_margin(packet,side,actor,tr[key][t],ori[key][t],size,plan['direction']);args=(tr['palm_'+side][t],tr[key][t],tr[other][t],extent_x_from_quat(size,ori[key][t]),extent_x_from_quat(osize,ori[other][t]));kw=dict(tip=record['observed_support_xyz'],quat=ori[key][t],control_offset_local=record.get('observed_support_offset_local') or record.get('control_offset_local') or (.2,0,.007),load_n=load,hand_obstacle_gap_m=record.get('hand_obstacle_gap_m'),slip_contact=contact)
  before=copy.deepcopy(on);a=off.update(*args,**kw);b=on.update(*args,**kw);region=regions.get(t);solver=region.get('solver') if region else None
  if solver is not None:
   assert not region['abort_reason'] and solver['accepted']
   for state,row in [(off,a),(on,b)]:
    if solver.get('handover'):
     state.selected_surface_local_xy=tuple(solver['selected_surface_local_xy']);state.top_mode=state.mode='top_press';state.mode_step=1;state.settled=0;state.command=None;state.push_x_anchor=None;state.approach_xy_bias=[0.,0.];state.descent_z=float(kw['tip'][2]);state.load.bias_m=0.
    else:
     state.top_mode=state.mode='top_descend';state.settled=0;state.command=None;state.load.bias_m=0.;state.descent_z=float(kw['tip'][2])
   # Original external region override is measured, replayed in both inputs.
   a['mode']=b['mode']=record['mode'];a['target_xyz']=b['target_xyz']=record['target_xyz']
  err=float(np.max(abs(np.array(a['target_xyz'])-record['target_xyz'])));maxerr=max(maxerr,err)
  if a['mode']!=record['mode'] or err>2e-6:errors.append(dict(step=t,mode=a['mode'],actual=record['mode'],error=err))
  on_modes[b['mode']]+=1
  if a['mode']!=b['mode'] or np.max(abs(np.array(a['target_xyz'])-b['target_xyz']))>1e-7:changed.append(dict(step=t,parent_mode=a['mode'],mode=b['mode'],target_xyz=b['target_xyz'],travel_height_m=b.get('travel_height_m'),recontacts=b.get('recontacts')))
  if before.top_mode=='top_push' and before.recontacts>0 and not fixtures:fixtures.append((before,args,kw))
 assert not errors,(ep,errors[:8])
 assert fixtures
 base,args,kw=fixtures[0];guards=[]
 for label in ['tilt','lost_contact','release','initial','bad_height']:
  a=copy.deepcopy(base);aa=list(copy.deepcopy(args));kk=copy.deepcopy(kw)
  if label=='tilt':kk['quat']=[np.sin(.04/2),0,0,np.cos(.04/2)]
  elif label=='lost_contact':a.lost_contact_steps=3;kk['load_n']=0.;kk['slip_contact']=None
  elif label=='release':aa[1]=np.array(aa[1]);aa[1][1]=.35*plan['direction']
  elif label=='initial':a.top_mode='top_lift';a.recontacts=0;a.start=tuple(kk['tip']);kk['tip']=list(kk['tip']);kk['tip'][2]=.8
  else:
   a.recontact_travel_z=.82
   try:a.update(*aa,**kk)
   except ValueError:guards.append(dict(case=label,rejected=True));continue
   raise AssertionError('bad height accepted')
  row=a.update(*aa,**kk)
  if label=='tilt':assert row['last_recontact_reason']=='incipient_tilt_independent' and row['mode'] in ['top_lift','top_cross']
  if label=='lost_contact':assert row['last_recontact_reason']=='lost_contact' and row['mode'] in ['top_lift','top_cross']
  if label=='release':assert row['mode']=='top_release' and row['target_xyz'][2]>=.91
  if label=='initial':assert row['travel_height_m']==.91 and row['target_xyz'][2]>=.91
  guards.append(dict(case=label,mode=row['mode']))
 reports.append(dict(episode=str(ep),frames=len(fr['rows']),parent_matches_actual=True,max_parent_reference_error_m=maxerr,candidate_modes=dict(on_modes),changed_rows=changed,guard_checks=guards,source_sha256={n:sha(ep/n) for n in ['trace.npz','parcel_orientation.npz','frontal_bypass.json','region_approach.json','solved_contact_forces.json']}));print(ep.name,run,'matched',len(fr['rows']),'changed',len(changed),flush=True)
out=dict(scope=__doc__,passed=True,episodes=reports,collector_wired=False,physical_validation=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'rear_cop_route.py',stage/'region_top_contact.py',stage/'collect_paired_sorting.py']});(w/'REAR_SHORT_RECOVERY_REPLAY.json').write_text(json.dumps(out,indent=2))
