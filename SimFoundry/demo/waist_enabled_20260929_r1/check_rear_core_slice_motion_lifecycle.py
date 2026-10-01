"""Default stream parity and enabled one-step parent guard integration."""
from pathlib import Path
import ast,copy,hashlib,json,sys,importlib.util
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1]
stage=w/'staged_rear_core_slice_motion';parent=w/'staged_region_measured_bounds'
sys.path[:0]=[str(stage),str(parent),str(repo)]
from rear_cop_route import RearCopRouteState
spec=importlib.util.spec_from_file_location('old_rear_wrapper',w/'staged_rear_cop_core_slice/rear_cop_route.py');oldmod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=oldmod;spec.loader.exec_module(oldmod)
from region_top_contact import TopContactBypassState
from simfoundry.data.frontal_bypass import FrontalBypassState
from simfoundry.data.contact_load_control import hand_target_vertical_load
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
encode=lambda obj:json.dumps(obj,sort_keys=True,default=lambda v:v.tolist() if isinstance(v,np.ndarray) else float(v))
rows=[]
for run in ['region_continuity_groups_r1','region_causal_response_groups_r1','region_causal_xy_groups_r2','region_measured_bounds_groups_r1','rear_cop_measured_bounds_groups_r1','rear_core_slice_groups_r1']:
 for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan']
  side='right' if task=='push_box_to_bin' else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';actor='parcel_box' if key=='box' else 'mailer';size=tuple(plan['top_recontact']['contact_size_xyz'])
  def make(cls):
   s=cls(FrontalBypassState(plan,staging_z=.92,press_z=.822,feedback_rear_endpoint=True,follow_target_y=True),side,size,guarded_descent=True,continuous_drag=True,alignment_tolerance_m=.01,tilt_recontact_rad=.03,confirm_terminal_release=True,hold_established_x=True)
   s.load.desired_n=5.;return s
  baseline=make(oldmod.RearCopRouteState);default=make(RearCopRouteState)
  with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
  with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
  packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};region={r['step']:r for r in json.loads((ep/'region_approach.json').read_text())['rows']}
  config=ep.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';node=next(n for n in ast.walk(ast.parse(config.read_text())) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='core_scale' for x in n.targets));scale=np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body))
  for state in [baseline,default]:state.rear_core_slice_enabled=True;state.rear_cop_enabled=True;state.rear_cop_core_size=np.array(size)*scale
  probe_state=None;overrides=nonpush=first_preserved=0
  for record in fr['rows']:
   t=record['step'];packet=packets.get(t-1);load=hand_target_vertical_load(packet,side,actor)
   kw=dict(tip=record['observed_support_xyz'],quat=ori[key][t],control_offset_local=record.get('observed_support_offset_local') or record.get('control_offset_local') or (.2,0,.007),load_n=load,hand_obstacle_gap_m=record.get('hand_obstacle_gap_m'))
   args=(tr['palm_'+side][t],tr[key][t],tr[other][t],plan['target_radius_x'],plan['obstacle_radius_x'])
   enabled=copy.deepcopy(default);enabled.rear_core_slice_motion_enabled=True;enabled.rear_core_slice_enabled=True;enabled.rear_cop_enabled=True;enabled.rear_cop_core_size=np.array(size)*scale
   if probe_state is not None:enabled.rear_cop=copy.deepcopy(probe_state)
   contact=loaded_forward_margin(packet,side,actor,tr[key][t],ori[key][t],size,-1 if side=='right' else 1)
   parent_probe=copy.deepcopy(default);parent_row=TopContactBypassState.update(parent_probe,*args,**kw)
   a=baseline.update(*args,**kw,slip_contact=contact);b=default.update(*args,**kw,slip_contact=contact);assert encode(a)==encode(b),(run,task,t)
   c=enabled.update(*args,**kw,slip_contact=contact);feedback=c.pop('rear_cop_centering');probe_state=enabled.rear_cop
   assert c['mode']==a['mode'] and np.array_equal(np.array(c['target_xyz'])[1:],np.array(parent_row['target_xyz'])[1:])
   if feedback['override']:
    overrides+=1;assert a['mode']=='top_push' and enabled.selected_surface_local_xy is not None
    assert enabled.command==tuple(c['target_xyz']) and enabled.last_waypoint_xy==tuple(c['target_xyz'][:2])
   else:
    assert encode(c)==encode(parent_row);nonpush+=a['mode']!='top_push';first_preserved+=feedback['reason']=='preserve_first_loaded_push'
   # Recorded hook applied to both default streams; enabled steps do not feed
   # synthetic state into subsequent real observations.
   r=region.get(t);solver=r.get('solver') if r else None
   if solver and solver.get('handover'):
    for s in [baseline,default]:
     s.selected_surface_local_xy=tuple(solver['selected_surface_local_xy']);s.top_mode='top_press';s.mode='top_press';s.mode_step=1;s.settled=0;s.command=None;s.push_x_anchor=None;s.approach_xy_bias=[0.,0.];s.descent_z=float(kw['tip'][2]);s.load.bias_m=0.
  rows.append(dict(run=run,episode=ep.name,default_exact_frames=len(fr['rows']),one_step_overrides=overrides,nonpush_unchanged=nonpush,first_loaded_transition_preserved=first_preserved,source_sha256={f:sha(ep/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','region_approach.json','solved_contact_forces.json']},collision_source_sha256=sha(config)))

# Real parent code, synthetic stimuli for three existing guard transitions.
s=make(RearCopRouteState);s.rear_core_slice_motion_enabled=True;s.rear_core_slice_enabled=True;s.rear_cop_enabled=True;s.rear_cop_core_size=np.array(size)*scale;s.selected_surface_local_xy=(0.,0.);s.top_mode='top_push';s.command=(.5,0.,.79);s.last_waypoint_xy=(.5,0.);s.push_x_anchor=.5;s.rear.plan=copy.deepcopy(plan);s.rear.plan['initial_target_xyz']=[.5,0.,.77];s.rear.plan['direction']=1
base_args=([.5,0.,.79],[.5,0.,.77],[.7,-.3,.77],.075,.075)
base_kw=dict(tip=[.5,0.,.79],quat=[0,0,0,1],control_offset_local=[.2,0,.007],load_n=5.,hand_obstacle_gap_m=.1,slip_contact=dict(valid=True,weighted_contact_local=[0,0,.02],normal_load_n=5.))
guards=[]
for kind in ['tilt','lost_contact','release']:
 test=copy.deepcopy(s);args=list(base_args);kw=copy.deepcopy(base_kw)
 if kind=='tilt':kw['quat']=Rotation.from_euler('x',.04).as_quat()
 if kind=='lost_contact':test.lost_contact_steps=2;kw['load_n']=0.;kw['slip_contact']=None
 if kind=='release':args[1]=[.5,.25,.77]
 out=test.update(*args,**kw);assert out['mode'] in ['top_lift','top_release'] and not out['rear_cop_centering']['override'],(kind,out)
 guards.append(dict(kind=kind,mode=out['mode'],feedback=out['rear_cop_centering']))
report=dict(passed=True,rows=rows,guard_stimuli=guards,total_default_exact_frames=sum(r['default_exact_frames'] for r in rows),total_one_step_overrides=sum(r['one_step_overrides'] for r in rows),source_sha256={str(p):sha(p) for p in [stage/'rear_cop_route.py',stage/'rear_cop_centering.py',parent/'region_top_contact.py']},checker_sha256=sha(Path(__file__)),collector_wired=False,physical_started=False,training_ready=False,scope='Twelve recorded-input rearCOP/core-slice enabled, motion-feedforward off default streams with recorded handover injection; enabled one-step comparisons from identical parent prior states. Parent Y/Z and nonpush guards preserved. Not full collector wiring, a physics forecast or sorting success.')
(stage/'LIFECYCLE_CHECK.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['rows','source_sha256']}))
