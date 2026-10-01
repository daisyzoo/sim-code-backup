"""Prediction-only test on completed records, with frozen unloaded parameters.
Every prediction uses q[t],q[t-1],u[t],u[t-1] and the current-frame virtual
reference; q[t+1] is held out for scoring only. No fitting, candidate commands,
controller changes, future COP prediction or physical efficacy claim.
"""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo));ep=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prov=json.loads((ep.parent/'provenance.json').read_text());source=prov['source_sha256'];snap=ep.parent/'source_snapshot'
def load(name,mod):
 n=next(k for k in source if k.endswith('/'+name));p=snap/n;assert sha(p)==source[n];s=importlib.util.spec_from_file_location(mod,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m,p
geo,gp=load('articulated_hand_geometry.py','causal_prediction_geometry');response,rp=load('causal_unloaded_response.py','frozen_causal_response')
parameter_name=next(k for k in source if k.endswith('/causal_response_parameters.json'));parameter_path=snap/parameter_name;assert sha(parameter_path)==source[parameter_name];params=json.loads(parameter_path.read_text())
fit_path=w/'unloaded_tracking_dynamics_bias_audit_r1/RESULT.json';assert sha(fit_path)==params['fit_report_sha256'];fit=json.loads(fit_path.read_text());assert fit['fit_parent']==params['fit_parent']
for task,v in params['tasks'].items():assert v['decay']==fit['fits'][task]['a'] and v['parent_samples']==fit['fits'][task]['n']
for name in ['third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf','assets/robots/g1_hand_support_vertices.json','simfoundry/calibration/sorting_station.py','simfoundry/data/hand_obstacle_clearance.py']:assert sha(repo/name)==source[name]
geometry=geo.ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
audit=json.loads((ep/'REAR_JOINT_XY_LIVE_AUDIT.json').read_text());assert audit['passed'] and audit['enabled'] and audit['auditor_sha256']==sha(w/'audit_rear_joint_xy_live.py')
for n,h in audit['source_sha256'].items():assert sha(ep/n)==h
side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';task='push_box_to_bin' if key=='box' else 'nudge_mailer_to_bin';a=np.array(params['tasks'][task]['decay'])
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
with np.load(ep/'trace.npz') as z:obj=z[key].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z[key]).as_matrix()
fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};cs={c['step']:c for c in json.loads((ep/'coordination.json').read_text())};rows=[];excluded=0
for t,f in fr.items():
 if f['mode']!='top_push' or f['contact_load']['observed_vertical_load_n']<.2 or t+1>=len(q):continue
 prev=fr.get(t-1,{})
 if prev.get('mode')!='top_push' or prev.get('contact_load',{}).get('observed_vertical_load_n',0)<.2:excluded+=1;continue
 offset=np.asarray(f['control_offset_local'])
 def point(angles):
  T,_,_=geometry.fk(side,angles);return T[:3,3]+T[:3,:3]@offset
 current=point(q[t]);assert np.max(abs(current-f['observed_support_xyz']))<2e-6
 gain,bias=response.response_parameters(q[t],q[t-1],u[t-1],a)
 forecasts={'nominal_command':u[t].copy(),'no_motion':q[t].copy(),'constant_velocity':2*q[t]-q[t-1],'frozen_unloaded_causal':gain*u[t]+bias}
 # Algebraic check uses only current and past inputs, independently of the helper.
 assert np.max(abs(forecasts['frozen_unloaded_causal']-(q[t]+a*(q[t]-q[t-1])+(1-a)*(u[t]-u[t-1]))))<1e-12
 actual=point(q[t+1]);cop=f.get('rear_cop_centering',{}).get('cop_world');local=R[t].T@(np.asarray(cop)-obj[t]) if cop is not None else None;axis=-np.sign(local[0])*R[t,:,0] if local is not None else None;items=[]
 for name,pred in forecasts.items():
  p=point(pred);item=dict(name=name,position_error_mm=float(np.linalg.norm(p-actual)*1000),joint_error_norm_rad=float(np.linalg.norm(pred-q[t+1])),predicted_motion_mm=((p-current)*1000).tolist())
  if axis is not None:item.update(predicted_inward_mm=float(axis@(p-current)*1000),actual_inward_mm=float(axis@(actual-current)*1000),inward_error_mm=float(axis@(p-actual)*1000))
  items.append(item)
 rows.append(dict(step=t,final_refined=bool(cs[t].get('joint_edge_refinement',{}).get('override')),variants=items))
assert rows
summary={}
for group,chosen in [('all_loaded_with_past',rows),('final_refined',[r for r in rows if r['final_refined']])]:
 if not chosen:continue
 summaries=[]
 for name in forecasts:
  vals=[next(v for v in r['variants'] if v['name']==name) for r in chosen];direct=[v for v in vals if 'inward_error_mm' in v]
  summary_row=dict(name=name,frames=len(vals),median_position_error_mm=float(np.median([v['position_error_mm'] for v in vals])),p90_position_error_mm=float(np.percentile([v['position_error_mm'] for v in vals],90)),direction_samples=len(direct))
  if direct:summary_row.update(median_abs_inward_error_mm=float(np.median([abs(v['inward_error_mm']) for v in direct])),predicted_nonoutward_actual_outward=sum(v['predicted_inward_mm']>=-.0001 and v['actual_inward_mm']<-.05 for v in direct),actual_outward=sum(v['actual_inward_mm']<-.05 for v in direct))
  summaries.append(summary_row)
 summary[group]=summaries
out=dict(episode=ep.name,run=ep.parent.parent.name,summary=summary,excluded_without_loaded_previous=excluded,rows=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','REAR_JOINT_XY_LIVE_AUDIT.json']},archived_geometry_sha256=sha(gp),archived_response_sha256=sha(rp),archived_parameters_sha256=sha(parameter_path),historical_fit_report_sha256=sha(fit_path),checker_sha256=sha(Path(__file__)),training_ready=False,scope=__doc__+' Frozen decay was fitted on earlier unloaded records, not this evaluated loaded trajectory. One-step errors only; contact/phase changes can invalidate extrapolation. No inferred gains exported or applied.')
(ep/'LOADED_CAUSAL_PREDICTION_DIAGNOSIS.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(episode=ep.name,run=out['run'],summary=summary,excluded=excluded),indent=2))
