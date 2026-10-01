"""Recorded phase/load/progress accounting, not a controller change or admission."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;ep=Path(sys.argv[1]).resolve();assert 'nudge_mailer' in ep.name;assert (ep/'quality.json').exists()
log=json.loads((ep/'frontal_bypass.json').read_text());assert log['plan']['front_route_selected'];rows=log['rows']
with np.load(ep/'trace.npz') as z:target=z['mailer'].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:yaw=Rotation.from_quat(z['mailer']).as_euler('xyz')[:,2]
assert target.shape==(1200,3) and len(rows)==1199
bins={};events=[];prev=0
for r in rows:
 t=r['step'];stage=r['route_stage'];mode=r['mode'];k=stage+'/'+mode
 b=bins.setdefault(k,dict(frames=0,observed_load_ge_0p3_frames=0,delta_xy_m=[0.,0.],delta_yaw_rad=0.,virtual_support_offset_x_m=[],virtual_support_offset_y_m=[]))
 b['frames']+=1;b['observed_load_ge_0p3_frames']+=int(r.get('contact_load',{}).get('observed_vertical_load_n',0.)>=.3)
 if t+1<len(target):
  b['delta_xy_m']=(np.asarray(b['delta_xy_m'])+target[t+1,:2]-target[t,:2]).tolist();b['delta_yaw_rad']+=float(np.arctan2(np.sin(yaw[t+1]-yaw[t]),np.cos(yaw[t+1]-yaw[t])))
 offset=np.asarray(r['observed_support_xyz'])-target[t];b['virtual_support_offset_x_m'].append(float(offset[0]));b['virtual_support_offset_y_m'].append(float(offset[1]))
 if r['recontacts']>prev:
  events.append(dict(step=t,route_stage=stage,reason=r['last_recontact_reason'],recontacts=r['recontacts'],target_xyz=target[t].tolist(),yaw_rad=float(yaw[t]),tilt_rad=r['observed_parcel_tilt_rad'],load_n=r['contact_load']['observed_vertical_load_n']))
 prev=r['recontacts']
for b in bins.values():
 for name in ['virtual_support_offset_x_m','virtual_support_offset_y_m']:
  a=b.pop(name);b[name+'_min_median_max']=[float(x) for x in np.quantile(a,[0,.5,1])]
result=dict(episode=ep.name,bins=bins,recontacts=events,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),frontal_sha256=hashlib.sha256((ep/'frontal_bypass.json').read_bytes()).hexdigest(),scope='Phase bins use pre-action mode/last measured load and t-to-t+1 motion; last frame has no following observation. Load is recorded sample, not sustained contact truth or force integral. Virtual reference offset is not actual loaded COP. No automatic trajectory admission or assumed benefit from longer rollout.',training_ready=False)
(ep/'FRONT_WORK_EFFICIENCY.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
