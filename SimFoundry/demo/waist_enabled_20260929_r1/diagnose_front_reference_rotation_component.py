"""Compare virtual reference motion to prior actual COP material point motion."""
from pathlib import Path
import json,sys,hashlib,importlib.util
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def mod(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
reports=[]
for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
 ep=w/'rear_core_slice_groups_r1'/f'case_{cid}/layout_{cid}_{task}';src=json.loads((ep.parent/'provenance.json').read_text())['source_sha256'];snap=ep.parent/'source_snapshot';gr=next(n for n in src if n.endswith('/articulated_hand_geometry.py'));pr='simfoundry/data/projected_support_reference.py'
 for n in [gr,pr]:assert sha(snap/n)==src[n]
 assets=['third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf','assets/robots/g1_hand_support_vertices.json','simfoundry/calibration/sorting_station.py','simfoundry/data/hand_obstacle_clearance.py']
 for n in assets:assert sha(repo/n)==src[n]
 model=mod(snap/gr,'mg').ArticulatedHandGeometry(repo/assets[0],repo/assets[1]);pm=mod(snap/pr,'mp');side='right' if task=='push_box_to_bin' else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if key=='box' else 'mailer'
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rots=Rotation.from_quat(z[key]).as_matrix()
 packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};fs=json.loads((ep/'frontal_bypass.json').read_text())['rows'];rows=[]
 for f in fs:
  t=f['step']
  if f['mode']!='top_push' or t==0 or t+1>=len(q):continue
  packet=packets[t-1];assert max(abs(np.array(packet['post_action_pose'][key])-xyz[t]))<1e-6;points=[];weights=[]
  for contact in packet['parcel_contacts']:
   slots=[i for i,s in enumerate(contact['shapes']) if '/'+actor+'/' in s]
   if len(slots)!=1 or not any(side+'_wrist' in s for s in contact['shapes']):continue
   force=np.array(contact['force_world_N'])*(1 if slots[0]==1 else -1);normal=-float(force@rots[t,:,2])
   if normal>.05:points.append(contact['position_world']);weights.append(normal)
  if sum(weights)<.3:continue
  cop=np.average(points,axis=0,weights=weights);T,_,_=model.fk(side,q[t]);handlocal=T[:3,:3].T@(cop-T[:3,3]);objlocal=rots[t].T@(cop-xyz[t]);ref=cs[t]['active_support_reference'];center=ref['center_local'];n=ref['world_normal']
  def virtual(v):
   M,_,_=model.fk(side,v);rr=pm.projected_support_reference(model.vertices[side],M[:3,:3],n,center_local=center);return M[:3,3]+M[:3,:3]@rr['reference_local']
  vc=virtual(q[t]);assert max(abs(vc-f['observed_support_xyz']))<2e-6
  U,_,_=model.fk(side,u[t]);N,_,_=model.fk(side,q[t+1]);cm=U[:3,3]+U[:3,:3]@handlocal;am=N[:3,3]+N[:3,:3]@handlocal;om=xyz[t+1]+rots[t+1]@objlocal
  rows.append(dict(step=t,route_stage=f['route_stage'],load_n=sum(weights),actual_virtual_delta_mm=((virtual(q[t+1])-vc)*1000).tolist(),actual_material_minus_virtual_delta_mm=(((am-cop)-(virtual(q[t+1])-vc))*1000).tolist(),actual_hand_material_delta_mm=((am-cop)*1000).tolist(),actual_object_material_delta_mm=((om-cop)*1000).tolist(),nominal_material_delta_mm=((cm-cop)*1000).tolist(),nominal_virtual_delta_mm=((virtual(u[t])-vc)*1000).tolist(),material_minus_virtual_nominal_delta_mm=(((cm-cop)-(virtual(u[t])-vc))*1000).tolist(),actual_hand_minus_object_material_delta_mm=((am-om)*1000).tolist(),nominal_minus_actual_hand_material_mm=((cm-am)*1000).tolist(),virtual_goal_residual_mm=((np.array(f['target_xyz'])-virtual(u[t]))*1000).tolist()))
 keys=['actual_material_minus_virtual_delta_mm','material_minus_virtual_nominal_delta_mm','actual_hand_minus_object_material_delta_mm','nominal_minus_actual_hand_material_mm','virtual_goal_residual_mm'];summary={k:dict(median_xyz=np.median([r[k] for r in rows],axis=0).tolist(),p95_abs_xyz=np.percentile(abs(np.array([r[k] for r in rows])),95,axis=0).tolist()) for k in keys};report=dict(episode=ep.name,samples=len(rows),summary=summary,rows=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','solved_contact_forces.json','coordination.json','frontal_bypass.json']});reports.append(report);print(ep.name,len(rows),json.dumps(summary),flush=True)
p=w/'FRONT_REFERENCE_ROTATION_COMPONENT.json';assert not p.exists();p.write_text(json.dumps(dict(episodes=reports,checker_sha256=sha(Path(__file__)),training_ready=False,scope='Use only prior after-action t-1 solved COP for current t material identities. Compare fixed material hand point with recalculated virtual reference, and next measured motion of same hand/object material points. No contact persistence, friction saturation, dynamics prediction or new controller claim.'),indent=2))
