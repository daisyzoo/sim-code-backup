"""Actual-state ideal-FK lifecycle checks, default replay and synthetic load gates."""
from pathlib import Path
import sys,json,copy,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_region_contact_x_follow';sys.path[:0]=[str(stage),str(repo)]
from region_top_contact import TopContactBypassState as CandidateState
from simfoundry.data.top_contact_bypass import TopContactBypassState,top_surface_point,local_surface_world
from simfoundry.data.frontal_bypass import FrontalBypassState
from simfoundry.data.projected_support_reference import projected_support_reference
from simfoundry.data.contact_load_control import hand_target_vertical_load
from articulated_hand_geometry import ArticulatedHandGeometry
from region_approach_lifecycle import RegionApproachLifecycle
import ast
bounds={}
for node in ast.parse((repo/'simfoundry/robots/g1_assets.py').read_text()).body:
 if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in ['U1_JOINT_LIMIT_LO','U1_JOINT_LIMIT_HI']:bounds[node.target.id]=np.array(ast.literal_eval(node.value))[12:]
lo=bounds['U1_JOINT_LIMIT_LO'];hi=bounds['U1_JOINT_LIMIT_HI'];lo[0]=-.98;hi[0]=.98;limits=np.full(11,.04);limits[0]=.015;damping=np.full(11,.045);damping[0]=.12
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
inputs=[(w/'contact_bout_yaw_groups_r1/case_898001/layout_898001_push_box_to_bin',117),(w/'fresh_diagonal_02_trial_v2_r1/case_840004/layout_840004_nudge_mailer_to_bin',100),(w/'fresh_lateral_00_trial_v2_r1/case_840001/layout_840001_push_box_to_bin',120)];reports=[]
for ep,t in inputs:
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';actor='parcel_box' if key=='box' else 'mailer';size=(.14,.09,.045) if key=='box' else (.15,.145,.04);other_size=(.15,.145,.04) if key=='box' else (.14,.09,.045)
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 log=json.loads((ep/'frontal_bypass.json').read_text());plan=log['plan'];packets={x['after_action_step']:x for x in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};coords={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};anchor=np.array(coords[t]['inactive_anchor'])
 def make(cls):
  state=cls(FrontalBypassState(plan,staging_z=.92,press_z=.822,feedback_rear_endpoint=True,follow_target_y=True),side,size,guarded_descent=True,continuous_drag=True,alignment_tolerance_m=.01,tilt_recontact_rad=.03,confirm_terminal_release=True,hold_established_x=True)
  state.load.desired_n=5.;return state
 # Compare original versus candidate-default state on every real recorded input.
 original,candidate=make(TopContactBypassState),make(CandidateState)
 for recorded in log['rows']:
  i=recorded['step'];load=hand_target_vertical_load(packets.get(i-1),side,actor);kw=dict(tip=recorded['observed_support_xyz'],quat=ori[key][i],control_offset_local=recorded.get('observed_support_offset_local') or recorded.get('control_offset_local') or (.2,0,.007),load_n=load,hand_obstacle_gap_m=recorded.get('hand_obstacle_gap_m'))
  a=original.update(tr['palm_'+side][i],tr[key][i],tr[other][i],plan['target_radius_x'],plan['obstacle_radius_x'],**kw);b=candidate.update(tr['palm_'+side][i],tr[key][i],tr[other][i],plan['target_radius_x'],plan['obstacle_radius_x'],**kw)
  def encode(x):return json.dumps(x,sort_keys=True,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else float(a))
  assert encode(a)==encode(b),(ep.name,i)
 state=make(CandidateState);state.top_mode='top_cross';life=RegionApproachLifecycle();q=qs[t].copy();target=tr[key][t].copy();obstacle=tr[other][t].copy();quat=ori[key][t].astype(float)
 def geometry(q):return model.scene_geometry(side,q,target_xyz=target,target_quat=quat,other_xyz=obstacle,other_quat=ori[other][t],other_size=other_size)
 history=[]
 for step in range(600):
  g=geometry(q);normal=g['target_rotation'][:,2];ref=projected_support_reference(g['vertices'],g['hand_rotation'],normal);tip=g['hand_xyz']+g['hand_rotation']@ref['reference_local']
  # One and only one parent update before the lifecycle hook.
  row=state.update(tip,target,obstacle,plan['target_radius_x'],plan['obstacle_radius_x'],tip=tip,quat=quat,control_offset_local=ref['reference_local'],load_n=0.,hand_obstacle_gap_m=g['hand_other_gap_m'])
  row,ref,result=life.update(row,state,ref,q=q,previous_command=q,geometry=geometry,lower=lo,upper=hi,step_limits=limits,damping=damping,inactive_anchor=anchor,normal_anchor=None,load_n=0.)
  assert result is not None and result.get('joint_override'),(ep.name,step,row)
  history.append(dict(step=step,mode=row['mode'],handover=result['handover'],max_joint_step_rad=float(np.max(abs(np.array(result['next_q'])-q)))))
  if result['handover']:
   assert np.array_equal(result['next_q'],q) and row['mode']=='top_press' and state.settled==0 and state.command is None
   assert np.linalg.norm(np.array(row['target_xyz'])-(g['hand_xyz']+g['hand_rotation']@ref['reference_local']))<1e-10
   break
  q=np.array(result['next_q'])
 else:raise AssertionError('No handover')
 selected=state.selected_surface_local_xy;tip=np.asarray(row['observed_support_xyz']);offset=ref['reference_local'];surface=local_surface_world(target,quat,(*selected,size[2]/2))
 assert np.max(abs(np.array(row['parcel_top_xyz'])-surface))<1e-10
 unloaded=copy.deepcopy(state)
 for _ in range(12):
  row0=unloaded.update(tip,target,obstacle,plan['target_radius_x'],plan['obstacle_radius_x'],tip=tip,quat=quat,control_offset_local=offset,load_n=0.,hand_obstacle_gap_m=g['hand_other_gap_m']);assert row0['mode']!='top_push'
 # Software-only load stimulus verifies existing confirmation; not measured physics.
 loaded=copy.deepcopy(state);modes=[]
 for _ in range(8):modes.append(loaded.update(tip,target,obstacle,plan['target_radius_x'],plan['obstacle_radius_x'],tip=tip,quat=quat,control_offset_local=offset,load_n=5.,hand_obstacle_gap_m=g['hand_other_gap_m'])['mode'])
 assert modes[:2]==['top_press','top_press'] and 'top_push' in modes
 loaded._start_recontact(tip,'software_fixture_lost_contact');assert loaded.selected_surface_local_xy==selected
 row1=loaded.update(tip,target,obstacle,plan['target_radius_x'],plan['obstacle_radius_x'],tip=tip,quat=quat,control_offset_local=offset,load_n=0.,hand_obstacle_gap_m=g['hand_other_gap_m']);assert np.max(abs(np.array(row1['parcel_top_xyz'])-surface))<1e-10
 for mode in ['top_release','front_guard_lift','initial_top_guard_lift']:
  fixture=RegionApproachLifecycle(active=True);guardrow=dict(row1,mode=mode);out,_,override=fixture.update(guardrow,copy.deepcopy(state),ref,q=q,previous_command=q,geometry=geometry,lower=lo,upper=hi,step_limits=limits,damping=damping,inactive_anchor=anchor,normal_anchor=None,load_n=0.);assert out==guardrow and override is None
 reports.append(dict(episode=ep.name,default_replay_frames=len(log['rows']),actual_start_frame=t,approach_steps=len(history),measured_q_hold_on_handover=True,selected_surface_local_xy=selected,zero_load_steps_without_push=12,synthetic_load_modes=modes,local_goal_preserved_on_recontact=True,original_guard_release_modes_preserved=3,history=history))
report=dict(rows=reports,source_sha256={f:hashlib.sha256((stage/f).read_bytes()).hexdigest() for f in ['region_top_contact.py','region_approach_lifecycle.py','contact_patch_approach.py','articulated_hand_geometry.py','collect_paired_sorting.py']},checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Actual raw-state FK approach and original/candidate-default replay; handover/load/guard tests use explicit software fixtures, NOT real pressing, full collector execution, collision proof or sorting success.',training_ready=False)
(stage/'LIFECYCLE_CHECK.json').write_text(json.dumps(report,indent=2));print(json.dumps([{k:v for k,v in row.items() if k!='history'} for row in reports],indent=2))
