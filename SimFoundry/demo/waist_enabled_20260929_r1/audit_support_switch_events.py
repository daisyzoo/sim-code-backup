"""Separate virtual support-vertex identity changes from actual rigid-hand motion."""
from pathlib import Path
import sys,json
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
run=Path(sys.argv[1]).resolve();rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';z=np.load(ep/'raw.npz');log=json.loads((ep/'frontal_bypass.json').read_text())['rows'];events=[]
 def pose(t):
  q=dict(zip(names,z['q'][t,12:23]));m=np.eye(4);m[:3,3]=[.08,0,.793]
  for name,orig,axis in chains[side]:
   m=m@orig
   if axis is not None:
    a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@a
  return m
 for old,cur in zip(log,log[1:]):
  if old.get('control_offset_local') is None or cur.get('control_offset_local') is None:continue
  a=np.array(old['control_offset_local']);b=np.array(cur['control_offset_local']);jump=float(np.linalg.norm(b-a))
  if jump<.003:continue
  t=cur['step'];m=pose(t);prev=pose(old['step']);normal=Rotation.from_quat(np.load(ep/'parcel_orientation.npz')[key][t]).as_matrix()[:,2]
  events.append(dict(step=t,previous_mode=old['mode'],mode=cur['mode'],virtual_vertex_change_m=jump,identity_change_world_m=(m[:3,:3]@(b-a)).tolist(),old_vertex_height_above_new_support_m=float(normal@(m[:3,:3]@(a-b))),same_old_point_physical_motion_m=float(np.linalg.norm((m[:3,:3]@a+m[:3,3])-(prev[:3,:3]@a+prev[:3,3]))),hand_origin_motion_m=float(np.linalg.norm(m[:3,3]-prev[:3,3])),waypoint_change_m=float(np.linalg.norm(np.array(cur['target_xyz'])-old['target_xyz'])),action_step_max_rad=float(np.max(abs(z['action'][t,12:23]-z['action'][t-1,12:23]))),load_n=cur.get('contact_load',{}).get('observed_vertical_load_n'),following_modes=[r['mode'] for r in log if t<=r['step']<t+5]))
 rows.append(dict(episode=ep.name,events_over_3mm=sorted(events,key=lambda e:-e['virtual_vertex_change_m'])))
out=dict(rows=rows,scope='Pre-action actual FK; virtual support change separated from rigid motion. Close-in-height vertices can be far apart tangentially. Temporal association is not causal proof. No source/controller modifications.',training_ready=False)
(run/'SUPPORT_SWITCH_EVENTS.json').write_text(json.dumps(out,indent=2))
for r in rows:print(r['episode'],'events',len(r['events_over_3mm']),'largest',r['events_over_3mm'][:4])
