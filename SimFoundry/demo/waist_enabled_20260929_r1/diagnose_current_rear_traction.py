"""Current closed rear episodes: actual COP material motion and last-tick traction.
No predicted force, friction modification, causal claim, or training admission.
Same material point is propagated for one measured interval, never assumed stuck.
"""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_front_direction_recontact';sys.path[:0]=[str(stage),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';model=ArticulatedHandGeometry(urdf,vertices);reports=[]
def contacts(packet,key,actor,side,rotation,position):
 groups={k:dict(force=np.zeros(3),moment=np.zeros(3),normal=0.,weighted_ratio=0.,mu=[]) for k in ['hand','table','other']};points=[];weights=[]
 for c in packet['parcel_contacts']:
  slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
  if len(slots)!=1:continue
  sg=1 if slots[0]==1 else -1;basis=np.array(c['contact_frame']);localforce=np.array(c['force_torque_contact']);mu=np.array(c['friction']);force=sg*np.array(c['force_world_N']);assert np.max(abs(localforce[:3]@basis-np.array(c['force_world_N'])))<3e-6
  kind='hand' if any(side+'_wrist_roll' in s for s in c['shapes']) else 'table' if any('/table/' in s for s in c['shapes']) else 'other';point=np.array(c['position_world']);group=groups[kind];group['force']+=force;group['moment']+=np.cross(point-position,force)+sg*localforce[3:]@basis
  if localforce[0]>.05 and min(mu[:2])>0:
   group['normal']+=localforce[0];group['weighted_ratio']+=abs(localforce[1])/mu[0]+abs(localforce[2])/mu[1];group['mu'].append(mu[:2].tolist())
  if kind=='hand':
   load=-float(force@rotation[:,2])
   if load>.05:points.append(point);weights.append(load)
 cop=np.average(points,axis=0,weights=weights) if sum(weights)>=.3 else None
 return groups,cop,float(sum(weights))
