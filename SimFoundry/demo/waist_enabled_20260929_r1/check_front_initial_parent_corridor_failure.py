"""Independently reconstruct measured parent corridor collapse, not new physics.
Recorded parcel_orientation arrays are XYZW, verified against initial plan radii;
no quaternion permutation based on a runtime attribute's name is permitted.
All original dimensions, margins, and failed outcomes are retained.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;B=W/'front_initial_margin_baseline_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
records=[];sources={str(Path(__file__)):sha(__file__)}
for seed,task,target,other in [(840023,'nudge_mailer_to_bin','mailer','box'),(840020,'push_box_to_bin','box','mailer')]:
 ep=B/f'case_{seed}'/f'layout_{seed}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];rows=fr['rows'];quality=json.loads((ep/'quality.json').read_text());assert not quality['passed'] and quality['frames']==1200
 with np.load(ep/'parcel_orientation.npz') as z:quat={k:z[k].copy() for k in z.files}
 with np.load(ep/'trace.npz') as z:trace={k:z[k].copy() for k in z.files}
 size={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])};mat={k:Rotation.from_quat(quat[k]).as_matrix() for k in size};radius={k:abs(mat[k])@size[k]/2 for k in size}
 np.testing.assert_allclose(radius[target][0,:2],plan['front_route_candidates']['target_radii_xy'],atol=1e-10,rtol=0)
 np.testing.assert_allclose(radius[other][0,:2],plan['front_route_candidates']['other_radii_xy'],atol=1e-10,rtol=0)
 first=rows[0]['step'];clear=plan['front_route_live_guards']['clearance_before_lateral_m'];assert clear==.012
 route_x=trace[other][first,0]-radius[other][first,0]-radius[target][first,0]-clear-.003
 goal=np.minimum(route_x,trace[other][:,0]-radius[other][:,0]-radius[target][:,0]-clear-.003);margin=goal-radius[target][:,0]-.28
 # Check all emitted ordinary route goals and their observation alignment.
 checked=[]
 for row in rows:
  t=row['step'];np.testing.assert_allclose(trace[target][t],row['observed_target'],atol=1e-10,rtol=0)
  if 'route_goal_x' in row:assert abs(row['route_goal_x']-goal[t])<1e-10;checked.append(t)
 actual=next(row for row in rows if row['mode']=='front_guard_lift');stop=actual['step'];assert actual['route_stop_reason']=='front_corridor_no_table_margin'
 assert next(t for t in range(first,len(margin)) if margin[t]<.005)==stop
 assert all(row['route_stop_reason']=='front_corridor_no_table_margin' for row in rows if row['step']>=stop)
 yaw=np.rad2deg(np.unwrap(Rotation.from_quat(quat[target]).as_euler('xyz')[:,2]));samples=[]
 for t in [first,stop-1,stop,1199]:
  samples.append(dict(step=t,table_margin_mm=float(margin[t]*1000),target_x_radius_mm=float(radius[target][t,0]*1000),target_yaw_deg=float(yaw[t]),goal_x_m=float(goal[t]),current_target_table_margin_mm=float((trace[target][t,0]-radius[target][t,0]-.28)*1000)))
 r=dict(episode=ep.name,original_task_passed=False,first_guard_step=stop,guard_frames=sum(row['mode']=='front_guard_lift' for row in rows),ordinary_route_goals_verified=len(checked),initial_margin_surplus_mm=float((margin[first]-.005)*1000),yaw_change_at_guard_deg=float(yaw[stop]-yaw[first]),target_final_progress_mm=quality['metrics']['target_final_progress_m']*1000,non_target_whole_episode_max_xy_mm=float(np.linalg.norm(trace[other][:,:2]-trace[other][0,:2],axis=1).max()*1000),samples=samples,interpretation='Guard is for future planned front corridor, not evidence the current parcel has crossed the table edge. Small/large measured footprint expansion exhausts existing reserve; guard latches for the remaining episode. Centered landing benefit remains an unverified intervention.')
 records.append(r)
 for name in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','quality.json','ACTUAL_REVIEW_BINDING.json']:
  sources[str(ep/name)]=sha(ep/name)
 for path in [W/'staged_terminal_release_margin/front_top_route_micro.py',B/'PROTOCOL.json']:sources[str(path)]=sha(path)
report=dict(status='complete',passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256=sources,training_ready=False,new_physical_trial=False,controller_modified=False)
p=W/'FRONT_INITIAL_PARENT_CORRIDOR_FAILURE.json';assert not p.exists();p.write_text(json.dumps(report,indent=2));print(json.dumps(records,indent=2))
