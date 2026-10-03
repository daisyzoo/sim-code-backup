"""One-step1mm COP proposals on historical measured states and arithmetic budget.
No replacement trajectory, predicted contact force, or physical improvement.
The runtime collector and every original guard remain unchanged.
"""
from pathlib import Path
import json,hashlib,datetime,sys,math
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;S=W/'staged_front_corridor_midpoint_integrated';R=W/'front_corridor_midpoint_physical_r1';sys.path.insert(0,str(S))
from contact_slip_following import CopSlipFollowing
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};results=[]
for ep in sorted(R.glob('case_*/layout_*')):
 p=ep/'frontal_bypass.json'
 if not p.exists():continue
 fr=json.loads(p.read_text());plan=fr['plan']
 if not plan.get('front_route_selected'):continue
 key='box' if plan['direction']==-1 else 'mailer';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04])
 with np.load(ep/'trace.npz') as z:xyz=z[key].copy()
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
 proposals=[]
 for row in fr['rows']:
  f=row.get('cop_slip_following',{})
  if not f.get('override'):continue
  t=row['step'];assert row['mode']=='top_push';ob=xyz[t];rr=rot[t];anchor=np.asarray(f['anchor_local']);local=np.asarray(f['measured_cop_local']);world=ob+rr@anchor;cop=ob+rr@local;feed=np.asarray(f['object_anchor_translation_xy']);prev=np.asarray(f['previous_command_xy']);ref=np.asarray(f['reference_xy'])
  goal_y=row.get('front_diagonal_entry',{}).get('goal_y',row['clearance_progress']['front_hold_y'] if row['route_stage']=='front_x' else plan['front_route_candidates']['goal_y'])
  goal=[row['route_goal_x'],goal_y]
  def call(step):
   c=CopSlipFollowing(local_anchor=anchor.copy(),previous_anchor_world=np.r_[world[:2]-feed,world[2]])
   return c.update(mode='top_push',object_xyz=ob,object_rotation=rr,object_size=size,goal_xy=goal,reference_xy=ref,previous_command_xy=prev,cop_world=cop,normal_load_n=1.,drive_step_m=step)
  # Geometry/command probe only. Unit load is explicit valid-COP branch input;
  # it is NOT a reconstructed measured force or evidence of real contact.
  parent=call(f['edge_speed']['drive_step_m'])
  for name in ['command_xy','drive_xy','slip_correction_xy','object_anchor_translation_xy']:np.testing.assert_allclose(parent[name],f[name],atol=2e-6,rtol=0)
  candidate=call(.001);xy=np.asarray(candidate['command_xy']);oldxy=np.asarray(row['target_xyz'][:2]);axis=f.get('route_axis_control',{}).get('active_axis')
  if axis is not None:xy[1-axis]=oldxy[1-axis]
  assert np.max(abs(xy-prev))<=.003+2e-12
  proposals.append(dict(step=t,stage=row['route_stage'],parent_drive_step_m=f['edge_speed']['drive_step_m'],candidate_drive_step_m=.001,parent_xy=oldxy.tolist(),candidate_unissued_xy=xy.tolist(),candidate_norm_delta_from_parent_m=float(np.linalg.norm(xy-oldxy)),original_z_unchanged=row['target_xyz'][2]))
 first=proposals[0]['step'];direction=plan['direction'];final_y=direction*max(.205,direction*xyz[1,1]+.16);need_y=direction*(final_y-xyz[first,1]);waypoints=next(c['waypoints_xy'] for c in plan['front_route_candidates']['candidates'] if c['route']=='front');length=float(sum(np.linalg.norm(np.array(b)-a) for a,b in zip(waypoints,waypoints[1:])))
 quality=json.loads((ep/'quality.json').read_text());results.append(dict(episode=ep.name,frames=len(xyz),first_loaded_override=first,remaining_action_slots=1200-first,old_loaded_override_frames=len(proposals),changed_single_step_proposals=sum(x['candidate_norm_delta_from_parent_m']>1e-12 for x in proposals),initial_fixed_orientation_route_length_m=length,one_to_one_motion_arithmetic_frames=math.ceil(length/.001),one_to_one_required_active_fraction=length/.001/(1200-first),initial_target_to_release_y_m=float(need_y),scope='One-to-one object/command arithmetic is not a physical lower bound, forecast, or sustained-contact proof. First-run route fixed-orientation geometry cannot establish future corridor feasibility.',proposals=proposals))
 for f in [p,ep/'trace.npz',ep/'parcel_orientation.npz',ep/'quality.json']:sources[str(f)]=sha(f)
for p in [Path(__file__),S/'contact_slip_following.py',S/'front_initial_center_cop_route.py',S/'front_edge_speed_direction.py']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,historical_unit_load_explicit=True,results=results,source_sha256=sources,physics_started=False,training_ready=False)
with (W/'FRONT_DRIVE_1MM_HISTORICAL_PROPOSAL_BUDGET.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps([{k:v for k,v in r.items() if k!='proposals'} for r in results],indent=2))
