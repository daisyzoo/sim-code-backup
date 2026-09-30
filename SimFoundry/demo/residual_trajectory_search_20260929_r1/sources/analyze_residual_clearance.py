#!/usr/bin/env python3
import argparse,hashlib,json,itertools
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from shapely.geometry import MultiPoint
p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();rows=[]
for meta_path in sorted(a.candidate.glob('case_*.json')):
 m=json.loads(meta_path.read_text());raw=meta_path.with_suffix('.npz');assert hashlib.sha256(raw.read_bytes()).hexdigest()==m['sha256'];task=m['source']['task'];target='box' if task=='push_box_to_bin' else 'mailer';other='mailer' if target=='box' else 'box'
 with np.load(raw) as z:
  shapes={};xz={}
  for key,size in [('box',[.14,.09,.045]),('mailer',[.15,.145,.04])]:
   rot=Rotation.from_quat(z[key+'_quat']).as_matrix();corners=np.asarray(list(itertools.product([-1,1],repeat=3)))*np.asarray(size)/2;points=np.einsum('tij,kj->tki',rot,corners)+z[key][:,None,:];shapes[key]=[MultiPoint(v[:,:2]).convex_hull for v in points]
  distance=np.array([x.distance(y) for x,y in zip(shapes['box'],shapes['mailer'])]);closest=int(np.argmin(distance));t=z[target];o=z[other]
  rows.append(dict(layout_id=m['source']['layout_id'],task=task,passed=m['report']['passed'],raw_sha256=m['sha256'],min_projected_clearance_m=float(distance.min()),min_clearance_frame=closest,final_clearance_m=float(distance[-1]),initial_target=t[0].tolist(),final_target=t[-1].tolist(),target_delta=(t[-1]-t[0]).tolist(),non_target_max_xy_m=float(np.linalg.norm(o[:,:2]-o[0,:2],axis=1).max()),target_at_min_clearance=t[closest].tolist()))
a.out.write_text(json.dumps(dict(candidate=str(a.candidate.resolve()),rows=rows,scope='Distance between projected nominal3D parcel boxes using recorded quaternion. Geometry only, not contact forces or continuous between-frame collision proof.',training_ready=False,goal_complete=False),indent=2))
for r in rows:print(r['layout_id'],r['task'],'pass',r['passed'],'delta',r['target_delta'],'min_gap',r['min_projected_clearance_m'],'last_gap',r['final_clearance_m'],flush=True)
