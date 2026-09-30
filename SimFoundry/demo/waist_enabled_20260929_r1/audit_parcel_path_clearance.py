"""Conservative core XY projection separation along actual paths; no control writes."""
from pathlib import Path
import json,sys,itertools
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
run=Path(sys.argv[1]).resolve();rows=[]
sizes={'box':np.array([.14*.96,.09*.96,.045]),'mailer':np.array([.15*.90,.145*.88,.04])}
vertices={k:np.array(list(itertools.product([-1,1],repeat=3)))*size/2 for k,size in sizes.items()}
for ep in sorted(run.glob('case_*/layout_*')):
 tr=np.load(ep/'trace.npz');ori=np.load(ep/'parcel_orientation.npz');log=json.loads((ep/'frontal_bypass.json').read_text());modes={r['step']:r['mode'] for r in json.loads((ep/'expert_control.json').read_text())};records=[]
 for t in range(len(tr['box'])):
  hulls={}
  for key in sizes:
   xy=(vertices[key]@Rotation.from_quat(ori[key][t]).as_matrix().T+tr[key][t])[:,:2];hulls[key]=xy[ConvexHull(xy).vertices]
  axes=[]
  for hull in hulls.values():
   edge=np.roll(hull,-1,axis=0)-hull
   normals=np.c_[-edge[:,1],edge[:,0]];axes.extend(normals/np.linalg.norm(normals,axis=1)[:,None])
  axes=np.array(axes);a=hulls['box']@axes.T;b=hulls['mailer']@axes.T
  gaps=np.maximum(a.min(0)-b.max(0),b.min(0)-a.max(0));sep=float(gaps.max())
  records.append(dict(frame=t,mode=modes.get(t,'zero_initial'),max_separating_axis_gap_m=sep,xy_projections_overlap=sep<0))
 force=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];contact=[]
 for packet in force:
  for c in packet['parcel_contacts']:
   if any('/mailer/' in s for s in c['shapes']) and any('/parcel_box/' in s for s in c['shapes']):
    contact.append(dict(after_action_step=packet['after_action_step'],force_norm_n=float(np.linalg.norm(c['force_world_N']))))
 rows.append(dict(episode=ep.name,min_projected_separating_gap_m=min(r['max_separating_axis_gap_m'] for r in records),xy_overlap_frames=sum(r['xy_projections_overlap'] for r in records),parcel_parcel_contact_samples=contact,max_recorded_parcel_contact_force_n=max((r['force_norm_n'] for r in contact),default=0),records=records))
 print(ep.name,'min axis gap',rows[-1]['min_projected_separating_gap_m'],'XY overlap',rows[-1]['xy_overlap_frames'],'parcel contact maxN',rows[-1]['max_recorded_parcel_contact_force_n'])
(run/'PARCEL_PATH_CLEARANCE_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Actual pre-action poses and projected actual Cube core vertices; full convex projected polygons, separating-axis max gap is not Euclidean distance. Negative means XY shadows overlap, not proof of 3D penetration. Sizes match separately measured collector core. Solved parcel-parcel contact forces are last-tick samples, not all-substep guarantee. No new quality gate or admission.',training_ready=False),indent=2))
