"""Actual target/obstacle contact evidence, with force threshold excluding zero manifolds.
Last-substep samples only; no integrated impulse or single-cause assertion.
Other-parcel displacement below the gate does not imply absence of obstruction.
"""
from pathlib import Path
import json,hashlib,datetime,collections
import numpy as np
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();results=[]
for run in ['minimum_motion_groups_r1','rear_slow_drag_groups_r1','rear_box_rate_groups_r1','box_center_groups_r1','box_entry_lift_groups_r1']:
 ep=w/run/'case_840001/layout_840001_push_box_to_bin';packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];fr=json.loads((ep/'frontal_bypass.json').read_text());fs={r['step']:r for r in fr['rows']}
 with np.load(ep/'trace.npz') as z:xyz=z['box'].astype(float);other=z['mailer'].astype(float)
 n=len(xyz);samples=[];touch={};allpairs=set();force_shapes=set()
 for p in packets:
  t=p['after_action_step']+1
  if t>=n:continue
  assert p['solver_force_buffer_unchanged'] and np.max(abs(p['post_action_pose']['box']-xyz[t]))<1e-6
  total=np.zeros(3);magnitudes=[];pairs=[]
  for c in p['parcel_contacts']:
   box=[i for i,s in enumerate(c['shapes']) if '/parcel_box/' in s];bag=[i for i,s in enumerate(c['shapes']) if '/mailer/' in s]
   if not(box and bag):continue
   assert len(box)==len(bag)==1 and box[0]!=bag[0];allpairs.add(tuple(c['shapes']));F=np.asarray(c['force_world_N'],float)*(1 if box[0]==1 else -1);total+=F;magnitudes.append(float(np.linalg.norm(F)));pairs.append(c['shapes'])
  if magnitudes:
   force_sum=sum(magnitudes);rec=dict(step=t,pair_force_magnitude_sum_n=force_sum,force_on_box_world_n=total.tolist(),box_xyz=xyz[t].tolist(),bag_xyz=other[t].tolist(),mode=fs[t]['mode'])
   if force_sum>.05:touch[t]=rec;force_shapes.update(tuple(p) for p in pairs)
   samples.append(rec)
 def stats(steps):
  steps=[t for t in steps if t<n-1];push=[t for t in steps if fs[t]['mode']=='top_push' and fs[t]['contact_load']['observed_vertical_load_n']>=.3];dy=[-(xyz[t+1,1]-xyz[t,1])*1000 for t in push]
  return dict(frames=len(steps),loaded_push_frames=len(push),loaded_net_progress_mm=float(sum(dy)),loaded_mean_progress_mm_per_frame=float(np.mean(dy)) if dy else None)
 first=min(touch) if touch else None
 intervals=[];active=None
 for t in sorted(touch):
  if active and t==active[-1]+1:active.append(t)
  else:
   if active:intervals.append(active)
   active=[t]
 if active:intervals.append(active)
 out=dict(run=run,episode=ep.name,manifold_frames=len(samples),force_gt_005N_frames=len(touch),first_nonzero=touch[first] if first else None,last_nonzero=touch[max(touch)] if touch else None,peak_sum_contact_magnitudes_n=max((x['pair_force_magnitude_sum_n'] for x in samples),default=0),non_target_max_xy_mm=float(np.max(np.linalg.norm(other[:,:2]-other[0,:2],axis=1))*1000),nonzero_shapes=[list(x) for x in sorted(force_shapes)],intervals=[dict(start=a[0],end=a[-1],frames=len(a)) for a in intervals],before_first=stats(range(1,first or n)),after_first=stats(range(first,n)) if first else None,during_nonzero=stats(touch),source_sha256={name:sha(ep/name) for name in ['solved_contact_forces.json','trace.npz','frontal_bypass.json']})
 results.append(out);print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','intervals']},indent=2),flush=True)
report=dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),force_threshold_n=.05,episodes=results,source_sha256={str(Path(__file__)):sha(__file__)},training_ready=False)
(w/'box_entry_lift_groups_r1/PARCEL_INTERFERENCE_DIAGNOSTIC.json').write_text(json.dumps(report,indent=2))
