"""Hypothetical rear-top path screening; CPU only, no dynamics or raw edits."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
root=Path(__file__).resolve().parent
source=(root/'audit_front_contact_fraction_kinematics.py').read_text()
exec(compile(source.split('actual=next(r for r in rows')[0],'<measured_approach_fk>','exec'))
from simfoundry.data.hand_obstacle_clearance import ConvexFaceSeparation
other_quat=ori[other_key][start];other_size=np.array([.14,.09,.045] if side=='left' else [.15,.145,.04]);other_radius=(abs(Rotation.from_quat(other_quat).as_matrix())@other_size/2)[0]
yaw_radius=float(np.linalg.norm(size[:2]/2));rear_base=float(obstacle[0]+other_radius+yaw_radius+.012+.003)
direction=log['plan']['direction'];goal_y=direction*max(.205,direction*log['plan']['initial_target_xyz'][1]+.16)
separation=ConvexFaceSeparation(vertices);results=[]
for extra in [0.,.02]:
 rear_x=rear_base+extra
 for fraction in [None,1.]:
  q=initial.copy();waypoints=[]
  for x in np.linspace(target[0],rear_x,max(2,int(np.ceil(abs(rear_x-target[0])/.02))+1)):waypoints.append([x,target[1],target[2]])
  for y in np.linspace(target[1],goal_y,max(2,int(np.ceil(abs(goal_y-target[1])/.02))+1))[1:]:waypoints.append([rear_x,y,target[2]])
  records=[];minimum_gap=float('inf');minimum_table=float('inf');first_failure=None
  for index,center in enumerate(waypoints):
   center=np.asarray(center);surface=np.array(top_surface_point(center,quat,size,front_inset_fraction=fraction));desired=surface+normal*.002
   all_gaps=[]
   for step in range(180):
    m,jl,jw=fk(side,q);rotation=m[:3,:3];ref=projected_support_reference(vertices,rotation,normal);point=m[:3,3]+rotation@ref['reference_local'];ja=projected_support_jacobian(jl,jw,rotation,ref)
    mi,jli,jwi=fk(other_side,q);po=np.array([.20,0,.007]);pi=mi[:3,3]+mi[:3,:3]@po;ji=jli-skew(mi[:3,:3]@po)@jwi
    error=desired-point;inactive_error=anchor-pi
    gap=separation.gap(m[:3,3],Rotation.from_matrix(rotation).as_quat(),obstacle,other_quat,other_size);all_gaps.append(gap)
    hand_vertices=m[:3,3]+vertices@rotation.T;minimum_table=min(minimum_table,float(hand_vertices[:,2].min()-.75))
    if np.max(abs(error[:2]))<.01 and abs(error[2])<.008 and np.max(abs(inactive_error))<.015:break
    jac=np.vstack([ja,ji]);err=np.r_[np.clip(.72*error,-.035,.035),np.clip(.72*inactive_error,-.035,.035)]
    q+=bounded_damped_step(jac,err,q,lo,hi,limits,damping)
   reached=bool(np.max(abs(error[:2]))<.01 and abs(error[2])<.008 and np.max(abs(inactive_error))<.015)
   minimum_gap=min(minimum_gap,min(all_gaps));heights=vertices@(rotation.T@normal);near=vertices[heights-heights.min()<=.0002];local=((m[:3,3]+near@rotation.T)-center)@rp;scale=np.array([.96,.96] if side=='right' else [.90,.88]);core_margin=float(np.min(size[:2]*scale/2-np.abs(local[:,:2])))
   records.append(dict(waypoint_index=index,hypothetical_target_xyz=center.tolist(),desired_reference_xyz=desired.tolist(),reached=reached,ik_steps=step+1,active_error_xyz_m=error.tolist(),inactive_error_xyz_m=inactive_error.tolist(),waist_yaw_rad=float(q[0]),min_hand_other_face_gap_during_ik_m=min(all_gaps),last_hand_other_face_gap_m=gap,near_support_core_margin_m=core_margin,q=q.tolist()))
   if not reached:first_failure=index;break
  result=dict(extra_rear_m=extra,front_inset_fraction=fraction,rear_x=rear_x,worst_flat_yaw_target_table_margin_m=.88-rear_x-yaw_radius,all_waypoints_reached=first_failure is None,first_failure=first_failure,checked_waypoints=len(records),total_waypoints=len(waypoints),min_hand_other_face_gap_m=minimum_gap,min_hand_vertex_z_above_table_m=minimum_table,records=records);results.append(result)
  print(json.dumps({k:v for k,v in result.items() if k!='records'}),flush=True)
out=dict(variants=results,start_actual_frame=start,raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),helper_sha256=hashlib.sha256(source.encode()).hexdigest(),scope='Hypothetical parcel centers sampled along back-then-side path, actual initial recorded q/inactive anchor, fixed target yaw. Each IK joint command is applied immediately in CPU kinematics. No simulation, object actuation, forces, loaded contact, swept full-arm collision or visibility validation. Positive hand face gap certifies only sampled hand/other separation; table Z diagnostic not full robot safety. Reached pose does not prove physical push feasibility. No raw data modified or training admission.',training_ready=False)
(p/'REAR_TOP_PATH_KINEMATICS.json').write_text(json.dumps(out,indent=2))
