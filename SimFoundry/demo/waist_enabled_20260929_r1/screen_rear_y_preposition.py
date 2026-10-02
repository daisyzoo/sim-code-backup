"""Screen Y-before-X rear routes on every completed rear-selected fresh episode.
Object screen is exact for axis-aligned segments and fixed initial rotated AABBs.
Robot screen is endpoint position IK at the original last rear-push requested X/Z,
with candidate Y. It deliberately does NOT certify contact, orientation, whole-arm
clearance, swept robot paths, new object orientations, tracking or success.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];STAGE=W/'staged_closed_peak_trial';sys.path[:0]=[str(STAGE),str(ROOT)]
from clearance_runtime import ClearanceGuard
from articulated_hand_geometry import skew
from simfoundry.data.hand_obstacle_clearance import hand_face_separation
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main(run):
 run=Path(run).resolve();guard=ClearanceGuard(ROOT,STAGE);records=[];sources={str(Path(__file__)):sha(__file__)}
 for f in sorted(run.glob('case_*/*/frontal_bypass.json')):
  ep=f.parent
  if not (ep/'quality.json').exists():continue
  data=json.loads(f.read_text());p=data['plan']
  if not p['required'] or p.get('front_route_selected') or p.get('initial_top_selected'):continue
  rear=[row for row in data['rows'] if row['mode']=='rear_push'];last=rear[-1];t=last['step'];isbox=ep.name.endswith('push_box_to_bin');side='right' if isbox else 'left';target='box' if isbox else 'mailer';other='mailer' if isbox else 'box';sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])};direction=p['direction'];prov=json.loads((ep.parent/'provenance.json').read_text())
  for path in [STAGE/'clearance_runtime.py',STAGE/'articulated_hand_geometry.py',STAGE/'self_clearance.py',STAGE/'elbow_torso_hulls.json',ROOT/'simfoundry/data/hand_obstacle_clearance.py',ROOT/'simfoundry/calibration/sorting_station.py',ROOT/'simfoundry/robots/g1_assets.py',*[Path(x) for x in guard.model.source_sha256]]:
   assert sha(path)==prov['source_sha256'][str(path.relative_to(ROOT))];sources[str(path)]=sha(path)
  with np.load(ep/'trace.npz') as z:start=z[target][0,:2].copy();obstacle=z[other][0,:2].copy();op=z[other][t].copy()
  with np.load(ep/'parcel_orientation.npz') as z:
   radii={s:(np.abs(Rotation.from_quat(z[s][0]).as_matrix())@(sizes[s]/2))[:2] for s in [target,other]};oq=z[other][t].copy()
  rt,ro=radii[target],radii[other];combined=rt+ro;margin=p['margin'];goal_y=p['front_route_candidates']['goal_y'];pre_limit=obstacle[1]-direction*(combined[1]+margin);available=max(0.,min(direction*(pre_limit-start[1]),direction*(goal_y-start[1])))
  coord=next(c for c in json.loads((ep/'coordination.json').read_text()) if c['step']==t);q=np.array(coord['task_inputs']['current']);base_goal=np.array(last['target_xyz']);indices=np.r_[0,np.arange(6,11) if isbox else np.arange(1,6)];lo=guard.lower[indices];hi=guard.upper[indices]
  def full(x):a=q.copy();a[indices]=x;return a
  def palm(a):
   T,jl,jw=guard.model.fk(side,a);off=T[:3,:3]@np.array([.20,0,.007]);return T,T[:3,3]+off,jl-skew(off)@jw
  assert np.max(abs(palm(q)[1]-coord['control_point_positions'][side]))<2e-6
  variants=[]
  for fraction in [0.,.5,1.]:
   y=start[1]+direction*available*fraction;waypoints=np.array([start,[start[0],y],[p['rear_goal_x'],y],[p['rear_goal_x'],goal_y]])
   separations=[]
   for a,b in zip(waypoints[:-1],waypoints[1:]):
    diff=abs(b-a);assert np.count_nonzero(diff>1e-12)<=1
    axis=int(diff.argmax());static=1-axis;closest=np.clip(obstacle[axis],min(a[axis],b[axis]),max(a[axis],b[axis]));separations.append(float(max(abs(a[static]-obstacle[static])-combined[static],abs(closest-obstacle[axis])-combined[axis])))
   # Original tabletop X bounds; Y bounds come from declared frozen scene width.
   table_x=min(float(np.min(waypoints[:,0]-rt[0]-.28)),float(np.min(.88-waypoints[:,0]-rt[0])))
   candidate_goal=base_goal.copy();candidate_goal[1]=y
   attempts=[]
   for label,seed in [('measured',q[indices]),('neutral_waist0',np.zeros(6)),('neutral_waist_task',np.r_[.98 if isbox else -.98,np.zeros(5)])]:
    fit=least_squares(lambda x:palm(full(x))[1]-candidate_goal,np.clip(seed,lo+1e-10,hi-1e-10),jac=lambda x:palm(full(x))[2][:,indices],bounds=(lo,hi),max_nfev=160,ftol=1e-11,xtol=1e-11,gtol=1e-11);a=full(fit.x);T,pos,_=palm(a);gap=hand_face_separation(side).gap(T[:3,3],Rotation.from_matrix(T[:3,:3]).as_quat(),op,oq,sizes[other]);attempts.append(dict(seed=label,success=bool(fit.success),nfev=int(fit.nfev),error_mm=float(np.linalg.norm(pos-candidate_goal)*1000),elbow_gap_mm=float(guard.geometry.constraints(a).min()*1000),hand_non_target_gap_mm=float(gap*1000),hand_min_z_m=float((guard.model.vertices[side]@T[:3,:3].T+T[:3,3])[:,2].min()),q=a.tolist()))
   variants.append(dict(y_fraction=fraction,pre_move_mm=available*fraction*1000,waypoints_xy=waypoints.tolist(),segment_object_separation_m=separations,table_x_margin_m=table_x,object_x_and_pair_eligible=bool(min(separations)>=margin-1e-9 and table_x>=.005),position_probe_goal=candidate_goal.tolist(),endpoint_attempts=attempts,best_endpoint_error_mm=min(a['error_mm'] for a in attempts)))
  row=dict(episode=ep.name,task_passed=json.loads((ep/'quality.json').read_text())['passed'],last_rear_step=t,original_last_palm_goal=base_goal.tolist(),available_safe_initial_y_advance_mm=available*1000,original_rear_margin_m=margin,variants=variants);records.append(row)
  for path in [f,ep/'quality.json',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'coordination.json',ep.parent/'provenance.json']:sources[str(path)]=sha(path)
  print(json.dumps(dict(episode=ep.name,task_passed=row['task_passed'],available_mm=row['available_safe_initial_y_advance_mm'],variants=[dict(fraction=v['y_fraction'],object_eligible=v['object_x_and_pair_eligible'],best_error_mm=v['best_endpoint_error_mm']) for v in variants])),flush=True)
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256=sources,runtime_changed=False,training_ready=False,full_route_robot_verified=False)
 with (run/'REAR_Y_PREPOSITION_SCREEN.json').open('x') as out:json.dump(report,out,indent=2)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');a=p.parse_args();main(a.run)
