"""Requested versus nominal-command FK versus next measured reference, same offset."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo));ep=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();prov=json.loads((ep.parent/'provenance.json').read_text());src=prov['source_sha256'];helper=next(k for k in src if k.endswith('/articulated_hand_geometry.py'));path=ep.parent/'source_snapshot'/helper;assert sha(path)==src[helper]
spec=importlib.util.spec_from_file_location('loaded_fk',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assets=['third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf','assets/robots/g1_hand_support_vertices.json','simfoundry/calibration/sorting_station.py','simfoundry/data/hand_obstacle_clearance.py']
for a in assets:assert sha(repo/a)==src[a]
model=module.ArticulatedHandGeometry(repo/assets[0],repo/assets[1]);side='right' if 'push_box' in ep.name else 'left'
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
fr=json.loads((ep/'frontal_bypass.json').read_text());coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};rows=[];max_alignment=0.
def point(v,offset):
 T,_,_=model.fk(side,v);return T[:3,3]+T[:3,:3]@offset
for r in fr['rows']:
 t=r['step']
 if r['mode']!='top_push' or t+1>=len(q):continue
 offset=np.asarray(r['control_offset_local']);goal=np.array(r['target_xyz']);current=point(q[t],offset);nominal=point(u[t],offset);actual=point(q[t+1],offset);error=float(np.max(abs(current-r['observed_support_xyz'])));max_alignment=max(max_alignment,error);assert error<2e-6
 normal=coords[t].get('contact_normal_tracking')
 rows.append(dict(step=t,loaded=r['contact_load']['observed_vertical_load_n']>=.2,goal_minus_current_mm=((goal-current)*1000).tolist(),goal_minus_nominal_command_mm=((goal-nominal)*1000).tolist(),goal_minus_next_actual_mm=((goal-actual)*1000).tolist(),nominal_minus_next_actual_mm=((nominal-actual)*1000).tolist(),actual_delta_mm=((actual-current)*1000).tolist(),nominal_delta_mm=((nominal-current)*1000).tolist(),waist_state_rad=q[t,0],waist_command_rad=u[t,0],normal_angle_error_rad=normal['angle_error_rad'] if normal else None,normal_weight_m=normal['weight_m'] if normal else None))
loaded=[r for r in rows if r['loaded']];keys=['goal_minus_current_mm','goal_minus_nominal_command_mm','goal_minus_next_actual_mm','nominal_minus_next_actual_mm','actual_delta_mm','nominal_delta_mm'];summary={k:dict(median_xyz=np.median([r[k] for r in loaded],axis=0).tolist(),p95_abs_xyz=np.percentile(np.abs([r[k] for r in loaded]),95,axis=0).tolist()) for k in keys};summary['loaded_steps']=len(loaded);summary['waist_command_at_reserve']=sum(bool(abs(r['waist_command_rad'])>=.98-1e-6) for r in loaded);summary['median_normal_angle_error_rad']=float(np.median([r['normal_angle_error_rad'] for r in loaded if r['normal_angle_error_rad'] is not None]))
out=dict(episode=ep.name,summary=summary,rows=rows,max_recorded_current_reference_error_m=max_alignment,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','frontal_bypass.json']},archived_helper_sha256=sha(path),assets_sha256={a:sha(repo/a) for a in assets},checker_sha256=sha(Path(__file__)),training_ready=False,scope='Same recorded current-frame virtual reference offset used for measured q[t], commanded absolute u[t] and measured q[t+1]. FK does not predict future contact or certify joint-command reachability under all simultaneous constraints. Requested-current lag, nominal solve residual and next actual tracking are distinct; no loaded response model is assumed.')
(ep/'LOADED_WAYPOINT_TRACKING_DIAGNOSIS.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(episode=ep.name,summary=summary,max_recorded_current_reference_error_m=max_alignment)))
