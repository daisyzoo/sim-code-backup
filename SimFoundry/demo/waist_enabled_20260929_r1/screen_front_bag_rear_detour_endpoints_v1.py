"""Unissued rear-detour necessary-condition screen using independent URDF geometry.
Three hypothetical fixed-object waypoints, not dynamics or a continuous robot
path. Preserve original geometry gates; never reinterpret optimizer iterates as
commands. A failed local search is not proof of global unreachability.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
from scipy.optimize import minimize,Bounds
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_corridor_lateral_v1';D=W/'front_bag_rear_detour_probe_r1';D.mkdir(exist_ok=False);sys.path[:0]=[str(W),str(ROOT)]
from audit_front_initial_center_events import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());run=W/'front_corridor_lateral_physical_r1';ep=run/'case_840023/layout_840023_nudge_mailer_to_bin';src=run/'FRONT_BAG_FIRST_GUARD_DIAGNOSIS.json';diag=read(src)
for p,h in diag['source_sha256'].items():assert sha(p)==h,p
assert diag['alternative_rear_object_envelope']['object_envelope_feasible'];step=diag['first_guard_step'];fr=read(ep/'frontal_bypass.json')
with np.load(ep/'raw.npz') as z:actual=z['q'][step,12:23].astype(float)
with np.load(ep/'trace.npz') as z:target=z['mailer'][step].astype(float);other=z['box'][step].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:quat=z['mailer'][step].astype(float);oq=z['box'][step].astype(float)
core=fr['plan']['front_cop_slip_following']['edge_speed']['actual_core']['collision_core_size_xyz'];audit=EventAudit(ROOT,S);axis=np.linalg.eigh(np.cov(audit.hand.vertices['left'].T))[1][:,0];normal=Rotation.from_quat(quat).as_matrix()[:,2];rows=[];warm=actual.copy()
points=diag['alternative_rear_object_envelope']['waypoints_xy_m'];assert len(points)==3
for index,xy in enumerate(points):
 pos=np.r_[xy,target[2]];scene=dict(side='left',target_xyz=pos.tolist(),target_quat=quat.tolist(),core_size=core,other_xyz=other.tolist(),other_quat=oq.tolist(),other_size=[.14,.09,.045]);cache={}
 def geometry(x):
  key=np.asarray(x).tobytes()
  if key not in cache:cache.clear();cache[key]=audit.geometry(x,scene)
  return cache[key]
 def constraints(x):
  r,g=geometry(x);p=g['point'];align=normal@g['pose'][:3,:3]@axis
  return np.r_[align*align-.8**2,.0015-p[:2],.0015+p[:2],p[2]-core[2]/2-.006,core[2]/2+.007-p[2],r['inactive_lowest_z_m']-.8405,r['elbow_gap_m']-.0055,np.array(list(r['hand_parcel_gaps_m'].values()))-.01]
 anchor=warm.copy()
 def cost(x):delta=x-anchor;return float(delta@delta),2*delta
 seeds=[('previous_endpoint_or_actual',warm.copy())]+[(f'neutral_waist_{v}',np.r_[v,np.zeros(10)]) for v in [-.5,0.,.5]];attempts=[]
 for label,seed in seeds:
  fit=minimize(cost,np.clip(seed,audit.lo,audit.hi),jac=True,bounds=Bounds(audit.lo,audit.hi),constraints=[dict(type='ineq',fun=constraints)],method='SLSQP',options=dict(maxiter=160,ftol=1e-11));x=np.asarray(fit.x);r,g=geometry(x);values=constraints(x);ok=bool(fit.success and np.isfinite(x).all() and min(values)>=-2e-7 and r['accepted'] and np.all(x>=audit.lo-2e-7) and np.all(x<=audit.hi+2e-7));a=dict(seed=label,accepted=ok,optimizer_success=bool(fit.success),status=int(fit.status),iterations=int(fit.nit),objective=float(fit.fun),minimum_constraint=float(min(values)),q=x.tolist(),geometry=r,thin_axis_alignment_abs=float(abs(normal@g['pose'][:3,:3]@axis)),constraint_values=values.tolist());attempts.append(a);print(json.dumps(dict(waypoint=index,seed=label,accepted=ok,status=int(fit.status),minimum_constraint=float(min(values)))),flush=True)
 best=min(attempts,key=lambda r:(not r['accepted'],r['objective']));rows.append(dict(waypoint_index=index,target_xy_m=xy,scene=scene,accepted=best['accepted'],best=best,attempts=attempts))
 if best['accepted']:warm=np.asarray(best['q'])
 (D/'PROGRESS.json').write_text(json.dumps(dict(completed_waypoints=len(rows),expected_waypoints=3,rows=rows,controller_changed=False,physics_started=False,training_ready=False),indent=2))
sources={str(p):sha(p) for p in [Path(__file__),src,ep/'raw.npz',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'frontal_bypass.json',S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']}
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,source_observation_step=step,completed_waypoints=3,accepted_waypoints=sum(r['accepted'] for r in rows),rows=rows,source_sha256=sources,limits=dict(planning_waist_abs_rad=.98,xy_tolerance_m=.0015,precontact_height_m=[.006,.007],inactive_height_m=.8405,elbow_gap_m=.0055,hand_parcel_gap_m=.01),continuous_robot_path_verified=False,loaded_contact_verified=False,target_rotation_evolution_verified=False,controller_changed=False,physics_started=False,training_ready=False)
with (D/'ENDPOINT_SCREEN.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(complete=True,accepted_waypoints=out['accepted_waypoints'],waypoints=3,physical_validation=False)),flush=True)
