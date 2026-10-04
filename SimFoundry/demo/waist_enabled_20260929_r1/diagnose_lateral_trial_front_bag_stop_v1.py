"""Recompute first actual bag guard and distinguish exercised interventions.
Original observations and margins remain unchanged; source hashes bind the full
failure. An object-envelope alternative is not a robot action or success proof.
"""
from pathlib import Path
import sys,json,hashlib,datetime,collections
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import linprog
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));R=W/'front_corridor_lateral_physical_r1';ep=R/'case_840023/layout_840023_nudge_mailer_to_bin';old=W/'joint_transport_reserve_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin'
from audit_front_corridor_lateral_record_v1 import verify
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());ready=read(ep/'READY_FOR_AUDIT.json');assert ready['executed_frames']==ready['requested_frames']==1200
for p,h in ready['source_sha256'].items():assert sha(p)==h,p
fr=read(ep/'frontal_bypass.json');row=next(r for r in fr['rows'] if r.get('route_stop_reason'));t=row['step'];assert not next(r for r in fr['rows'] if r['step']==t-1).get('route_stop_reason');record=row['front_corridor_midpoint'];assert row['route_stage']=='front_x'
with np.load(ep/'trace.npz') as z:target=z['mailer'][t].astype(float);other=z['box'][t].astype(float);initial=z['box'][0].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:quat=z['mailer'][t].astype(float);oq=z['box'][t].astype(float)
with np.load(ep/'raw.npz') as z:meta=json.loads(str(z['collect_meta']));q=z['q'].copy();u=z['action'].copy()
assert meta['front_corridor_lateral_replan'] is True and read(ep.parent/'provenance.json')['args']['front_corridor_lateral_replan'] is True
checks=[]
for flag in [False,True]:
 result=verify(record=record,original_goal_x=record['original_goal_x'],route_stage=row['route_stage'],target=target,obstacle=other,size=[.15,.145,.04],other_size=[.14,.09,.045],quat=quat,other_quat=oq,direction=1,planning_margin=.012,initial_other=initial,hand_obstacle_gap_m=row['hand_obstacle_gap_m'],parent_guard_reason=None,prior_stop_reason=None,lateral_y_enabled=flag);assert result['passed'] and not result['changed'];checks.append(dict(lateral_enabled=flag,**result))
width=1000*(record['safe_interval_x'][1]-record['safe_interval_x'][0]);assert width<0
changed=[dict(step=r['step'],stage=r['route_stage']) for r in fr['rows'] if r.get('front_corridor_midpoint',{}).get('changed')];counts=dict(collections.Counter(r['stage'] for r in changed));observed_stages=dict(collections.Counter(r['route_stage'] for r in fr['rows'] if 'front_corridor_midpoint' in r))
with np.load(old/'raw.npz') as z:oldq=z['q'];oldu=z['action'];assert q.shape==oldq.shape and u.shape==oldu.shape
qdiff=np.max(np.abs(q.astype(float)-oldq.astype(float)),axis=1);udiff=np.max(np.abs(u.astype(float)-oldu.astype(float)),axis=1)
first=lambda d:None if not np.any(d>1e-7) else int(np.flatnonzero(d>1e-7)[0])
# Geometry-only alternative: route around the rear (+X) side of the fixed box.
# Keep12mm obstacle margin,5mm table margin,3mm extra route reserve. The
# complete robot, contact feasibility and target-yaw evolution are unproven.
size=np.array([.15,.145,.04]);osize=np.array([.14,.09,.045]);rad=np.abs(Rotation.from_quat(quat).as_matrix())@size/2;orrad=np.abs(Rotation.from_quat(oq).as_matrix())@osize/2;rear_lo=other[0]+orrad[0]+rad[0]+.012;rear_hi=.88-.005-rad[0];rear_x=rear_lo+.003;goal_y=max(.205,target[1]+.16);points=np.array([target[:2],[rear_x,target[1]],[rear_x,goal_y]])
gaps=[]
for a,b in zip(points,points[1:]):
 start=a-other[:2];delta=b-a;intercepts=np.r_[start-(rad+orrad)[:2],-start-(rad+orrad)[:2]];slopes=np.r_[delta,-delta];lp=linprog([0,1],A_ub=np.column_stack([slopes,-np.ones(4)]),b_ub=-intercepts,bounds=[(0,1),(None,None)],method='highs');assert lp.success;gaps.append(float(lp.fun))
tm=float(min(min(x-rad[0]-.28,.88-x-rad[0],y-rad[1]+.75,.75-y-rad[1]) for x,y in points));alternate=dict(scope='Fixed observed oriented-object envelopes only; not robot/IK/contact or future yaw proof.',safe_rear_interval_x_m=[rear_lo,rear_hi],waypoints_xy_m=points.tolist(),minimum_axis_gap_mm=1000*min(gaps),minimum_table_margin_mm=1000*tm,object_envelope_feasible=bool(rear_lo<=rear_x<=rear_hi and min(gaps)>=.012-1e-10 and tm>=.005-1e-10),target_x_travel_mm=1000*(rear_x-target[0]),unissued=True,robot_reachability_verified=False,physics_started=False)
num=read(ep/'FRONT_CORRIDOR_LATERAL_R1_V1_STAGE_NUMERIC_REVIEW.json');assert not num['original_task_and_pose_passed']
findings=['Actual full1200-frame bag trajectory failed; non-target remained stable.','First guard has a negative-width front corridor under unchanged margins; both flag settings preserve this rejection.','Count actual lateral_y changes before attributing performance to the new phase extension. Differences from one parent rollout do not establish causal performance impact.','A rear-side object-envelope route, if feasible, still requires independent robot reachability, clearance and contact/control checks before any candidate implementation.']
source=[Path(__file__),W/'audit_front_corridor_lateral_record_v1.py',R/'PROTOCOL.json',ep/'READY_FOR_AUDIT.json',ep.parent/'provenance.json',ep/'raw.npz',ep/'frontal_bypass.json',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'FRONT_CORRIDOR_LATERAL_R1_V1_STAGE_NUMERIC_REVIEW.json',ep/'ACTUAL_REVIEW_BINDING.json',old/'raw.npz']
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,first_guard_step=t,reason=row['route_stop_reason'],route_stage=row['route_stage'],independent_checks=checks,safe_interval_width_mm=width,actual_table_margin_mm=1000*record['current_table_margin_m'],actual_parcel_axis_gap_mm=1000*record['current_parcel_axis_gap_m'],hand_obstacle_gap_mm=1000*row['hand_obstacle_gap_m'],progress_mm=num['progress_mm'],non_target_max_xy_mm=num['non_target_max_xy_mm'],changed_counts_by_stage=counts,observed_counts_by_stage=observed_stages,changed_records=changed,parent_first_state_divergence_frame=first(qdiff),parent_first_command_divergence_frame=first(udiff),alternative_rear_object_envelope=alternate,findings=findings,source_sha256={str(p):sha(p) for p in source},training_ready=False)
with (R/'FRONT_BAG_FIRST_GUARD_DIAGNOSIS.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['scope','source_sha256','changed_records','findings','independent_checks']},ensure_ascii=False))
