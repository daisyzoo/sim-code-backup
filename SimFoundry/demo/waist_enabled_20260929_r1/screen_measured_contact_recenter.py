"""Continuous lift/recenter screen from actual initial contact; no physics/commands."""
from pathlib import Path
import sys,json,hashlib
requested=Path(sys.argv[1]).resolve()
root=Path(__file__).resolve().parent
source=(root/'check_staged_contact_normal.py').read_text()
exec(compile(source.split("ep=root/'terminal_hold_front09")[0],'<actual_solver_fk_setup>','exec'))
from simfoundry.data.hand_obstacle_clearance import hand_face_separation
p=requested
with np.load(p/'raw.npz') as z:qs=z['q'].copy()
with np.load(p/'trace.npz') as z:tr={k:z[k].copy() for k in z.files}
with np.load(p/'parcel_orientation.npz') as z:ori={k:z[k].copy() for k in z.files}
ctrl={r['step']:r for r in json.loads((p/'expert_control.json').read_text())}
coord={r['step']:r for r in json.loads((p/'coordination.json').read_text())}
front={r['step']:r for r in json.loads((p/'frontal_bypass.json').read_text())['rows']}
side='right' if 'push_box' in p.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';actor='parcel_box' if key=='box' else 'mailer';inactive_side='left' if side=='right' else 'right'
start=next(t for t,r in ctrl.items() if r['mode']=='top_push')
packets=json.loads((p/'solved_contact_forces.json').read_text())['rows'];samples=[]
for packet in packets:
 t=packet['after_action_step']
 if not start-3<=t<start or ctrl[t]['mode']!='top_press':continue
 pts=[];weights=[]
 for c in packet['parcel_contacts']:
  slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
  if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
  force=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1)
  if -force[2]>.05:pts.append(c['position_world']);weights.append(-force[2])
 if not weights:continue
 cop=np.average(pts,axis=0,weights=weights);m=transform(side,qs[t+1,12:]);local=m[:3,:3].T@(cop-m[:3,3]);samples.append(dict(step=t,load_n=sum(weights),local=local.tolist(),cop_world=cop.tolist()))
assert len(samples)==3 and min(s['load_n'] for s in samples)>.3
center=np.median([s['local'] for s in samples],axis=0);scatter=float(np.max(np.linalg.norm(np.array([s['local'] for s in samples])-center,axis=1)))
mesh=np.asarray(json.loads((repo/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'][side]);q=qs[start,12:].astype(float);normal=np.array(coord[start]['contact_normal_tracking']['target_local_up']);inactive=np.array(coord[start]['inactive_anchor']);n=np.array([0.,0.,1.]);target0=tr[key][start];obstacle=tr[other][start];obstacle_q=ori[other][start];other_size=[.15,.145,.04] if key=='box' else [.14,.09,.045]
def ref(v):
 m=transform(side,v);world=mesh@m[:3,:3].T+m[:3,3];ix=int(np.argmin(world[:,2]));wc=m[:3,:3]@center+m[:3,3];point=wc+n*(world[ix,2]-wc[2]);local=m[:3,:3].T@(point-m[:3,3]);return point,dict(reference_local=local,center_local=center,lowest_vertex_local=mesh[ix],world_normal=n)
initial,_=ref(q);goals=[];prior=initial.copy()
def segment(dest,stage):
 global prior
 dest=np.array(dest);count=max(1,int(np.ceil(np.max(abs(dest-prior))/.003)))
 for ratio in np.linspace(0,1,count+1)[1:]:goals.append((prior+(dest-prior)*ratio,stage))
 prior=dest
high=.86 if 'route_goal_x' in front[start] else .91
segment([initial[0],initial[1],high],'unload_lift')
segment([target0[0],target0[1],high],'recenter_air')
segment([target0[0],target0[1],target0[2]+(.0225 if key=='box' else .02)],'descent')
for _ in range(20):goals.append((prior.copy(),'settle'))
x=front[start].get('route_goal_x',target0[0]);segment([x,target0[1],prior[2]],'front_x')
segment([x,-.205 if key=='box' else .205,prior[2]],'lateral_y')
for _ in range(20):goals.append((prior.copy(),'settle'))
records=[];clearance=hand_face_separation(side)
for k,(goal,phase) in enumerate(goals):
 for _ in range(4):
  robot=robot_at(q);point,reference=ref(q);a=np.zeros(23)
  live(robot,{'left':1,'right':2},a,state=NS(side=side,last_target_xyz=goal),anchor={inactive_side:inactive},default=np.zeros(23),waist_limit=1.,bounded=True,active_point_offset=reference['reference_local'],active_support_reference=reference,active_normal_anchor_local=normal,trace_jacobian=True)
  dq=a[12:]-q;assert np.max(abs(dq))<=.04000001 and abs(dq[0])<=.01500001;q=a[12:].copy()
 m=transform(side,q);other_m=transform(inactive_side,q);point,_=ref(q)
 records.append(dict(waypoint=k,phase=phase,goal=goal.tolist(),q=q.tolist(),active_error_m=float(np.linalg.norm(point-goal)),inactive_error_m=float(np.linalg.norm(other_m[:3,:3]@np.array(PALM_OFFSET)+other_m[:3,3]-inactive)),normal_error_deg=float(np.degrees(np.arccos(np.clip((m[:3,:3].T@n)@normal,-1,1)))),hand_obstacle_face_gap_m=clearance.gap(m[:3,3],Rotation.from_matrix(m[:3,:3]).as_quat(),obstacle,obstacle_q,other_size)))
summary=dict(waypoints=len(records),solver_steps=4*len(records),contact_local_scatter_m=scatter,max_active_error_m=max(r['active_error_m'] for r in records),max_inactive_error_m=max(r['inactive_error_m'] for r in records),max_normal_error_deg=max(r['normal_error_deg'] for r in records),min_hand_obstacle_face_gap_m=min(r['hand_obstacle_face_gap_m'] for r in records),max_waist_rad=max(abs(r['q'][0]) for r in records),hypothetical_recenter_xy_m=(target0[:2]-initial[:2]).tolist())
protocol=json.loads((p.parents[1]/'PROTOCOL.json').read_text())
for name,h in protocol['source_sha256'].items():assert sha(name)==h,name
out=dict(summary=summary,measured_samples=samples,contact_tangent_center_local=center.tolist(),records=records,source_sha256={f:sha(p/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','expert_control.json','coordination.json','frontal_bypass.json','solved_contact_forces.json']},current_protocol_sha256=sha(p.parents[1]/'PROTOCOL.json'),scope='Actual current bounded solver with independent URDF/finite-difference observation API; force-weighted first3 loaded press centroids define fixed hand-local tangential reference projected to exact lowest plane. Hypothetical unload/lift/recenter/descend/front/lateral path with frozen object positions/orientations, instant q tracking. Face-axis gap only proves sampled active-hand separation from other object, not all-arm/table/path dynamics or future real contact centroid. No controller changes or physical command, no quality gate changes/admission.',training_ready=False)
(p/'MEASURED_CONTACT_RECENTER_SCREEN.json').write_text(json.dumps(out,indent=2));print(json.dumps(summary,indent=2))
