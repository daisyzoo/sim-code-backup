"""Actual staged bounded solver on continuous hypothetical front motion, no dynamics."""
from pathlib import Path
import json,hashlib,sys
with_lifts='--with-lifts' in sys.argv
requested_episode=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else None
root=Path(__file__).resolve().parent
source=(root/'check_staged_contact_normal.py').read_text();exec(compile(source.split('for t in (101,106,180,251,365,532,551):')[0],'<validated_staged_setup>','exec'))
if requested_episode is not None:
 ep=requested_episode
 with np.load(ep/'raw.npz') as z:qs=z['q']
 coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};ctrl={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())}
side='right' if 'push_box' in ep.name else 'left';inactive_side='left' if side=='right' else 'right';start=next(t for t,r in ctrl.items() if r['mode']=='top_press');front_selected=json.loads((ep/'frontal_bypass.json').read_text())['plan'].get('front_route_selected',False)
mesh=np.asarray(json.loads((repo/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'][side]);center=(mesh.min(0)+mesh.max(0))/2
qstart=qs[start,12:].astype(float);normal=transform(side,qstart)[:3,:3].T@np.array([0.,0.,1.]);inactive=np.array(coords[start]['inactive_anchor']);waypoints=[]
# First settle at initial measured virtual target, then front X and lateral Y.
initial=np.array(ctrl[start]['target_xyz']);initial[2]=.7924758 if side=='right' else .7899758
waypoints.extend([initial.copy() for _ in range(40)])
front=np.array([.3675 if front_selected else initial[0],initial[1],initial[2]]);n=max(1,int(np.ceil(np.max(abs(front-initial))/.003)))
waypoints.extend(initial+(front-initial)*a for a in np.linspace(0,1,n+1)[1:])
for k,y in enumerate(np.linspace(initial[1],-.24 if side=='right' else .24,110)[1:],1):
 point=np.array([front[0],y,front[2]]);waypoints.append(point.copy())
 if with_lifts and k in (30,60,90):
  high=.86 if front_selected else .91
  for z in np.linspace(point[2],high,41)[1:]:waypoints.append(np.array([point[0],point[1],z]))
  waypoints.extend([np.array([point[0],point[1],high]) for _ in range(15)])
  for z in np.linspace(high,point[2],41)[1:]:waypoints.append(np.array([point[0],point[1],z]))
waypoints.extend([waypoints[-1].copy() for _ in range(40)])
results=[]
for enabled in (False,True):
 q=qstart.copy();records=[]
 for k,goal in enumerate(waypoints):
  for repeat in range(4):
   robot=robot_at(q);m=transform(side,q);world=mesh@m[:3,:3].T+m[:3,3];lowest=int(np.argmin(world[:,2]));wc=m[:3,:3]@center+m[:3,3];point=wc+np.array([0.,0.,world[lowest,2]-wc[2]]);local=m[:3,:3].T@(point-m[:3,3]);reference=dict(reference_local=local,center_local=center,lowest_vertex_local=mesh[lowest],world_normal=np.array([0.,0.,1.]))
   action=np.zeros(23);result=candidate(robot,{'left':1,'right':2},action,state=NS(side=side,last_target_xyz=goal),anchor={inactive_side:inactive},default=np.zeros(23),waist_limit=1.,bounded=True,active_point_offset=local,active_support_reference=reference,active_normal_anchor_local=normal if enabled else None,trace_jacobian=True)
   dq=action[12:]-q;assert np.max(abs(dq))<=.04000001 and abs(dq[0])<=.01500001
   q=action[12:].copy()
  m=transform(side,q);other=transform(inactive_side,q);world=mesh@m[:3,:3].T+m[:3,3];wc=m[:3,:3]@center+m[:3,3];point=wc+np.array([0.,0.,world[:,2].min()-wc[2]])
  records.append(dict(waypoint=k,goal=goal.tolist(),active_error_m=float(np.linalg.norm(point-goal)),inactive_error_m=float(np.linalg.norm(other[:3,:3]@np.array(PALM_OFFSET)+other[:3,3]-inactive)),normal_error_deg=float(np.degrees(np.arccos(np.clip((m[:3,:3].T@np.array([0.,0.,1.]))@normal,-1,1)))),waist_rad=float(q[0]),q=q.tolist()))
 tracked=records[40:];summary=dict(normal_enabled=enabled,waypoints=len(records),solver_steps=4*len(records),max_active_error_after_initial_settle_m=max(x['active_error_m'] for x in tracked),max_inactive_error_after_initial_settle_m=max(x['inactive_error_m'] for x in tracked),max_normal_error_after_initial_settle_deg=max(x['normal_error_deg'] for x in tracked),final_active_error_m=records[-1]['active_error_m'],final_inactive_error_m=records[-1]['inactive_error_m'],final_normal_error_deg=records[-1]['normal_error_deg'],max_waist_rad=max(abs(x['waist_rad']) for x in records))
  # All q here are immediate kinematic updates, not simulator states.
 results.append(dict(summary=summary,records=records));print(json.dumps(summary),flush=True)
for p,h in manifest['source_sha256'].items():assert sha(p)==h,p
(stage/('CONTINUOUS_IK_CHECK_'+ep.name+('_with_lifts' if with_lifts else '')+'.json')).write_text(json.dumps(dict(results=results,candidate_sha256=manifest['candidate_sha256'],checker_sha256=sha(__file__),includes_three_hypothetical_lifts=with_lifts,fixture_episode=str(ep),fixture_raw_sha256=sha(ep/'raw.npz'),scope='Actual staged bounded solver; independent URDF FK/finite-difference robot API, instant q command tracking, hypothetical flat top/front path and fixed inactive anchor. Original joint and step limits checked. No contact forces, parcel dynamics, collision checks, image quality or guaranteed physical success. Screen tolerances do not alter original gates.',training_ready=False),indent=2))
