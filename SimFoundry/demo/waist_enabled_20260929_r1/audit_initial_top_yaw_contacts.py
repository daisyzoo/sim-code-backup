"""Aligned recorded contact moment arms and parcel yaw; correlation, not causal proof."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
run=Path(sys.argv[1]).resolve();results=[]
for ep in sorted(run.glob('case_*/layout_*')):
 if not (ep/'quality.json').exists():continue
 key,actor,side=('box','parcel_box','right') if 'push_box' in ep.name else ('mailer','mailer','left')
 fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']}
 with np.load(ep/'parcel_orientation.npz') as z:quats=z[key];yaw=np.unwrap(Rotation.from_quat(quats).as_euler('xyz')[:,2])
 records=[]
 for packet in json.loads((ep/'solved_contact_forces.json').read_text())['rows']:
  t=packet['after_action_step']+1
  if t not in fr or t>=len(yaw):continue
  row=fr[t]
  if row['mode'] not in ['top_press','top_push']:continue
  center=np.asarray(packet['post_action_pose'][key]);assert np.max(abs(center-np.asarray(row['observed_target'])))<1e-5
  normal=Rotation.from_quat(quats[t]).as_matrix()[:,2];force=np.zeros(3);moment=np.zeros(3);tablemoment=np.zeros(3);points=[];weights=[];couple_max=0.
  for c in packet['parcel_contacts']:
   slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
   if len(slots)!=1:continue
   f=np.asarray(c['force_world_N'])*(1 if slots[0]==1 else -1);lever=np.asarray(c['position_world'])-center;torque=np.cross(lever,f)
   if any(side+'_wrist' in s for s in c['shapes']):
    force+=f;moment+=torque;couple_max=max(couple_max,max(abs(x) for x in c.get('force_torque_contact',[0]*6)[3:]))
    weight=-float(f@normal)
    if weight>.05:points.append(c['position_world']);weights.append(weight)
   elif any('/table/' in s for s in c['shapes']):tablemoment+=torque
  if sum(weights)<=.3:continue
  cop=np.average(points,axis=0,weights=weights);lever=cop-center
  records.append(dict(frame=t,mode=row['mode'],feedback_stage=(row.get('clearance_feedback') or {}).get('stage'),yaw_rad=float(yaw[t]),delta_yaw_from_start_rad=float(yaw[t]-yaw[0]),hand_force_n=force.tolist(),hand_moment_arm_torque_nm=moment.tolist(),table_moment_arm_torque_nm=tablemoment.tolist(),intrinsic_contact_couple_max_nm=float(couple_max),cop_lever_xy_m=lever[:2].tolist(),reference_minus_cop_xy_m=(np.asarray(row['observed_support_xyz'])-cop)[:2].tolist(),normal_load_n=float(sum(weights))))
 summary=[]
 for phase in ['top_press','lateral_y','clearance_x']:
  selected=[r for r in records if (r['feedback_stage'] or r['mode'])==phase]
  if not selected:continue
  row=dict(phase=phase,samples=len(selected),positive_hand_yaw_moment_fraction=float(np.mean([r['hand_moment_arm_torque_nm'][2]>0 for r in selected])))
  for field in ['cop_lever_xy_m','hand_force_n','hand_moment_arm_torque_nm','table_moment_arm_torque_nm','reference_minus_cop_xy_m']:
   values=np.asarray([r[field] for r in selected]);row[field]={name:np.quantile(values,q,axis=0).tolist() for name,q in [('p10',.1),('median',.5),('p90',.9)]}
  summary.append(row)
 result=dict(episode=ep.name,summary=summary,records=records,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),force_sha256=hashlib.sha256((ep/'solved_contact_forces.json').read_bytes()).hexdigest(),initial_final_yaw_rad=[float(yaw[0]),float(yaw[-1])]);results.append(result)
 print(json.dumps(dict(episode=ep.name,initial_final_yaw=result['initial_final_yaw_rad'],summary=[dict(phase=x['phase'],samples=x['samples'],cop_median=x['cop_lever_xy_m']['median'],hand_force_median=x['hand_force_n']['median'],yaw_moment_median=x['hand_moment_arm_torque_nm']['median'][2],positive_fraction=x['positive_hand_yaw_moment_fraction']) for x in summary])),flush=True)
(run/'INITIAL_TOP_YAW_CONTACTS.json').write_text(json.dumps(dict(rows=results,scope='Solved last-substep packets matched to next pre-action pose/quaternion; hand/table r-cross-F about object center and normal-weighted COP. Not all-substep torque integral, no inference of unique friction mechanism, no counterfactual physical proof. Original controller and gates untouched.',training_ready=False),indent=2))
