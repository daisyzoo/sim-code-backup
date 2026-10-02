"""Read-only actual plan->handover->contact transfer and missed recovery windows.
No planner threshold, controller, data admission or force integration changes.
"""
from pathlib import Path
import sys,json,hashlib,datetime,collections
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_box_center_preference';sys.path[:0]=[str(stage),str(w),str(repo)]
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage)
ep=w/'box_center_groups_r1/case_840001/layout_840001_push_box_to_bin'
es=json.loads((ep/'recontact_pose.json').read_text())['rows'];fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];fs={x['step']:x for x in fr}
with np.load(ep/'trace.npz') as z:xyz=z['box'].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z['box']).as_matrix()
packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];contact={}
for pkt in packets:
 t=pkt['after_action_step']+1
 if t>=len(xyz):continue
 assert pkt['solver_force_buffer_unchanged'] and np.max(abs(np.array(pkt['post_action_pose']['box'])-xyz[t]))<1e-6
 total=0.;point=np.zeros(3)
 for c in pkt['parcel_contacts']:
  slots=[i for i,n in enumerate(c['shapes']) if '/parcel_box/' in n]
  if not slots or not any('right_wrist' in n for n in c['shapes']):continue
  assert len(slots)==1
  force=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1)
  load=-float(force@R[t,:,2])
  if load>.05:total+=load;point+=load*(R[t].T@(np.array(c['position_world'])-xyz[t]))
 if total>=.3:contact[t]=dict(step=t,normal_load_n=total,cop_local_mm=(point/total*1000).tolist(),radius_mm=float(np.linalg.norm(point[:2]/total)*1000))
recoveries=[]
for n in sorted(set(e['context']['recontacts'] for e in es if e['context']['recontacts']>0)):
 events=[e for e in es if e['context']['recontacts']==n];plans=[e for e in events if e.get('planning')];handovers=[e for e in events if e['kind']=='handover'];blocked=[e for e in events if e.get('reason')=='initial_hand_below_unloaded_planning_height'];heights=[]
 for e in blocked:
  T=np.array(e['context']['observed_hand_pose']);heights.append(float(np.min((guard.model.vertices['right']@T[:3,:3].T+T[:3,3])[:,2])))
 row=dict(recontact=n,start_step=events[0]['step'],end_step=events[-1]['step'],height_blocked_frames=len(blocked),blocked_lowest_hand_z_range_m=[min(heights),max(heights)] if heights else None,plans=[],handovers=[])
 for e in plans:
  p=e['planning'];m=p['box_center_preference_pose'];old=m['parent_plan']['minimum_motion_pose'];a=np.array(old['selected_path_checks'][-1]['contact_object_local']);b=np.array(m['selected_path_checks'][-1]['contact_object_local']);row['plans'].append(dict(step=e['step'],selected=m['selected'],old_endpoint_xy_mm=(a[:2]*1000).tolist(),new_endpoint_xy_mm=(b[:2]*1000).tolist(),old_radius_mm=float(np.linalg.norm(a[:2])*1000),new_radius_mm=float(np.linalg.norm(b[:2])*1000),old_waypoints=len(m['parent_plan']['waypoints']),new_waypoints=len(p['waypoints'])))
 for e in handovers:
  later=[t for t in range(e['step'],events[-1]['step']+1) if t in contact and t in fs and fs[t]['mode']=='top_push'];row['handovers'].append(dict(step=e['step'],measured_selected_xy_mm=(np.array(e['selected_surface_local_xy'])*1000).tolist(),first_loaded=contact[later[0]] if later else None,last_loaded=contact[later[-1]] if later else None,loaded_push_frames=len(later)))
 recoveries.append(row)
sources={str(ep/n):sha(ep/n) for n in ['recontact_pose.json','frontal_bypass.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json']}
for p in [Path(__file__),stage/'clearance_runtime.py',stage/'minimum_motion_lifecycle.py',repo/'assets/robots/g1_hand_support_vertices.json']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,recoveries=recoveries,original_start_height_m=.84,source_sha256=sources,limitations=['COP from final contact substep, not whole-frame force integral.','Planned lowest vertex is not identical to future contact COP.','Recorded rejected-height windows do not prove a different policy can safely reach the threshold.'],training_ready=False)
(ep.parent.parent/'LANDING_TRANSFER_DIAGNOSTIC.json').write_text(json.dumps(out,indent=2));print(json.dumps(recoveries,indent=2))
