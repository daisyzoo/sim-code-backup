"""Re-derive live front guard geometry and compare explicit static margins."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
p=Path(sys.argv[1]).resolve();tr=np.load(p/'trace.npz');ori=np.load(p/'parcel_orientation.npz');j=json.loads((p/'frontal_bypass.json').read_text());log=j['rows'];stop=next(r for r in log if r.get('route_stop_reason'));side='right' if 'push_box' in p.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);osize=np.array([.15,.145,.04] if key=='box' else [.14,.09,.045]);yaw=np.unwrap(Rotation.from_quat(ori[key]).as_euler('xyz')[:,2]);initial=tr[key][0];obstacle0=tr[other][0];configured_clearance=float(j['plan'].get('front_route_live_guards',{}).get('clearance_before_lateral_m',.02))
def radii(q,s):return abs(Rotation.from_quat(q).as_matrix())@s/2
r0=radii(ori[key][0],size);or0=radii(ori[other][0],osize);records=[]
for t in sorted(set([0,39,99,103,110,120,124,max(0,stop['step']-30),max(0,stop['step']-10),max(0,stop['step']-1),stop['step'],min(len(tr[key])-1,stop['step']+1),len(tr[key])-1])):
 target=tr[key][t];obstacle=tr[other][t];r=radii(ori[key][t],size);ro=radii(ori[other][t],osize);alternatives=[]
 for margin in sorted(set([.020,.012,configured_clearance])):
  initial_goal=min(initial[0],obstacle0[0]-r0[0]-or0[0]-margin)-.003
  goal=min(initial_goal,obstacle[0]-r[0]-ro[0]-margin-.003)
  alternatives.append(dict(is_recorded_configuration=margin==configured_clearance,planned_object_clearance_m=margin,front_goal_x_m=float(goal),planned_table_margin_m=float(goal-r[0]-.28),table_guard_5mm_pass=bool(goal-r[0]>=.285)))
 records.append(dict(step=t,yaw_deg=float(np.rad2deg(yaw[t])),target_xyz=target.tolist(),actual_visual_x_radius_m=float(r[0]),actual_front_table_margin_m=float(target[0]-r[0]-.28),actual_front_object_axis_gap_m=float(obstacle[0]-target[0]-r[0]-ro[0]),alternatives=alternatives))
forces=json.loads((p/'solved_contact_forces.json').read_text())['rows'];contacts=[];actor='parcel_box' if key=='box' else 'mailer';modes={r['step']:r['mode'] for r in log}
for packet in forces:
 t=packet['after_action_step']
 if t>=stop['step'] or modes.get(t)!='top_push':continue
 for c in packet['parcel_contacts']:
  slots=[i for i,v in enumerate(c['shapes']) if '/'+actor+'/' in v]
  if len(slots)!=1 or not any(side+'_wrist' in v for v in c['shapes']):continue
  f=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1)
  if abs(f[2])<.1:continue
  pose_frame=min(t+1,len(tr[key])-1);lever=np.array(c['position_world'])-tr[key][pose_frame];torque=np.cross(lever,f)
  contacts.append(dict(after_action_step=t,contact_lever_world_m=lever.tolist(),force_on_target_world_n=f.tolist(),torque_about_target_com_Nm=torque.tolist()))
out=dict(configured_clearance_m=configured_clearance,raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),frontal_sha256=hashlib.sha256((p/'frontal_bypass.json').read_bytes()).hexdigest(),first_guard_step=stop['step'],reason=stop['route_stop_reason'],records=records,top_push_contacts=contacts,training_ready=False,scope='Measured visual envelopes/poses; configured clearance is read from frozen plan metadata and marked in alternatives. Other margins are static alternatives only. Three-mm extra lead and5mm table guard retained. Static alternative does not prove dynamic clearance or success, change existing gates, alter parcels, or justify training. Contact torque from recorded last tick with next preaction COM, not full-substep integrated impulse.')
(p/'FRONT_GUARD_GEOMETRY.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['top_push_contacts','scope']},indent=2))
if contacts:print('forceweighted mean contact lever',np.average([v['contact_lever_world_m'] for v in contacts],axis=0,weights=[abs(v['force_on_target_world_n'][2]) for v in contacts]).tolist(),'contacts',len(contacts))
