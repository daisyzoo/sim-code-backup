"""Measured hand wrench lever and current-geometry zero-yaw-moment line.
Translating all measured contact forces by the computed offset cancels sampled
Z moment algebraically. Real contact forces will change; this is not a predicted
motion, executable contact command, causal intervention or data admission.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();reports=[]
for run in ['joint_edge_retry_groups_r1','self_clearance_groups_r1','front_direction_recontact_groups_r1']:
 for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}'
  if not (ep/'quality.json').exists():continue
  fr=json.loads((ep/'frontal_bypass.json').read_text());side='right' if 'push_box' in task else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if side=='right' else 'mailer'
  assert fr['plan']['front_route_selected'];core=np.array(fr['plan']['front_cop_slip_following']['edge_speed']['actual_core_size_xyz']);half=core[:2]/2-.01
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
  packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};records=[]
  for row in fr['rows']:
   if row['mode']!='top_push':continue
   t=row['step'];packet=packets[t-1];assert np.max(abs(np.array(packet['post_action_pose'][key])-xyz[t]))<1e-6
   force=np.zeros(3);moment=np.zeros(3);points=[];weights=[];forces=[]
   for c in packet['parcel_contacts']:
    slots=[i for i,label in enumerate(c['shapes']) if '/'+actor+'/' in label]
    if len(slots)!=1 or not any(side+'_wrist' in label for label in c['shapes']):continue
    f=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);p=np.array(c['position_world']);force+=f;moment+=np.cross(p-xyz[t],f);points.append(p);forces.append(f);weights.append(max(0.,-float(f@rot[t,:,2])))
   if sum(weights)<.3 or np.linalg.norm(force[:2])<.5:continue
   cop=np.average(points,axis=0,weights=weights);local=rot[t].T@(cop-xyz[t]);stage=row['route_stage'];axis=0 if stage=='front_x' else 1;cross=1-axis;derivative=force[1] if cross==0 else -force[0]
   if abs(derivative)<.5:continue
   shift=-moment[2]/derivative;offset=np.zeros(3);offset[cross]=shift;predicted_cop=cop+offset;newlocal=rot[t].T@(predicted_cop-xyz[t]);residual=sum(np.cross(p+offset-xyz[t],f)[2] for p,f in zip(points,forces));assert abs(residual)<1e-12
   feedback=row.get('cop_slip_following',{});route=feedback.get('route_axis_control');reference=np.array(row['observed_support_xyz']);goal=np.array(row['target_xyz']);records.append(dict(step=t,stage=stage,force_N=force.tolist(),moment_z_Nm=float(moment[2]),yaw_lever_mm=float(moment[2]/np.linalg.norm(force[:2])*1000),current_cop_local_mm=(local*1000).tolist(),cross_axis=cross,algebraic_shift_mm=float(shift*1000),shifted_cop_local_mm=(newlocal*1000).tolist(),shifted_center_inside_core10mm=bool(np.all(abs(newlocal[:2])<=half)),algebraic_moment_residual_Nm=float(residual),virtual_reference_to_cop_mm=((cop-reference)*1000).tolist(),emitted_cross_reference_lead_mm=float((goal[cross]-reference[cross])*1000),original_cop_cross_correction_discarded=bool(route is not None)))
  groups=[]
  for stage in ['front_x','lateral_y']:
   rs=[x for x in records if x['stage']==stage]
   if not rs:continue
   groups.append(dict(stage=stage,loaded_frames=len(rs),median_moment_z_Nm=float(np.median([x['moment_z_Nm'] for x in rs])),negative_moment_frames=sum(x['moment_z_Nm']<0 for x in rs),median_abs_lever_mm=float(np.median([abs(x['yaw_lever_mm']) for x in rs])),median_required_cross_shift_mm=float(np.median([x['algebraic_shift_mm'] for x in rs])),shift_inside_core10mm_frames=sum(x['shifted_center_inside_core10mm'] for x in rs),median_virtual_to_cop_mm=np.median([x['virtual_reference_to_cop_mm'] for x in rs],axis=0).tolist(),median_cross_reference_lead_mm=float(np.median([x['emitted_cross_reference_lead_mm'] for x in rs]))))
  reports.append(dict(episode=str(ep),core_xyz_m=core.tolist(),groups=groups,records=records,source_sha256={n:sha(ep/n) for n in ['frontal_bypass.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json']}));print(run,task,json.dumps(groups),flush=True)
out=dict(scope=__doc__,episodes=reports,diagnostic_sha256=sha(__file__),training_ready=False);(w/'FRONT_WRENCH_LINE_DIAGNOSIS.json').write_text(json.dumps(out,indent=2))
