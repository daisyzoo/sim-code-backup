"""Recorded instantaneous post-action contact wrenches and explicit toy rotation budget.
Forces are last physics tick only, not timestep-integrated or intervention outcomes.
Uniform table pressure + Coulomb disk friction is a sensitivity model, NOT a
measured force limit, static feasibility certificate, or actual rotation prediction.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
from numpy.polynomial.legendre import leggauss
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
def quantile(v):return None if not v else {str(p):float(np.percentile(v,p)) for p in [0,50,90,100]}
for cid in [840000,840001,840004,840005]:
 for task in ['push_box_to_bin','nudge_mailer_to_bin']:
  ep=w/f'joint_edge_retry_groups_r1/case_{cid}/layout_{cid}_{task}';key='box' if task=='push_box_to_bin' else 'mailer';actor='parcel_box' if key=='box' else 'mailer';side='right' if key=='box' else 'left';fr=json.loads((ep/'frontal_bypass.json').read_text());modes={r['step']:r['mode'] for r in fr['rows']};packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows']
  with np.load(ep/'trace.npz') as z:position=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
  series=[];all_hand_mu=set();all_table_mu=set();world_force_checks=0
  for packet in packets:
   action=packet['after_action_step'];t=action+1
   if t>=len(position):continue
   forces={k:np.zeros(3) for k in ['hand','table','other']};torques={k:np.zeros(3) for k in forces};normal=0.;lever=0.;torsion_abs=0.;contacts=0;table_load=0.
   for c in packet['parcel_contacts']:
    slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
    if len(slots)!=1:continue
    sign=1 if slots[0]==1 else -1;frame=np.array(c['contact_frame']);f0=np.array(c['force_torque_contact']);assert np.allclose(f0[:3]@frame,c['force_world_N'],rtol=2e-6,atol=2e-6);world_force_checks+=1;F=sign*np.array(c['force_world_N']);tau=sign*f0[3:]@frame;point=np.array(c['position_world']);group='hand' if any(side+'_wrist_roll_rubber_hand' in s for s in c['shapes']) else 'table' if any('/table/' in s for s in c['shapes']) else 'other';forces[group]+=F;torques[group]+=np.cross(point-position[t],F)+tau
    if group=='hand':
     all_hand_mu.add(tuple(c['friction'][:2]));load=-float(F@rot[t,:,2])
     if load>.05:normal+=load;lever+=load*np.linalg.norm(((point-position[t])@rot[t])[:2]);contacts+=1
     torsion_abs+=float(np.linalg.norm(tau))
    if group=='table':all_table_mu.add(tuple(c['friction'][:2]));table_load+=float(F[2])
   if modes.get(action)=='top_push' and normal>.3:
    series.append(dict(step=action,load_n=normal,weighted_lever_mm=1000*lever/normal,hand_xy_force_n=float(np.linalg.norm(forces['hand'][:2])),hand_yaw_torque_nm=float(torques['hand'][2]),table_yaw_torque_nm=float(torques['table'][2]),net_contact_yaw_torque_nm=float(sum(torques.values())[2]),table_vertical_load_n=table_load,direct_hand_contact_torque_abs_nm=torsion_abs,hand_contact_count=contacts))
  row=dict(episode=ep.name,loaded_top_push_samples=len(series),hand_mu=sorted(all_hand_mu),table_mu=sorted(all_table_mu),world_force_transform_checks=world_force_checks,statistics={k:quantile([v[k] for v in series]) for k in ['load_n','weighted_lever_mm','hand_xy_force_n','hand_yaw_torque_nm','table_yaw_torque_nm','net_contact_yaw_torque_nm','table_vertical_load_n','direct_hand_contact_torque_abs_nm']},source_sha256={n:sha(ep/n) for n in ['trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json']});rows.append(row);print(ep.name,len(series),row['statistics']['weighted_lever_mm'],flush=True)
# Explicit sensitivity calculation, not fitted to episode success/failure.
box_ep=w/'joint_edge_retry_groups_r1/case_840001/layout_840001_push_box_to_bin';fr=json.loads((box_ep/'frontal_bypass.json').read_text());size=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']);layout_file=box_ep.parent/'source_snapshot/scenes/sorting_station_g1_23/twin/layout.json';layout=json.loads(layout_file.read_text());mass=next(o['mass'] for o in layout['objects'] if o['name']=='parcel_box');assert mass==.18
root=np.array(leggauss(100)[0]);weight=np.array(leggauss(100)[1]);rad=np.hypot(root[:,None]*size[0]/2,root[None,:]*size[1]/2);mean_radius=float(np.sum(rad*weight[:,None]*weight[None,:])/4)
old=json.loads((w/'ROTATED_ROUTE_STICKING_CONTINUATION.json').read_text());lever0=float(np.linalg.norm(old['fixed_parcel_material_point'][:2]));contact_levers={'prior_selected':lever0,'near_edge':size[0]/2-.010,'near_corner':float(np.linalg.norm(size[:2]/2-.010))};toy=[]
for name,lever in contact_levers.items():
 for load in [.5,1.,3.,5.,10.]:
  hand_cap=1.*load*lever;table_model=.550000011920929*(mass*9.81+load)*mean_radius;toy.append(dict(contact=name,lever_arm_mm=lever*1000,load_n=load,hand_point_tangential_yaw_capacity_nm=hand_cap,uniform_pressure_table_rotation_resistance_nm=table_model,capacity_to_resistance_ratio=hand_cap/table_model))
out=dict(scope=__doc__,episodes=rows,toy_model=dict(assumptions=['Planar pure rotation about center, upright body, single top point force tangent to radius.','Hand mu1 and table mu.55 observed in actual contact packets.','Uniform table pressure over collision-core rectangle; hand downforce adds to support load.','Ignores redistributed pressure, spin/rolling friction, elastic/dynamic effects, joint torque, full arm and contact patch geometry.','A model ratio above1 only avoids this toy-model rejection; it does not prove realizable rotation.'],mass_kg=mass,core_size=size.tolist(),uniform_pressure_mean_radius_m=mean_radius,rows=toy),source_sha256={str(layout_file.relative_to(w)):sha(layout_file),'ROTATED_ROUTE_STICKING_CONTINUATION.json':sha(w/'ROTATED_ROUTE_STICKING_CONTINUATION.json')},checker_sha256=sha(Path(__file__)),training_ready=False)
(w/'ROTATION_WRENCH_BUDGET.json').write_text(json.dumps(out,indent=2));print('mean radius mm',mean_radius*1000,'toy at3N',[r for r in toy if r['load_n']==3.])
