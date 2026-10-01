"""Reject unsafe interpolation hypotheses; not an executable motion planner."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
s=(w/'screen_lateral_camera_reach.py').read_text();exec(compile(s.split("run=root/'fresh_lateral_00_pilot_r1'")[0],'<validated FK>','exec'))
ep=Path(sys.argv[1]).resolve();region=json.loads((ep/'TOP_CONTACT_REGION_SCREEN.json').read_text());side='left' if 'mailer' in ep.name else 'right';key='mailer' if side=='left' else 'box';other='box' if key=='mailer' else 'mailer';size=(.15,.145,.04) if key=='mailer' else (.14,.09,.045);other_size=(.14,.09,.045) if key=='mailer' else (.15,.145,.04)
with np.load(ep/'raw.npz') as z:q0=z['q'][-1,12:23].astype(float)
with np.load(ep/'trace.npz') as z:tr={k:z[k][-1] for k in z.files}
with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k][-1] for k in z.files}
mesh=np.array(json.loads((repo/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'][side]);limits=np.full(11,.04);limits[0]=.015;rows=[]
for row in region['rows']:
 for fit in row['starts']:
  if not fit['geometric_candidate']:continue
  q1=np.array(fit['q']);n=max(1,int(np.ceil(np.max(abs(q1-q0)/limits))));trace=[]
  for i,alpha in enumerate(np.linspace(0,1,n+1)):
   q=q0+(q1-q0)*alpha;m=transform(side,q);quat=Rotation.from_matrix(m[:3,:3]).as_quat();world=mesh@m[:3,:3].T+m[:3,3];over=(world[:,0]>=.28)&(world[:,0]<=.88)&(abs(world[:,1])<=.75)
   table_min_z=float(world[over,2].min()) if over.any() else None
   other_gap=float(hand_face_separation(side).gap(m[:3,3],quat,tr[other],ori[other],other_size));target_gap=float(hand_face_separation(side).gap(m[:3,3],quat,tr[key],ori[key],size))
   trace.append(dict(step=i,table_hand_min_z=table_min_z,hand_other_gap_m=other_gap,hand_target_gap_m=target_gap))
  min_table=min(x['table_hand_min_z'] for x in trace if x['table_hand_min_z'] is not None);min_other=min(x['hand_other_gap_m'] for x in trace);min_target=min(x['hand_target_gap_m'] for x in trace)
  entry=dict(require_projected_bbox_half=row['require_projected_bbox_half'],top_clearance_m=row['top_clearance_m'],start=fit['start'],joint_step_count=n,max_upper_step_rad=float(np.max(abs(q1-q0))/n),waist_step_rad=float(abs(q1[0]-q0[0])/n),min_sampled_hand_table_clearance_m=min_table-.75,min_sampled_hand_other_gap_m=min_other,min_sampled_hand_target_gap_m=min_target,rejected_for_sampled_penetration=bool(min_table<.746 or min_other<.005 or min_target<-.001),trace=trace)
  rows.append(entry);print(json.dumps({k:v for k,v in entry.items() if k!='trace'}),flush=True)
report=dict(rows=rows,scope='Bounded joint interpolation from actual stalled q to static candidate, fixed recorded parcels. Samples actual active hand hull versus table/objects only. Target penetration below-1mm or other gap below5mm rejects this interpolation hypothesis; passing samples do NOT certify swept/all-arm/self collision, joint tracking, dynamics, force or task completion. Never execute interpolated/optimized q directly. No production controller changed.',source_region_sha256=hashlib.sha256((ep/'TOP_CONTACT_REGION_SCREEN.json').read_bytes()).hexdigest(),raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),training_ready=False)
(ep/'TOP_CONTACT_REGION_PATH_SCREEN.json').write_text(json.dumps(report,indent=2))
