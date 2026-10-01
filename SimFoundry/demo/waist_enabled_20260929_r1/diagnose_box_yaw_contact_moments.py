"""Observed active-hand/table yaw moments, no desired-yaw controller."""
from pathlib import Path
import json,hashlib,numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;ep=w/'rear_core_slice_groups_r1/case_840001/layout_840001_push_box_to_bin';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with np.load(ep/'trace.npz') as z:xyz=z['box'].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:yaw=np.unwrap(Rotation.from_quat(z['box']).as_euler('xyz')[:,2])
fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];rows=[]
for packet in packets:
 t=packet['after_action_step']
 if t+1>=len(xyz) or t not in fr:continue
 assert max(abs(np.array(packet['post_action_pose']['box'])-xyz[t+1]))<1e-6
 force={k:np.zeros(3) for k in ['active_hand','table','other']};torque={k:np.zeros(3) for k in force};counts={k:0 for k in force}
 for c in packet['parcel_contacts']:
  slots=[i for i,s in enumerate(c['shapes']) if '/parcel_box/' in s]
  if len(slots)!=1:continue
  f=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);k='active_hand' if any('right_wrist' in s for s in c['shapes']) else ('table' if any('/table/' in s or '/table_edge_wear/' in s for s in c['shapes']) else 'other');force[k]+=f;torque[k]+=np.cross(np.array(c['position_world'])-xyz[t+1],f);counts[k]+=1
 rows.append(dict(step=t,mode=fr[t]['mode'],yaw_deg=float(yaw[t]*180/np.pi),yaw_delta_deg=float((yaw[t+1]-yaw[t])*180/np.pi),object_delta_xy_mm=((xyz[t+1]-xyz[t])[:2]*1000).tolist(),force_on_object_N={k:v.tolist() for k,v in force.items()},moment_about_object_center_Nm={k:v.tolist() for k,v in torque.items()},contact_counts=counts))
summary=[]
for mode in ['rear_push','top_push','top_lift','top_press']:
 selected=[r for r in rows if r['mode']==mode];contact=[r for r in selected if r['contact_counts']['active_hand']]
 summary.append(dict(mode=mode,intervals=len(selected),active_hand_contact_intervals=len(contact),summed_yaw_delta_deg=sum(r['yaw_delta_deg'] for r in selected),median_contact_yaw_delta_deg=float(np.median([r['yaw_delta_deg'] for r in contact])) if contact else None,median_active_hand_yaw_moment_Nm=float(np.median([r['moment_about_object_center_Nm']['active_hand'][2] for r in contact])) if contact else None,median_table_yaw_moment_Nm=float(np.median([r['moment_about_object_center_Nm']['table'][2] for r in contact])) if contact else None))
report=dict(episode=ep.name,summary=summary,rows=rows,initial_yaw_deg=float(yaw[0]*180/np.pi),final_yaw_deg=float(yaw[-1]*180/np.pi),source_sha256={n:sha(ep/n) for n in ['trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']},checker_sha256=sha(Path(__file__)),training_ready=False,scope='Force and r-cross-force moment from last solved substep at actual postaction target center; actual orientation changes span full observation interval. Moments are not integrated impulses or causal action-response fits. Existing incidental yaw is not proof of controlled90deg rotation, safe in-place turn or a viable alternate route.')
p=ep/'YAW_CONTACT_MOMENT_DIAGNOSIS.json';assert not p.exists();p.write_text(json.dumps(report,indent=2));print(json.dumps(summary,indent=2))
