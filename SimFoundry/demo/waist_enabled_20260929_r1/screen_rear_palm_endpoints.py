"""Multi-start offline position IK for actual stalled rear-control palm requests.
Same original joint bounds, fixed base, inactive arm joints held at recorded state.
Only instantaneous endpoint kinematics: no collision constraints in optimization,
no path, tracking, contact or reachability certificate. Every attempt is retained.
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

def main(run,out):
 run=Path(run).resolve();guard=ClearanceGuard(ROOT,STAGE);records=[];sources={str(Path(__file__)):sha(__file__)}
 for task,side in [('push_box_to_bin','right'),('nudge_mailer_to_bin','left')]:
  ep=run/f'case_840008/layout_840008_{task}';prov=json.loads((ep.parent/'provenance.json').read_text())
  for p in [STAGE/'clearance_runtime.py',STAGE/'articulated_hand_geometry.py',STAGE/'self_clearance.py',STAGE/'elbow_torso_hulls.json',ROOT/'simfoundry/data/hand_obstacle_clearance.py',ROOT/'simfoundry/calibration/sorting_station.py',ROOT/'simfoundry/robots/g1_assets.py',*[Path(p) for p in guard.model.source_sha256]]:
   assert sha(p)==prov['source_sha256'][str(p.relative_to(ROOT))];sources[str(p)]=sha(p)
  coord=json.loads((ep/'coordination.json').read_text())[-1];fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'][-1];assert coord['step']==fr['step']==1199 and fr['mode']=='rear_push';q=np.array(coord['task_inputs']['current']);goal=np.array(fr['target_xyz']);indices=np.r_[0,np.arange(6,11) if side=='right' else np.arange(1,6)];lower=guard.lower[indices];upper=guard.upper[indices]
  def full(x):
   a=q.copy();a[indices]=x;return a
  def geom(a):
   T,jl,jw=guard.model.fk(side,a);offset=T[:3,:3]@np.array([.20,0,.007]);return T,T[:3,3]+offset,jl-skew(offset)@jw
  _,p,_=geom(q);assert np.max(abs(p-np.array(coord['control_point_positions'][side])))<2e-6
  def fun(x):return geom(full(x))[1]-goal
  def jac(x):return geom(full(x))[2][:,indices]
  seeds=[('measured',q[indices])]
  for neutral in [False,True]:
   for waist in [-.98,0.,.98]:
    x=q[indices].copy() if not neutral else np.zeros(6);x[0]=waist;seeds.append((f'{"neutral" if neutral else "measured_arm"}_waist{waist}',x))
  other='mailer' if side=='right' else 'box';size=np.array([.15,.145,.04] if other=='mailer' else [.14,.09,.045])
  with np.load(ep/'trace.npz') as z:op=z[other][1199].copy()
  with np.load(ep/'parcel_orientation.npz') as z:oq=z[other][1199].copy()
  attempts=[]
  for label,seed in seeds:
   fit=least_squares(fun,np.clip(seed,lower+1e-10,upper-1e-10),jac=jac,bounds=(lower,upper),max_nfev=160,ftol=1e-11,xtol=1e-11,gtol=1e-11);candidate=full(fit.x);T,p,J=geom(candidate);gap=hand_face_separation(side).gap(T[:3,3],Rotation.from_matrix(T[:3,:3]).as_quat(),op,oq,size)
   attempts.append(dict(seed=label,optimizer_success=bool(fit.success),status=int(fit.status),function_evaluations=int(fit.nfev),palm_error_mm=((p-goal)*1000).tolist(),palm_error_norm_mm=float(np.linalg.norm(p-goal)*1000),waist_rad=float(candidate[0]),max_joint_change_rad=float(abs(candidate-q).max()),minimum_elbow_torso_gap_mm=float(guard.geometry.constraints(candidate).min()*1000),active_hand_non_target_face_gap_mm=float(gap*1000),active_mesh_min_z_m=float((guard.model.vertices[side]@T[:3,:3].T+T[:3,3])[:,2].min()),candidate_upper_q=candidate.tolist(),path_verified=False))
  record=dict(episode=ep.name,step=1199,goal=goal.tolist(),measured_palm=p.tolist() if False else geom(q)[1].tolist(),attempts=attempts,best_position_error_mm=min(x['palm_error_norm_mm'] for x in attempts));records.append(record)
  for p in [ep/'coordination.json',ep/'frontal_bypass.json',ep/'trace.npz',ep/'parcel_orientation.npz',ep.parent/'provenance.json']:sources[str(p)]=sha(p)
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256=sources,runtime_changed=False,full_collision_or_path_verified=False,training_ready=False)
 with Path(out).open('x') as f:json.dump(report,f,indent=2)
 for row in records:print(json.dumps(dict(episode=row['episode'],attempts=[{k:x[k] for k in ['seed','palm_error_norm_mm','minimum_elbow_torso_gap_mm','active_hand_non_target_face_gap_mm','max_joint_change_rad']} for x in row['attempts']]),indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--out',required=True);a=p.parse_args();main(a.run,a.out)
