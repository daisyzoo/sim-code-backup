"""Recorded-pose support selector shadow for the new diagonal bag stall."""
from pathlib import Path
import sys,json
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text();exec(compile(source.split('results=[];rng')[0],'<cached_fk>','exec'))
p=Path(sys.argv[1]).resolve();z=np.load(p/'raw.npz');ori=np.load(p/'parcel_orientation.npz');log=json.loads((p/'frontal_bypass.json').read_text())['rows'];mesh=np.asarray(json.loads((root.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices']['left']);heights=[];times=[];recorded=[]
for row in log:
 t=row['step'];q=dict(zip(names,z['q'][t,12:23]));m=np.eye(4)
 for name,origin,axis in chains['left']:
  m=m@origin
  if axis is not None:a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@a
 normal=m[:3,:3].T@Rotation.from_quat(ori['mailer'][t]).as_matrix()[:,2];heights.append(mesh@normal);times.append(t);recorded.append(row['observed_support_offset_local'])
results=[]
for bound in [0.,.0001,.0002,.0005]:
 previous=None;points=[];excess=[]
 for h in heights:
  index=int(np.argmin(h));minimum=h[index]
  if previous is not None and bound>0:
   if h[previous]-minimum<=bound:index=previous
   else:
    allowed=np.flatnonzero(h-minimum<=bound*.25);index=int(allowed[np.argmin(np.sum((mesh[allowed]-mesh[previous])**2,axis=1))])
  points.append(mesh[index]);excess.append(float(h[index]-minimum));previous=index
 jumps=np.linalg.norm(np.diff(points,axis=0),axis=1);window=np.array(times[1:])>=396
 r=dict(height_bound_m=bound,all_changes_over3mm=int((jumps>.003).sum()),stall_changes_over3mm=int((jumps[window]>.003).sum()),stall_changes_over8mm=int((jumps[window]>.008).sum()),stall_max_virtual_change_m=float(jumps[window].max()),max_support_plane_excess_m=max(excess),max_local_difference_from_actual_log_m=float(np.linalg.norm(np.array(points)-recorded,axis=1).max()) if bound==0 else None);results.append(r);print(json.dumps(r),flush=True)
(p/'STALL_HYSTERESIS_SHADOW.json').write_text(json.dumps(dict(rows=results,scope='Actual hand/parcel poses fixed, independent FK and vectorized existing real-vertex hysteresis formula. 396..959 is the observed uninterrupted descent stall. Virtual reference changes are not hand teleportation; no commands/dynamics rerun, no causal or task-success claim. Actual current collector permits hysteresis only together with collision-core corner route; decoupling needs explicit future diagnostic code review, not silently changing active settings.',training_ready=False),indent=2))
