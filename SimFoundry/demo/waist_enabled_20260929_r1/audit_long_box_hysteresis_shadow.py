"""Offline-only selector sensitivity on recorded poses; not closed-loop evidence."""
from pathlib import Path
import sys,json
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
run=Path(sys.argv[1]).resolve();mesh=json.loads((root.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'];rows=[]
for ep in sorted(run.glob('case_*/layout_*push_box_to_bin')):
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';z=np.load(ep/'raw.npz');ori=np.load(ep/'parcel_orientation.npz');log=json.loads((ep/'frontal_bypass.json').read_text())['rows'];vertices=np.array(mesh[side]);series=[]
 for row in log:
  if row.get('control_offset_local') is None:continue
  t=row['step'];q=dict(zip(names,z['q'][t,12:23]));m=np.eye(4);m[:3,3]=[.08,0,.793]
  for name,orig,axis in chains[side]:
   m=m@orig
   if axis is not None:
    a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@a
  normal=m[:3,:3].T@Rotation.from_quat(ori[key][t]).as_matrix()[:,2];series.append((t,normal))
 variants=[]
 for tolerance in (.0001,.0002,.0003,.0005):
  previous=None;selected=[];excess=[];changes=[]
  for t,normal in series:
   heights=vertices@normal;idx=int(np.argmin(heights));minimum=heights[idx]
   if previous is not None:
    if heights[previous]-minimum<=tolerance:idx=previous
    else:
     candidates=np.flatnonzero(heights-minimum<=tolerance*.25)
     idx=int(candidates[np.argmin(np.linalg.norm(vertices[candidates]-vertices[previous],axis=1))])
    jump=float(np.linalg.norm(vertices[idx]-vertices[previous]));changes.append((t,jump))
   selected.append(vertices[idx]);excess.append(float(heights[idx]-minimum));previous=idx
  variants.append(dict(tolerance_m=tolerance,max_height_above_true_support_m=max(excess),max_vertex_jump_m=max(j for t,j in changes),changes_over_3mm=sum(j>.003 for t,j in changes),total_jump_path_m=sum(j for t,j in changes),late_changes_over_3mm=sum(j>.003 for t,j in changes if t>=800),stall_window_changes_over_3mm=sum(j>.003 for t,j in changes if 878<=t<=1127)))
 rows.append(dict(episode=ep.name,variants=variants))
out=dict(rows=rows,scope='Shadow selector only on unchanged historical poses. Retain previous real mesh vertex if within height tolerance, otherwise nearest candidate within quarter tolerance. No dynamics or contact geometry guarantee; height difference needs explicit accounting if used. No actual action executed.',training_ready=False)
(run/'BOX_SUPPORT_HYSTERESIS_SHADOW.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
