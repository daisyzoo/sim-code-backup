"""Recorded loaded transition fixtures, no simulated force response."""
from pathlib import Path
import sys,json,hashlib,importlib.util,copy
import numpy as np
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w.parents[1]));stage=w/'staged_region_contact_x_follow'
from simfoundry.data.frontal_bypass import FrontalBypassState
classes={}
for label,path in [('parent',w/'staged_region_handover_continuity/region_top_contact.py'),('candidate',stage/'region_top_contact.py')]:
 spec=importlib.util.spec_from_file_location('fixture_'+label,path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);classes[label]=m.TopContactBypassState
p=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else w/'region_continuity_groups_r1/case_840004/layout_840004_nudge_mailer_to_bin';side='right' if 'push_box' in p.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';size=(.14,.09,.045) if side=='right' else (.15,.145,.04);log=json.loads((p/'frontal_bypass.json').read_text());plan=log['plan'];by={r['step']:r for r in log['rows']};reg=json.loads((p/'region_approach.json').read_text())['rows'];handover=next(r for r in reg if r['solver'] and r['solver'].get('handover'));selected=handover['selected_surface_local_xy']
with np.load(p/'trace.npz') as z:tr={k:z[k] for k in z.files}
with np.load(p/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
records=[]
for t,r in by.items():
 prev=by.get(t-1)
 if r['mode']!='top_push' or not prev or prev['mode']!='top_press':continue
 kw=dict(tip=r['observed_support_xyz'],quat=ori[key][t],control_offset_local=r['control_offset_local'],load_n=r['contact_load']['observed_vertical_load_n'],hand_obstacle_gap_m=r['hand_obstacle_gap_m']);outputs={};states={}
 for label,cls in classes.items():
  s=cls(FrontalBypassState(plan,staging_z=.92,press_z=.822,feedback_rear_endpoint=True,follow_target_y=True),side,size,guarded_descent=True,continuous_drag=True,alignment_tolerance_m=.01,tilt_recontact_rad=.03,confirm_terminal_release=True,hold_established_x=True)
  s.top_mode='top_press';s.settled=2;s.load.desired_n=5.;s.load.bias_m=prev['contact_load']['stored_z_bias_m'];s.load.filtered_n=prev['contact_load']['filtered_vertical_load_n'];s.push_x_anchor=prev['push_x_anchor_m'];s.selected_surface_local_xy=tuple(selected);s.last_waypoint_xy=tuple(prev['target_xyz'][:2]);s.recontacts=prev['recontacts'];s.start=tuple(kw['tip'])
  args=(tr['palm_'+side][t],tr[key][t],tr[other][t],plan['target_radius_x'],plan['obstacle_radius_x'])
  no_load=copy.deepcopy(s);no_load.settled=0;no_load.load.filtered_n=0.;nog=dict(kw,load_n=0.)
  for _ in range(12):assert no_load.update(*args,**nog)['mode']!='top_push'
  states[label]=copy.deepcopy(s)
  out=s.update(*args,**kw);assert out['mode']=='top_push';outputs[label]=out
  if label=='candidate':
   assert abs(out['target_xyz'][0]-prev['target_xyz'][0])<1e-12
   moved=list(args[1]);moved[0]+=.001
   follow=s.update(args[0],moved,*args[2:],**kw);assert follow['mode']=='top_push'
   assert abs(follow['target_xyz'][0]-out['target_xyz'][0]-.001)<1e-10
   s._start_recontact(kw['tip'],'software_fixture');assert s.region_push_object_x is None
   s.top_mode='top_press';s.settled=2;s.load.filtered_n=2.;s.last_waypoint_xy=(out['target_xyz'][0]+.004,out['target_xyz'][1]);reset_expected=s.last_waypoint_xy[0]
   reacquire=s.update(*args,**kw);assert reacquire['mode']=='top_push' and abs(reacquire['target_xyz'][0]-reset_expected)<1e-10
 # Original protections must take priority over X following.
 for guard in ['tilt','lost_contact','position_release']:
  guarded={};guard_args=list(args);guard_kw=dict(kw)
  for label,state0 in states.items():
   state=copy.deepcopy(state0);state.top_mode='top_push';state.command=tuple(prev['target_xyz']);state.lost_contact_steps=2
   if guard=='tilt':guard_kw['quat']=(float(np.sin(.06/2)),0.,0.,float(np.cos(.06/2)))
   elif guard=='lost_contact':guard_kw['load_n']=0.
   else:
    moved=np.array(args[1],copy=True);moved[1]=.35 if side=='left' else -.35;guard_args[1]=moved
   guarded[label]=state.update(*guard_args,**guard_kw)
  assert guarded['parent']==guarded['candidate'],(t,guard)
  assert guarded['candidate']['mode']!='top_push',(t,guard)
 for state in states.values():state.selected_surface_local_xy=None
 default_outputs={label:state.update(*args,**kw) for label,state in states.items()}
 assert default_outputs['parent']==default_outputs['candidate']
 assert np.max(abs(np.asarray(outputs['parent']['target_xyz'])-r['target_xyz']))<1e-6,(t,'fixture does not reconstruct parent waypoint')
 a=np.asarray(outputs['candidate']['target_xyz']);b=np.asarray(prev['target_xyz']);assert abs(a[0]-b[0])<=.002000001 and abs(a[1]-b[1])<=.003000001
 assert abs(a[2]-outputs['parent']['target_xyz'][2])<1e-12
 records.append(dict(step=t,parent_command_delta_xy_m=(np.asarray(r['target_xyz'])-b)[:2].tolist(),candidate_command_delta_xy_m=(a-b)[:2].tolist(),z_unchanged=True,default_branch_exact_match=True,three_original_guard_outputs_exact_match=True,observed_1mm_object_translation_followed=True,recontact_anchor_recaptured=True,parent_recorded_waypoint_reconstructed=True,zero_load_12_steps_without_push=True,next_recorded_parent_load_n=by[t+1]['contact_load']['observed_vertical_load_n']))
assert len(records)==10
report=dict(passed=True,records=records,raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),helper_sha256=hashlib.sha256((stage/'region_top_contact.py').read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Ten actual press-to-push inputs with explicitly reconstructed state fixtures; parent waypoint matches raw log. Checks candidate preserves loaded press X preload, follows observed1mm X translation, recaptures per-bout anchor, default nonregion output exactly equal, original bounds/Z/load confirmation unchanged. No physical trajectory, sustained contact or task success claim.',training_ready=False)
(stage/('X_FOLLOW_CHECK_'+key.upper()+'.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
