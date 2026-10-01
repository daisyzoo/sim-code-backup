"""Score completed actual region forecasts against next measured states; no fitting."""
from pathlib import Path
import json,sys,hashlib,collections
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w/'staged_contact_patch_approach'),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
from scipy.spatial.transform import Rotation
p=Path(sys.argv[1]).resolve();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
with np.load(p/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float);task=str(z['task_id'])
assert len(q)==1200 and (p/'quality.json').exists()
with np.load(p/'trace.npz') as z:tr={k:z[k] for k in z.files}
with np.load(p/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
rows=json.loads((p/'region_approach.json').read_text())['rows'];side='right' if task=='push_box_to_bin' else 'left';key='box' if side=='right' else 'mailer';model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');prov=json.loads((p.parent/'provenance.json').read_text())
for f in ['third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf','assets/robots/g1_hand_support_vertices.json','simfoundry/calibration/sorting_station.py']:assert sha(repo/f)==prov['source_sha256'][f]
errors=[];details=[];fkerror=0.;core=None
for row in rows:
 t=row['step'];s=row['solver']
 if not s or not s.get('joint_override') or s.get('handover') or t+1>=len(q):continue
 assert t>0;c=s['causal_response'];a=np.array(c['decay']);g=1-a;b=a*q[t]+(q[t]-u[t-1])-a*(q[t-1]-u[t-1]);pred=g*u[t]+b
 assert np.max(abs(g-np.array(c['gain'])))<2e-6 and np.max(abs(b-np.array(c['offset'])))<2e-6
 core=np.array(c['core_scale']);R=Rotation.from_quat(ori[key][t+1]).as_matrix();xyz=tr[key][t+1]
 def point(v):
  T=model.fk(side,v)[0];pts=(model.vertices[side]@T[:3,:3].T+T[:3,3]-xyz)@R;return pts[pts[:,2].argmin()],T
 actual,T=point(q[t+1]);forecast,_=point(pred);held,_=point(u[t]+q[t]-u[t-1]);fkerror=max(fkerror,float(np.max(abs(T[:3,3]+T[:3,:3]@np.array([.2,0,.007])-tr['palm_'+side][t+1]))))
 size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);half=size[:2]*core[:2]/2-.01
 details.append(dict(step=t,actual_next_top_gap_mm=float((actual[2]-size[2]/2)*1000),actual_next_core_margin_mm=((half-abs(actual[:2]))*1000).tolist(),causal_height_error_mm=float((forecast[2]-actual[2])*1000),held_residual_height_error_mm=float((held[2]-actual[2])*1000),causal_max_joint_error_rad=float(np.max(abs(pred-q[t+1]))),command_step_rad=float(np.max(abs(u[t]-u[t-1]))),solver_record=s))
assert fkerror<2e-6
metrics={}
for name in ['causal_height_error_mm','held_residual_height_error_mm','causal_max_joint_error_rad']:
 v=np.array([r[name] for r in details]);metrics[name]=dict(n=len(v),rmse=float(np.sqrt(np.mean(v*v))),p95_abs=float(np.percentile(abs(v),95)),max_abs=float(np.max(abs(v)))) if len(v) else None
selected=[r for r in rows if r['solver']];out=dict(episode=p.name,quality=json.loads((p/'quality.json').read_text()),solver_reason_counts=dict(collections.Counter(r['solver'].get('reason','') for r in selected)),handover_steps=[r['step'] for r in selected if r['solver'].get('handover')],metrics=metrics,actual_fk_palm_error_m=fkerror,first_forecast=details[0] if details else None,last_forecast=details[-1] if details else None,forecast_rows=details,raw_sha256=sha(p/'raw.npz'),source_sha256={f:sha(p/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','region_approach.json','quality.json']},script_sha256=sha(Path(__file__)),scope='Completed real episode next-state prediction error and actual core margins. All region joint overrides retained; no new fitting. Cannot establish full-interval absence of contacts or task success beyond original quality.',training_ready=False)
(p/'CAUSAL_ACTUAL_RESPONSE_DIAGNOSIS.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['forecast_rows','first_forecast','last_forecast','source_sha256']},indent=2))
