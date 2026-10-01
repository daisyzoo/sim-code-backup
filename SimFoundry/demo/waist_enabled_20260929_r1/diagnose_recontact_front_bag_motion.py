"""Recorded front bag route commands, same-step hand material response, object motion.
Force samples are last physics tick, never integrated impulse or causal proof.
Both old and new whole episodes retained, no replay as synthetic demonstrations.
"""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(repo),str(w/'staged_self_clearance_task_ik')]
from articulated_hand_geometry import ArticulatedHandGeometry
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');reports=[]
for run in ['self_clearance_groups_r1','front_direction_recontact_groups_r1']:
 ep=w/run/'case_840001/layout_840001_nudge_mailer_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());rows={r['step']:r for r in fr['rows']};coord={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
 with np.load(ep/'trace.npz') as z:xyz=z['mailer'].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['mailer']).as_matrix();yaw=Rotation.from_quat(z['mailer']).as_euler('xyz')[:,2]
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);actions=z['action'][:,12:23].astype(float)
 frames=[]
 def contact(packet,R):
  force=np.zeros(3);moment=np.zeros(3);points=[];weights=[]
  for c in packet['parcel_contacts']:
   slots=[i for i,s in enumerate(c['shapes']) if '/mailer/' in s]
   if len(slots)!=1 or not any('left_wrist' in s for s in c['shapes']):continue
   f=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);force+=f;point=np.array(c['position_world']);moment+=np.cross(point-np.array(packet['post_action_pose']['mailer']),f);weight=-float(f@R[:,2])
   if weight>.05:points.append(point);weights.append(weight)
  return force,moment,(np.average(points,axis=0,weights=weights) if sum(weights)>=.3 else None),sum(weights)
 for t in range(1,len(q)-1):
  c=coord[t];r=rows[t];T,_,_=model.fk('left',q[t]);T1,_,_=model.fk('left',q[t+1]);Tu,_,_=model.fk('left',actions[t]);offset=np.array(c['active_point_offset_local']);point=T[:3,3]+T[:3,:3]@offset;assert np.max(abs(point-np.array(c['control_point_positions']['left'])))<3e-6
  oldforce,oldmoment,cop,load=contact(packets[t-1],rot[t]);force,moment,_,postload=contact(packets[t],rot[t+1]);assert np.max(abs(np.array(packets[t-1]['post_action_pose']['mailer'])-xyz[t]))<1e-6;assert np.max(abs(np.array(packets[t]['post_action_pose']['mailer'])-xyz[t+1]))<1e-6
  material=None
  if cop is not None:
   local=T[:3,:3].T@(cop-T[:3,3]);nominal=Tu[:3,3]+Tu[:3,:3]@local-cop;actual=T1[:3,3]+T1[:3,:3]@local-cop;coplocal=rot[t].T@(cop-xyz[t]);material=dict(current_cop_world=cop.tolist(),current_cop_object_local=coplocal.tolist(),hand_local_material=local.tolist(),nominal_delta_m=nominal.tolist(),actual_delta_m=actual.tolist())
  frames.append(dict(step=t,mode=r['mode'],stage=r.get('route_stage'),stop=r.get('route_stop_reason'),task_ik_override=c.get('self_clearance_task',{}).get('override',False),target_xyz=r['target_xyz'],virtual_point_world=point.tolist(),intent_delta_m=(np.array(r['target_xyz'])-point).tolist(),nominal_virtual_delta_m=(Tu[:3,3]+Tu[:3,:3]@offset-point).tolist(),actual_fixed_virtual_delta_m=(T1[:3,3]+T1[:3,:3]@offset-point).tolist(),object_delta_m=(xyz[t+1]-xyz[t]).tolist(),object_yaw_rad=float(yaw[t]),object_yaw_delta_rad=float(np.arctan2(np.sin(yaw[t+1]-yaw[t]),np.cos(yaw[t+1]-yaw[t]))),old_load_N=load,post_load_N=postload,last_tick_hand_force_on_object_N=force.tolist(),last_tick_hand_moment_about_object_Nm=moment.tolist(),current_contact_material=material))
 groups=[]
 for mode,stage in dict.fromkeys((r['mode'],r['stage']) for r in frames):
  group=[r for r in frames if r['mode']==mode and r['stage']==stage];loaded=[r for r in group if r['current_contact_material'] is not None];direction=[]
  for r in loaded:
   m=r['current_contact_material'];direction.append(dict(step=r['step'],nominal_x=m['nominal_delta_m'][0],actual_x=m['actual_delta_m'][0],obj_x=r['object_delta_m'][0],force_x=r['last_tick_hand_force_on_object_N'][0]))
  groups.append(dict(mode=mode,stage=stage,frames=len(group),first=group[0]['step'],last=group[-1]['step'],object_delta_mm=(np.sum([r['object_delta_m'] for r in group],axis=0)*1000).tolist(),yaw_delta_deg=float(np.rad2deg(sum(r['object_yaw_delta_rad'] for r in group))),task_ik_overrides=sum(r['task_ik_override'] for r in group),loaded_frames=len(loaded),median_intent_mm=(np.median([r['intent_delta_m'] for r in group],axis=0)*1000).tolist(),nominal_material_negative_x=sum(r['nominal_x']<-.00005 for r in direction),actual_material_negative_x=sum(r['actual_x']<-.00005 for r in direction),object_negative_x=sum(r['obj_x']<-.00005 for r in direction),positive_intent_x_actual_material_negative_x=sum(r['nominal_x']>.00005 and r['actual_x']<-.00005 for r in direction),last_tick_force_negative_x=sum(r['force_x']<-.05 for r in direction)))
 events=[]
 for t in [1,125,200,250,300,350,400,450,458,600,1199]:
  if t>=len(q):continue
  row=rows[t];events.append(dict(step=t,mode=row['mode'],stage=row.get('route_stage'),stop=row.get('route_stop_reason'),target_xyz=row['target_xyz'],object_xyz=xyz[t].tolist(),yaw_deg=float(np.rad2deg(yaw[t])),visual_radius_x_m=float(abs(rot[t,0])@np.array([.15,.145,.04])/2),control_point_xyz=coord[t]['control_point_positions']['left']))
 reports.append(dict(run=run,groups=groups,events=events,frames=frames,plan=fr['plan']['front_route_candidates'],source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','coordination.json','frontal_bypass.json','solved_contact_forces.json']}));print(run,json.dumps(groups,indent=2),flush=True)
out=dict(scope=__doc__,episodes=reports,checker_sha256=sha(Path(__file__)),geometry_sha256=sha(w/'staged_self_clearance_task_ik/articulated_hand_geometry.py'),training_ready=False);(w/'FRONT_RECONTACT_BAG_MOTION_CAUSE.json').write_text(json.dumps(out,indent=2))