for run in ['self_clearance_groups_r1','front_direction_recontact_groups_r1']:
 root=w/run;closed=json.loads((root/'RESULT.json').read_text());assert closed['actual_sampled_visual_review_complete']
 for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
  ep=root/f'case_{cid}/layout_{cid}_{task}';prov=json.loads((ep.parent/'provenance.json').read_text());source=prov['source_sha256'];geom=next(n for n in source if n.endswith('/articulated_hand_geometry.py'))
  assert sha(stage/'articulated_hand_geometry.py')==source[geom]
  for p in [urdf,vertices]:assert sha(p)==source[str(p.relative_to(repo))]
  side='right' if 'push_box' in task else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if key=='box' else 'mailer';direction=-1 if key=='box' else 1
  fr=json.loads((ep/'frontal_bypass.json').read_text());assert not fr['plan'].get('front_route_selected');coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
  records=[];lastmode=None;bout=0
  for row in fr['rows']:
   t=row['step']
   if row['mode']=='top_push' and lastmode!='top_push':bout+=1
   lastmode=row['mode']
   if row['mode']!='top_push' or t+1>=len(q):continue
   packet=packets[t-1];post=packets[t];assert np.max(abs(np.array(packet['post_action_pose'][key])-xyz[t]))<1e-6 and np.max(abs(np.array(post['post_action_pose'][key])-xyz[t+1]))<1e-6
   groups,cop,load=contacts(packet,key,actor,side,rot[t],xyz[t]);after,_,postload=contacts(post,key,actor,side,rot[t+1],xyz[t+1])
   if cop is None:continue
   T,_,_=model.fk(side,q[t]);U,_,_=model.fk(side,u[t]);N,_,_=model.fk(side,q[t+1]);hl=T[:3,:3].T@(cop-T[:3,3]);ol=rot[t].T@(cop-xyz[t]);offset=np.array(coords[t]['active_point_offset_local']);virtual=T[:3,3]+T[:3,:3]@offset;assert np.max(abs(virtual-np.array(coords[t]['control_point_positions'][side])))<3e-6
   nominal=U[:3,3]+U[:3,:3]@hl-cop;actual=N[:3,3]+N[:3,:3]@hl-cop;virtual_delta=U[:3,3]+U[:3,:3]@offset-virtual;object_material=xyz[t+1]+rot[t+1]@ol-cop;slip=actual-object_material;inward=-np.sign(ol[0])*rot[t,:,0]
   metrics=dict(nominal_material_inward_mm=float(inward@nominal*1000),nominal_virtual_inward_mm=float(inward@virtual_delta*1000),actual_material_fixed_axis_inward_mm=float(inward@actual*1000),actual_relative_material_inward_mm=float(inward@slip*1000),nominal_virtual_material_difference_mm=float(np.linalg.norm(nominal-virtual_delta)*1000),nominal_actual_material_difference_mm=float(np.linalg.norm(nominal-actual)*1000),actual_forward_material_slip_mm=float(direction*slip[1]*1000),object_forward_delta_mm=float(direction*(xyz[t+1,1]-xyz[t,1])*1000),load_n=load,post_load_n=postload)
   forcegroups={k:dict(force_N=v['force'].tolist(),moment_Nm=v['moment'].tolist(),contact_normal_n=float(v['normal']),normal_weighted_translation_cone_ratio=float(v['weighted_ratio']/v['normal']) if v['normal'] else None,mu=v['mu']) for k,v in groups.items()}
   records.append(dict(step=t,bout=bout,metrics=metrics,hand_local_material_mm=(hl*1000).tolist(),object_local_cop_mm=(ol*1000).tolist(),forcegroups=forcegroups,task_ik_override=coords[t].get('self_clearance_task',{}).get('override',False)))
  summary={k:dict(median=float(np.median([r['metrics'][k] for r in records])),p90=float(np.percentile([r['metrics'][k] for r in records],90))) for k in records[0]['metrics']}
  counts=dict(loaded_steps=len(records),virtual_inward_material_outward=sum(r['metrics']['nominal_virtual_inward_mm']>=-1e-4 and r['metrics']['nominal_material_inward_mm']<-.05 for r in records),nominal_inward_actual_outward=sum(r['metrics']['nominal_material_inward_mm']>.05 and r['metrics']['actual_material_fixed_axis_inward_mm']<-.05 for r in records),hand_forward_slip_over_05mm=sum(r['metrics']['actual_forward_material_slip_mm']>.5 for r in records),hand_translation_ratio_over_098=sum((r['forcegroups']['hand']['normal_weighted_translation_cone_ratio'] or 0)>.98 for r in records),table_translation_ratio_over_098=sum((r['forcegroups']['table']['normal_weighted_translation_cone_ratio'] or 0)>.98 for r in records),task_ik_overrides=sum(r['task_ik_override'] for r in records))
  item=dict(episode=str(ep),summary=summary,counts=counts,records=records,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','solved_contact_forces.json']},closed_result_sha256=sha(root/'RESULT.json'));reports.append(item);print(run,task,json.dumps(counts),json.dumps({k:v for k,v in summary.items() if k in ['nominal_virtual_material_difference_mm','nominal_actual_material_difference_mm','actual_forward_material_slip_mm','load_n']}),flush=True)
out=dict(scope=__doc__,episodes=reports,checker_sha256=sha(__file__),geometry_sha256=sha(stage/'articulated_hand_geometry.py'),limitations=['Force packets sample only last physics tick; no integrated impulse or causal gain inference.','Translation cone ratio ignores torsional/rolling friction allocation; saturation does not alone prove continuous sliding.','Material point matches current COP only; next actual COP may migrate.','No future states are used by any collector; this is recorded diagnosis only.'],training_ready=False)
(w/'CURRENT_REAR_TRACTION_DIAGNOSIS.json').write_text(json.dumps(out,indent=2))
