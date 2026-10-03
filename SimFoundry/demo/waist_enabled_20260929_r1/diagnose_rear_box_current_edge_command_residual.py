"""Current four real rear-box trials: edge timing and measured material motion.
Use prior solved force packet aligned with current measured pose; future pose
scores observed response only. No future input to a controller, rollout or gate.
"""
from pathlib import Path
import sys,json,hashlib,datetime,importlib.util
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo));r=w/'front_corridor_midpoint_physical_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
budget=json.loads((r/'REAR_BOX_FOUR_RUN_BUDGET_DIAGNOSTIC.json').read_text());sources={str(r/'REAR_BOX_FOUR_RUN_BUDGET_DIAGNOSTIC.json'):sha(r/'REAR_BOX_FOUR_RUN_BUDGET_DIAGNOSTIC.json')};results=[]
def summary(rows):
 near=[x for x in rows if x['near_axes']];verified=[x for x in near if x['edge_command_reported_valid']]
 def stats(key,selected):
  values=[v for x in selected for v in x[key]]
  return dict(n=len(values),median=float(np.median(values)),minimum=float(min(values)),maximum=float(max(values))) if values else None
 return dict(frames=len(rows),near_edge_frames=len(near),edge_input_selected=sum(x['edge_input_selected'] for x in near),edge_command_reported_valid=len(verified),edge_override=sum(x['edge_override'] for x in near),reference_contact_distance_mm_median=float(np.median([x['reference_contact_distance_mm'] for x in rows])) if rows else None,final_virtual_inward_mm=stats('final_virtual_inward_mm',verified),final_material_nominal_inward_mm=stats('final_material_nominal_inward_mm',verified),observed_material_world_inward_mm=stats('observed_material_world_inward_mm',verified),observed_material_relative_inward_mm=stats('observed_material_relative_inward_mm',verified),verified_relative_outward_gt_0_05mm=sum(min(x['observed_material_relative_inward_mm'])<-.05 for x in verified),verified_world_outward_gt_0_05mm=sum(min(x['observed_material_world_inward_mm'])<-.05 for x in verified),final_command_differs_from_refined=sum(x['refined_final_max_joint_difference_rad']>1e-7 for x in verified),final_virtual_below_declared_inward=sum(min(x['final_virtual_inward_mm'])<x['nominal_inward_requirement_mm']-.0001 for x in verified))
