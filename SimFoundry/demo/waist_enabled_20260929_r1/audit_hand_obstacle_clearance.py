"""Actual hand hull/other parcel SAT at selected frames; no robot commands executed."""
from pathlib import Path
import json,sys,itertools
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text();exec(compile(source.split('results=[];rng')[0],'<cached_fk>','exec'))
run=Path(sys.argv[1]).resolve();mesh=json.loads((root.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'];rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 if not (ep/'raw.npz').exists():continue
 side='right' if 'push_box' in ep.name else 'left';other='mailer' if side=='right' else 'box';actor='mailer' if other=='mailer' else 'parcel_box'
 points=np.asarray(mesh[side]);hull=ConvexHull(points);vertices=points[hull.vertices];face_axes=hull.equations[:,:3];edges=set()
 for face in hull.simplices:
  for a,b in [(face[0],face[1]),(face[0],face[2]),(face[1],face[2])]:edges.add(tuple(sorted((int(a),int(b)))))
 edgevec=np.array([points[b]-points[a] for a,b in edges]);edgevec/=np.linalg.norm(edgevec,axis=1)[:,None]
 z=np.load(ep/'raw.npz');tr=np.load(ep/'trace.npz');ori=np.load(ep/'parcel_orientation.npz');log={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];events=[]
 for p in packets:
  selected=[c for c in p['parcel_contacts'] if any('/'+actor+'/' in s for s in c['shapes']) and any(side+'_wrist' in s for s in c['shapes'])]
  force=sum(float(np.linalg.norm(c['force_world_N'])) for c in selected)
  if force>.05:events.append(dict(after_action_step=p['after_action_step'],hand_other_force_n=force))
 control_modes={r['step']:r['mode'] for r in json.loads((ep/'expert_control.json').read_text())}
 times=set(range(0,len(z['q']),20))|{len(z['q'])-1}
 for t,row in log.items():
  if row.get('last_recontact_reason')=='hand_obstacle_clearance' and row.get('recontacts',0)>log.get(t-1,{}).get('recontacts',0):times.update(range(max(0,t-3),min(len(z['q']),t+4)))
 for e in events:times.update(range(max(0,e['after_action_step']-5),min(len(z['q']),e['after_action_step']+3)))
 half=np.array([.1344,.0864,.045] if other=='box' else [.135,.1276,.04])/2;cube=np.array(list(itertools.product([-1,1],repeat=3)))*half;records=[]
 for t in sorted(times):
  q=dict(zip(names,z['q'][t,12:23]));m=np.eye(4);m[:3,3]=[.08,0,.793]
  for name,origin,axis in chains[side]:
   m=m@origin
   if axis is not None:a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@a
  rh=m[:3,:3];rb=Rotation.from_quat(ori[other][t]).as_matrix();hand=vertices@rh.T+m[:3,3];box=cube@rb.T+tr[other][t]
  cross=np.cross((edgevec@rh.T)[:,None,:],rb.T[None,:,:]).reshape(-1,3);cross=cross[np.linalg.norm(cross,axis=1)>1e-9];cross/=np.linalg.norm(cross,axis=1)[:,None]
  axes=np.concatenate([face_axes@rh.T,rb.T,cross]);axes=np.unique(np.round(axes,9),axis=0);axes/=np.linalg.norm(axes,axis=1)[:,None]
  face=np.concatenate([face_axes@rh.T,rb.T]);fa=hand@face.T;fb=box@face.T;face_gap=float(np.maximum(fa.min(0)-fb.max(0),fb.min(0)-fa.max(0)).max())
  a=hand@axes.T;b=box@axes.T;gaps=np.maximum(a.min(0)-b.max(0),b.min(0)-a.max(0));gap=float(gaps.max())
  shifted=[]
  for shift in [.01,.02,.03]:
   aa=a+shift*axes[:,0];gg=np.maximum(aa.min(0)-b.max(0),b.min(0)-aa.max(0));shifted.append(float(gg.max()))
  records.append(dict(frame=t,mode=control_modes.get(t,'unrecorded'),independent_face_axis_gap_m=face_gap,logged_face_axis_gap_m=log.get(t,{}).get('hand_obstacle_gap_m'),max_separating_axis_gap_m=gap,hand_convex_hull_overlaps_other_core=gap<0,static_hand_translation_positive_x_gaps_m=shifted))
 row=dict(episode=ep.name,other=other,hand_convex_hull_vertices=len(vertices),contact_events=events,checked_frames=len(records),min_sampled_gap_m=min(x['max_separating_axis_gap_m'] for x in records),records=records);rows.append(row)
 print(ep.name,'hand-other contact samples',len(events),'maxforce',max((e['hand_other_force_n'] for e in events),default=0),'min sampled SAT gap',row['min_sampled_gap_m'],'hullvertices',len(vertices),flush=True)
(run/'HAND_OBSTACLE_CLEARANCE_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Independent URDF FK and convex hull of actual hand collision vertices against actual other-parcel Cube core. Complete convex polyhedron SAT axes (face normals and crossed edge directions); max signed axis gap is not Euclidean distance. Every20 frames plus force-event neighborhoods, not all-substep path certification. Hypothetical whole-hand +X translations10/20/30mm are static geometry only, not solved IK/contact-preserving commands or executed actions. Contact forces are recorded last tick.',training_ready=False),indent=2))
