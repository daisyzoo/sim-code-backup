"""Bounded near-support convex centroid shadow, unchanged recorded hand poses only."""
from pathlib import Path
import json,sys
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text();exec(compile(source.split('results=[];rng')[0],'<cached_fk>','exec'))
run=Path(sys.argv[1]).resolve();mesh=json.loads((root.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'];out=[]
for ep in sorted(run.glob('case_*/layout_*')):
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';z=np.load(ep/'raw.npz');ori=np.load(ep/'parcel_orientation.npz');log=json.loads((ep/'frontal_bypass.json').read_text())['rows'];vertices=np.array(mesh[side]);old=[];centroid=[];excess=[];times=[]
 for row in log:
  if row.get('control_offset_local') is None:continue
  t=row['step'];q=dict(zip(names,z['q'][t,12:23]));m=np.eye(4)
  for name,orig,axis in chains[side]:
   m=m@orig
   if axis is not None:a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@a
  normal=m[:3,:3].T@Rotation.from_quat(ori[key][t]).as_matrix()[:,2];h=vertices@normal;delta=h-h.min();w=np.maximum(0,1-delta/.0002)**2;point=w@vertices/w.sum();centroid.append(point);old.append(row['control_offset_local']);excess.append(float(point@normal-h.min()));times.append(t)
 def stats(points):
  jumps=np.linalg.norm(np.diff(points,axis=0),axis=1);window=np.array(times[1:])>=1230
  return dict(max_local_reference_change_m=float(jumps.max()),count_over3mm=int((jumps>.003).sum()),terminal_window_max_m=float(jumps[window].max()),terminal_window_count_over3mm=int((jumps[window]>.003).sum()))
 r=dict(episode=ep.name,old=stats(np.array(old)),centroid=stats(np.array(centroid)),max_support_plane_excess_m=max(excess));out.append(r);print(json.dumps(r),flush=True)
(run/'SUPPORT_CENTROID_SHADOW.json').write_text(json.dumps(dict(rows=out,definition='Convex weighted centroid of actual hand vertices within0.2mm of exact support plane, weights=max(0,1-excess/0.2mm)^2. Virtual control reference may lie inside convex hull, NOT a real surface vertex/contact point; exact support and whole-hull collision still require separate observation. No mesh/physics change. Unchanged-pose shadow is not closed-loop/IK proof.',training_ready=False),indent=2))