for item in budget['records']:
 ep=w/item['run']/'case_840023/layout_840023_push_box_to_bin';prov=json.loads((ep.parent/'provenance.json').read_text());snap=ep.parent/'source_snapshot';helper=next(n for n in prov['source_sha256'] if n.endswith('/articulated_hand_geometry.py'));p=snap/helper;assert sha(p)==prov['source_sha256'][helper]
 spec=importlib.util.spec_from_file_location('archived_geometry',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 assets=[repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json']
 for path in assets:assert sha(path)==prov['source_sha256'][str(path.relative_to(repo))];sources[str(path)]=sha(path)
 geom=mod.ArticulatedHandGeometry(*assets);sources[str(p)]=sha(p)
 fr=json.loads((ep/'frontal_bypass.json').read_text());coord={c['step']:c for c in json.loads((ep/'coordination.json').read_text())};packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];core=np.array(fr['plan']['rear_cop_centering']['actual_core_size_xyz'])
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:xyz=z['box'].astype(float);palm=z['palm_right'].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['box']).as_matrix()
 hands=np.array([geom.fk('right',v)[0] for v in q]);err=float(np.max(abs(hands[:,:3,3]+hands[:,:3,:3]@np.array([.2,0,.007])-palm)));assert err<2e-6;records=[]
 for row in fr['rows']:
  t=row['step']
  if t>=len(q)-1 or row['mode']!='top_push':continue
  pkt=packets[t-1];assert pkt['after_action_step']==t-1;np.testing.assert_allclose(pkt['post_action_pose']['box'],xyz[t],rtol=0,atol=2e-6);points=[];weights=[]
  for contact in pkt['parcel_contacts']:
   slots=[i for i,n in enumerate(contact['shapes']) if '/parcel_box/' in n]
   if len(slots)!=1 or not any('right_wrist' in n for n in contact['shapes']):continue
   force=np.array(contact['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@rot[t,:,2])
   if load>.05:points.append(contact['position_world']);weights.append(load)
  if sum(weights)<.3:continue
  cop=np.average(points,weights=weights,axis=0);local=rot[t].T@(cop-xyz[t]);margin=core[:2]/2-abs(local[:2]);axes=np.flatnonzero(margin<=.010)
  if row['rear_cop_centering'].get('override'):np.testing.assert_allclose(cop,row['rear_cop_centering']['cop_world'],rtol=0,atol=2e-6)
  T=hands[t];N=hands[t+1];U=geom.fk('right',u[t])[0];material=T[:3,:3].T@(cop-T[:3,3]);virtual=np.asarray(row['control_offset_local']);vp=T[:3,3]+T[:3,:3]@virtual;assert abs(vp-row['observed_support_xyz']).max()<2e-6
  nominal_virtual=U[:3,3]+U[:3,:3]@virtual;nominal_material=U[:3,3]+U[:3,:3]@material;actual_material=N[:3,3]+N[:3,:3]@material;next_local=rot[t+1].T@(actual_material-xyz[t+1]);normals=np.array([-np.sign(local[k])*rot[t,:,k] for k in axes]).reshape(-1,3)
  world=normals@(actual_material-cop)*1000;translation=-normals@(xyz[t+1]-xyz[t])*1000;rotation=np.array([-np.sign(local[k])*((rot[t+1].T-rot[t].T)@(actual_material-xyz[t+1]))[k]*1000 for k in axes]);relative=np.array([-np.sign(local[k])*(next_local[k]-local[k])*1000 for k in axes]);assert np.max(abs(relative-world-translation-rotation),initial=0)<1e-8
  edge=coord[t]['joint_edge_refinement'];valid=bool(edge['input_selected'] and edge['reason'] in ['nonlinear_joint_direction','parent_direction_valid']);selected=np.asarray(edge['final_upper_command'])
  previous_nominal=geom.fk('right',u[t-1])[0];previous_point=previous_nominal[:3,3]+previous_nominal[:3,:3]@virtual
  actual_virtual=N[:3,3]+N[:3,:3]@virtual
  records.append(dict(requested_reference_lead_world_mm=((np.array(row['target_xyz'])-vp)*1000).tolist(),unrealized_waypoint_minus_commanded_reference_mm=((np.array(row['target_xyz'])-nominal_virtual)*1000).tolist(),final_nominal_reference_motion_world_mm=((nominal_virtual-vp)*1000).tolist(),final_nominal_step_from_previous_command_mm=((nominal_virtual-previous_point)*1000).tolist(),actual_virtual_motion_world_mm=((actual_virtual-vp)*1000).tolist(),step=t,edge_input_selected=edge['input_selected'],edge_override=edge['override'],edge_reason=edge['reason'],edge_command_reported_valid=valid,nominal_inward_requirement_mm=1000*edge.get('nominal_inward_requirement_m',0),refined_final_max_joint_difference_rad=float(abs(selected-u[t]).max()),cop_local_mm=(1000*local).tolist(),core_margin_mm=(1000*margin).tolist(),near_axes=axes.tolist(),reference_contact_distance_mm=float(np.linalg.norm(cop-vp)*1000),normal_load_n=sum(weights),final_virtual_inward_mm=(normals@(nominal_virtual-vp)*1000).tolist(),final_material_nominal_inward_mm=(normals@(nominal_material-cop)*1000).tolist(),observed_material_world_inward_mm=world.tolist(),object_translation_inward_mm=translation.tolist(),object_rotation_inward_mm=rotation.tolist(),observed_material_relative_inward_mm=relative.tolist(),observed_tilt_rad=row['observed_parcel_tilt_rad'],actual_target_forward_mm=float(-(xyz[t+1,1]-xyz[t,1])*1000)))
 bouts=[]
 for b in item['bouts']:
  rr=[x for x in records if b['start']<=x['step']<=b['last']];tail=[x for x in rr if x['step']>=b['last']-7]
  bouts.append(dict(start=b['start'],last=b['last'],exit_reason=b['exit_reason'],summary=summary(rr),last8_summary=summary(tail),last8=tail,first_under_20mm=next((x['step'] for x in rr if min(x['core_margin_mm'])<20),None),first_under_10mm=next((x['step'] for x in rr if min(x['core_margin_mm'])<10),None)))
 result=dict(run=item['run'],passed=item['passed'],max_fk_palm_error_m=err,summary=summary(records),bouts=bouts,records=records);results.append(result)
 for name in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','solved_contact_forces.json']:sources[str(ep/name)]=sha(ep/name)
 print(json.dumps({k:v for k,v in result.items() if k not in ['bouts','records']}),flush=True)
sources[str(Path(__file__))]=sha(__file__)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,results=results,source_sha256=sources,training_ready=False,controller_changed=False)
with (r/'REAR_BOX_CURRENT_EDGE_COMMAND_RESIDUAL_DIAGNOSTIC.json').open('x') as f:json.dump(out,f,indent=2)
