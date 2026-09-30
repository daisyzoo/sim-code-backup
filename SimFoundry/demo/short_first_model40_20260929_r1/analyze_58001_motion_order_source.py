from pathlib import Path
import numpy as np,json,hashlib
r=Path('SimFoundry/demo/short_first_model40_20260929_r1');rows=[]
for seed in [0,1,2]:
 p=r/f'evaluation/new_spatial160_seed{seed}/layout_58001/layout_58001_push_box_to_bin';q=json.loads((p/'quality.json').read_text());assert q['frames']==160
 with np.load(p/'trace.npz') as d:
  arrays={k:d[k].copy() for k in d.files}
  move={k:np.linalg.norm(d[k][:,:2]-d[k][0,:2],axis=1) for k in ['box','mailer']}
  events=[]
  for obj in ['box','mailer']:
   for threshold in [.002,.005,.015]:
    hits=np.flatnonzero(move[obj]>threshold);t=int(hits[0]) if len(hits) else None
    events.append(dict(object=obj,xy_displacement_threshold_m=threshold,first_frame=t,right_palm_xyz=None if t is None else d['palm_right'][t].tolist(),box_xyz=None if t is None else d['box'][t].tolist(),mailer_xyz=None if t is None else d['mailer'][t].tolist()))
  segment=[]
  for lo,hi in [(0,39),(40,79),(80,119),(120,159)]:segment.append(dict(start=lo,end=hi,box_max_displacement_m=float(move['box'][lo:hi+1].max()),mailer_max_displacement_m=float(move['mailer'][lo:hi+1].max())))
 rows.append(dict(seed=seed,passed=q['passed'],events=events,segments=segment,trace_sha256=hashlib.sha256((p/'trace.npz').read_bytes()).hexdigest()))
p=r/'LAYOUT58001_BOX_MOTION_ORDER.json';assert not p.exists();p.write_text(json.dumps(dict(rows=rows,scope='Recorded pre-action XY displacement thresholds, not contact onset or force causation. Threshold crossings may follow initial contact; sparse video cannot resolve exact contact.',goal_complete=False),indent=2))
for row in rows:print(row['seed'],row['passed'],[(x['object'],x['xy_displacement_threshold_m'],x['first_frame']) for x in row['events']])
