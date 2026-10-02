"""Offline causal one-step object-surface motion baselines on recorded commands.
Current COP defines a material point; future measured poses score only. Predictions
use current/previous poses, never future state. Not a counterfactual dynamics model.
No new controller, no parameter selection on independent policy evaluation layouts.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;r=w/'box_entry_lift_groups_r1';source=r/'RELATIVE_MOTION_DECOMPOSITION.json';d=json.loads(source.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();out=[]
def metrics(rows):
 ans={}
 for name in ['stationary','constant_twist','half_twist']:
  z=np.array([x['models'][name]['world_error_mm'] for x in rows]).reshape(-1,3);norm=np.linalg.norm(z,axis=1)
  ans[name]=dict(n=len(rows),median_norm_mm=float(np.median(norm)) if len(rows) else None,p95_norm_mm=float(np.quantile(norm,.95)) if len(rows) else None,max_norm_mm=float(max(norm)) if len(rows) else None,mean_abs_xyz_mm=np.mean(abs(z),axis=0).tolist() if len(rows) else None)
 return ans
for episode in d['episodes']:
 ep=next(r.glob('case_*/'+episode['episode']));key='box' if 'push_box' in ep.name else 'mailer'
 for name,h in episode['source_sha256'].items():assert sha(ep/name)==h,name
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z[key]).as_matrix()
 rows=[]
 for rec in episode['records']:
  t=rec['step'];local=np.array(rec['cop_local_mm'])/1000;cop=xyz[t]+R[t]@local;actual=xyz[t+1]+R[t+1]@local;translation=xyz[t]-xyz[t-1];relative=Rotation.from_matrix(R[t]@R[t-1].T);models={}
  for name,scale in [('stationary',0.),('constant_twist',1.),('half_twist',.5)]:
   G=Rotation.from_rotvec(relative.as_rotvec()*scale).as_matrix();pred=xyz[t]+scale*translation+G@(cop-xyz[t]);models[name]=dict(world_error_mm=((pred-actual)*1000).tolist(),predicted_surface_delta_mm=((pred-cop)*1000).tolist())
  rows.append(dict(step=t,near_tilt=rec['near_tilt'],near_loss=rec['near_loss'],edge_verified=rec['edge_verified'],actual_surface_delta_mm=((actual-cop)*1000).tolist(),models=models))
 e=dict(episode=ep.name,all=metrics(rows),near_tilt=metrics([x for x in rows if x['near_tilt']]),near_loss=metrics([x for x in rows if x['near_loss']]),records=rows,source_sha256={name:sha(ep/name) for name in ['trace.npz','parcel_orientation.npz']});out.append(e);print(ep.name,json.dumps({k:v for k,v in e.items() if k in ['all','near_tilt','near_loss']}),flush=True)
(r/'OBJECT_MOTION_PREDICTION_DIAGNOSTIC.json').write_text(json.dumps(dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),episodes=out,source_sha256={str(p):sha(p) for p in [Path(__file__),source]},training_ready=False),indent=2))
