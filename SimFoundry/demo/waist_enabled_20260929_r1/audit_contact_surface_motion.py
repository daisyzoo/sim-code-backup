"""Measured rigid-body surface motion and solved forces; descriptive, no control.
Uses after-action contact at t, matched to recorded object state t+1. Tangential
material displacement is finite over the observation interval, not a contact
persistence certificate or a full-substep impulse/friction saturation test.
"""
from pathlib import Path
import sys,json,hashlib,ast,importlib.util
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo));ep=Path(sys.argv[1]).resolve();case=ep.parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prov=json.loads((case/'provenance.json').read_text());source=prov['source_sha256'];helper=next(k for k in source if k.endswith('/articulated_hand_geometry.py'));assert sha(case/'source_snapshot'/helper)==source[helper]
spec=importlib.util.spec_from_file_location('archived_articulated_geometry',case/'source_snapshot'/helper);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assets=['third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf','assets/robots/g1_hand_support_vertices.json','simfoundry/calibration/sorting_station.py','simfoundry/data/hand_obstacle_clearance.py']
for name in assets:assert sha(repo/name)==source[name]
model=module.ArticulatedHandGeometry(repo/assets[0],repo/assets[1]);key='box' if 'push_box' in ep.name else 'mailer';actor='parcel_box' if key=='box' else 'mailer';side='right' if key=='box' else 'left';other='mailer' if key=='box' else 'box'
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float);palm=z['palm_'+side].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
hands=np.array([model.fk(side,v)[0] for v in q]);fkerr=float(np.max(abs(hands[:,:3,3]+hands[:,:3,:3]@np.array([.2,0,.007])-palm)));assert fkerr<2e-6
fr=json.loads((ep/'frontal_bypass.json').read_text());by={r['step']:r for r in fr['rows']};packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];cfg=case/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';assert sha(cfg)==source['simfoundry/scene_bridge/isaac_cfg.py'];node=next(n for n in ast.walk(ast.parse(cfg.read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='core_scale' for t in n.targets));assert ast.unparse(node.value.test)=="obj.semantic == 'mailer'";scale=np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body));size=np.array(fr['plan']['top_recontact']['contact_size_xyz']);half=size*scale/2;series=[];max_world_error=0.;mus={'hand':set(),'table':set()}
for packet in packets:
 t=packet['after_action_step'];r=by.get(t)
 if t+1>=len(q) or r is None or r['mode']!='top_push':continue
 assert np.max(abs(np.array(packet['post_action_pose'][key])-xyz[t+1]))<1e-6
 direction=np.array([-1.,0.,0.]) if r.get('route_stage')=='front_x' else np.array([0.,-1. if key=='box' else 1.,0.]);hf=np.zeros(3);tf=np.zeros(3);contacts=[];weights=[];ratios=[];hnorm=0.
 for c in packet['parcel_contacts']:
  slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
  if len(slots)!=1:continue
  force=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);localf=np.array(c['force_torque_contact'][:3]);frame=np.array(c['contact_frame']);err=float(np.max(abs(localf@frame-np.array(c['force_world_N']))));max_world_error=max(max_world_error,err);assert err<2e-5
  hand=any(side+'_wrist' in s for s in c['shapes']);table=any('/table/' in s or '/table_edge_wear/' in s for s in c['shapes']);mu=np.array(c['friction'][:2])
  if table:tf+=force;mus['table'].add(tuple(mu.tolist()))
  if not hand:continue
  hf+=force;mus['hand'].add(tuple(mu.tolist()));normal=-float(force@rot[t+1,:,2]);hnorm+=normal
  if normal<=.05 or localf[0]<=.05:continue
  assert np.min(mu)>0
  point=np.array(c['position_world']);lp=rot[t+1].T@(point-xyz[t+1]);hp=hands[t+1,:3,:3].T@(point-hands[t+1,:3,3]);prior_obj=xyz[t]+rot[t]@lp;prior_hand=hands[t,:3,3]+hands[t,:3,:3]@hp
  rel=prior_obj-prior_hand;rel_tangent=rel-float(rel@rot[t+1,:,2])*rot[t+1,:,2]
  weights.append(normal);ratios.append(float(np.sum(abs(localf[1:])/mu)/localf[0]));contacts.append(dict(core_local_mm=(lp*1000).tolist(),material_relative_displacement_world_mm=(rel_tangent*1000).tolist(),material_relative_along_route_mm=float(rel_tangent@direction*1000),normal_n=normal,normalized_tangent_l1=ratios[-1]))
 if not weights or hnorm<.3:continue
 cop=np.average([c['core_local_mm'] for c in contacts],axis=0,weights=weights);rel=np.average([c['material_relative_displacement_world_mm'] for c in contacts],axis=0,weights=weights)
 series.append(dict(step=t,stage=r.get('route_stage','rear_top'),hand_load_n=hnorm,hand_force_along_route_n=float(hf@direction),table_force_along_route_n=float(tf@direction),net_hand_table_force_along_route_n=float((hf+tf)@direction),table_normal_world_n=float(tf[2]),target_displacement_along_route_mm=float((xyz[t+1]-xyz[t])@direction*1000),relative_surface_displacement_along_route_mm=float(rel@direction),relative_surface_displacement_norm_mm=float(np.linalg.norm(rel)),cop_core_margin_mm=(half[:2]*1000-abs(cop[:2])).tolist(),contact_normalized_tangent_l1_weighted=float(np.average(ratios,weights=weights)),contact_normalized_tangent_l1_max=max(ratios),contacts=contacts))
def stats(rr):
 if not rr:return dict(n=0)
 keys=['hand_load_n','hand_force_along_route_n','table_force_along_route_n','net_hand_table_force_along_route_n','target_displacement_along_route_mm','relative_surface_displacement_along_route_mm','relative_surface_displacement_norm_mm','contact_normalized_tangent_l1_weighted','contact_normalized_tangent_l1_max']
 return dict(n=len(rr),median={k:float(np.median([r[k] for r in rr])) for k in keys},p95={k:float(np.percentile([r[k] for r in rr],95)) for k in keys},count_relative_ahead_gt_0_1mm=sum(r['relative_surface_displacement_along_route_mm']>.1 for r in rr),count_normalized_tangent_l1_gt_0_95=sum(r['contact_normalized_tangent_l1_max']>.95 for r in rr))
summary={stage:stats([r for r in series if r['stage']==stage]) for stage in sorted({r['stage'] for r in series})}
out=dict(episode=ep.name,summary=summary,series=series,actual_friction={k:[list(v) for v in sorted(vals)] for k,vals in mus.items()},max_fk_palm_error_m=fkerr,max_contact_force_transform_error_n=max_world_error,source_sha256={str(p.relative_to(case)):sha(p) for p in [ep/'raw.npz',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'frontal_bypass.json',ep/'solved_contact_forces.json',cfg,case/'source_snapshot'/helper]},asset_sha256={k:source[k] for k in assets},auditor_sha256=sha(__file__),scope='All top_push intervals with after-action actual active-hand contact load>=0.3N; post-action object pose checked against t+1, FK against measured palms all frames. Finite-step relative material displacement at end contact location, not COP velocity. Force is last solved substep, not interval impulse or causal predictor of full-step motion. Normalized absolute tangent L1 uses recorded contact-frame forces and friction; descriptive threshold counts are not gates or proof of saturation/sticking. No friction/controller changes, quality relaxation or training admission.',training_ready=False)
(ep/'CONTACT_SURFACE_MOTION_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['series','source_sha256','asset_sha256','scope']}))
