"""Compare frozen virtual and current contact material references on actual logs.
The load-weighted recorded contact point is transformed into the current hand
frame, then advected with commanded/next observed hand poses. This is a material
point diagnostic, NOT a prediction that the future COP remains at that point.
Next parcel poses are used only for scoring observed relative motion, never to
construct a command or a predictor. No runtime/audit/admission changes.
"""
from pathlib import Path
import json,sys,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_box_entry_lift';sys.path[:0]=[str(stage),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
r=w/'box_entry_lift_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();geom=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');episodes=[]
for ep in sorted(r.glob('case_*/layout_*')):
 if not (ep/'BOX_ENTRY_NUMERIC_REVIEW.json').exists() or 'wait_no_package' in ep.name:continue
 fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan']
 if not plan.get('rear_cop_centering',{}).get('enabled'):continue
 nr=json.loads((ep/'BOX_ENTRY_NUMERIC_REVIEW.json').read_text());fs={x['step']:x for x in fr['rows']};cs={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};packets={x['after_action_step']:x for x in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};key='box' if 'push_box' in ep.name else 'mailer';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';core=np.array(plan['rear_cop_centering']['actual_core_size_xyz'])
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z[key]).as_matrix()
 losses={t for b in nr['bouts'] if b['exit_reason']=='lost_contact' for t in range(max(b['start'],b['end']-11),b['end']+1)};tilts={t for b in nr['bouts'] if b['exit_reason']=='incipient_tilt_independent' for t in range(max(b['start'],b['end']-11),b['end']+1)};rows=[]
 for t,f in fs.items():
  if t>=len(q)-1 or f['mode']!='top_push':continue
  points=[];weights=[]
  for c in packets[t-1]['parcel_contacts']:
   slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
   if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
   force=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@R[t,:,2])
   if load>.05:points.append(c['position_world']);weights.append(load)
  if sum(weights)<.3:continue
  cop=np.average(points,axis=0,weights=weights);local=R[t].T@(cop-xyz[t]);axes=[k for k in [0,1] if core[k]/2-abs(local[k])<=.01];T,_,_=geom.fk(side,q[t]);U,_,_=geom.fk(side,u[t]);N,_,_=geom.fk(side,q[t+1]);hand_local=T[:3,:3].T@(cop-T[:3,3]);virtual=np.array(f['control_offset_local']);vp=T[:3,3]+T[:3,:3]@virtual;assert np.max(abs(vp-f['observed_support_xyz']))<1e-6
  commanded_virtual=U[:3,3]+U[:3,:3]@virtual;commanded_material=U[:3,3]+U[:3,:3]@hand_local;observed_material=N[:3,3]+N[:3,:3]@hand_local;next_local=R[t+1].T@(observed_material-xyz[t+1]);normals=np.array([-np.sign(local[k])*R[t,:,k] for k in axes]).reshape(-1,3)
  cv=normals@(commanded_virtual-vp)*1000;cm=normals@(commanded_material-cop)*1000;om=normals@(observed_material-cop)*1000;rel=[-np.sign(local[k])*(next_local[k]-local[k])*1000 for k in axes];trace=cs[t]['joint_edge_refinement'];edge_verified=bool(trace['input_selected'] and trace['reason'] in ['nonlinear_joint_direction','parent_direction_valid'])
  translation=-normals@(xyz[t+1]-xyz[t])*1000;rotation=np.array([-np.sign(local[k])*((R[t+1].T-R[t].T)@(observed_material-xyz[t+1]))[k]*1000 for k in axes]);assert np.max(abs(np.array(rel)-(om+translation+rotation)),initial=0)<1e-8
  rows.append(dict(object_translation_inward_mm=translation.tolist(),object_rotation_inward_mm=rotation.tolist(),step=t,near_loss=t in losses,near_tilt=t in tilts,edge_verified=edge_verified,edge_reason=trace['reason'],load_n=sum(weights),reference_contact_distance_mm=float(np.linalg.norm(cop-vp)*1000),near_axes=axes,cop_local_mm=(local*1000).tolist(),commanded_virtual_inward_mm=cv.tolist(),commanded_material_inward_mm=cm.tolist(),observed_material_world_inward_mm=om.tolist(),observed_material_relative_inward_mm=rel,virtual_pass_but_material_nominal_outward=bool(edge_verified and len(axes) and min(cv)>=-.0001 and min(cm)<-.05),next_material_outside_core=bool(np.any(abs(next_local[:2])>core[:2]/2+.0001))))
 def summary(group):
  verified=[x for x in group if x['edge_verified']];return dict(rows=len(group),edge_verified=len(verified),virtual_pass_but_material_nominal_outward=sum(x['virtual_pass_but_material_nominal_outward'] for x in group),median_reference_contact_distance_mm=float(np.median([x['reference_contact_distance_mm'] for x in group])) if group else None,p90_reference_contact_distance_mm=float(np.quantile([x['reference_contact_distance_mm'] for x in group],.9)) if group else None,verified_but_observed_world_outward_gt_0_05mm=sum(bool(x['observed_material_world_inward_mm'] and min(x['observed_material_world_inward_mm'])<-.05) for x in verified),verified_but_observed_relative_outward_gt_0_05mm=sum(bool(x['observed_material_relative_inward_mm'] and min(x['observed_material_relative_inward_mm'])<-.05) for x in verified),next_material_outside_core=sum(x['next_material_outside_core'] for x in group))
 out=dict(episode=ep.name,summary=summary(rows),loss_summary=summary([x for x in rows if x['near_loss']]),tilt_summary=summary([x for x in rows if x['near_tilt']]),records=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','solved_contact_forces.json','BOX_ENTRY_NUMERIC_REVIEW.json']});episodes.append(out);print(ep.name,json.dumps(out['summary']),json.dumps(out['loss_summary']),json.dumps(out['tilt_summary']),flush=True)
(r/'RELATIVE_MOTION_DECOMPOSITION.json').write_text(json.dumps(dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),episodes=episodes,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'articulated_hand_geometry.py',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json']},runtime_unchanged=True,training_ready=False),indent=2))
