"""Offline raised two-waypoint paths for five straight-path failures.
No execution or contact claim. Retain original .25 joint spacing and selected
geometry acceptance. PCA thin axis is not an identified physical palm face.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.optimize import minimize,Bounds
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_precise_parent_seed';sys.path[:0]=[str(stage),str(w),str(repo)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_recontact_pose_events import EventAudit
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();src=w/'FLAT_FACE_PATH_FINDINGS.json';data=json.loads(src.read_text())
for p,h in data['source_sha256'].items():assert sha(Path(p))==h
original=json.loads((w/'FLAT_FACE_RECONTACT_SCREEN.json').read_text())
for p,h in original['source_sha256'].items():assert sha(Path(p))==h
sources={str(src):sha(src),**original['source_sha256'],str(Path(__file__)):sha(Path(__file__))};guard=ClearanceGuard(repo,stage);audit=EventAudit(repo,stage);records=[]
def solve_lift(scene,reference,height):
 g0=scene.details(reference);xy=g0['point'][:2].copy()
 def cost(x):
  delta=x-reference;return float(delta@delta),2*delta
 def cons(x):
  g=scene.details(x);p=g['point'];J=g['jacobian'];h=p[2]-scene.core[2]/2
  return np.r_[.002-(p[:2]-xy),.002+(p[:2]-xy),h-height,height+.001-h,g['inactive_z']-.84,guard.geometry.constraints(x)-.005],np.vstack([-J[:2],J[:2],J[2],-J[2],g['inactive_z_jacobian'],guard.geometry.jacobian(x)])
 fit=minimize(cost,np.clip(reference,guard.lower,guard.upper),jac=True,bounds=Bounds(guard.lower,guard.upper),constraints=[dict(type='ineq',fun=lambda x:cons(x)[0],jac=lambda x:cons(x)[1]),dict(type='ineq',fun=lambda x:np.array(list(scene.details(x)['gaps'].values()))-.01)],method='SLSQP',options=dict(maxiter=220,ftol=1e-12))
 x=np.array(fit.x);g,detail=audit.geometry(x,scene.record());h=g['active_above_top_m'];ind=float(min(*(.002-abs(detail['point'][:2]-xy)),h-height,height+.001-h,audit.hand.minz(x,scene.inactive)-.84,g['elbow_gap_m']-.005));assert abs(ind-min(cons(x)[0]))<2e-8
 valid=bool(fit.success and ind>=-2e-7 and g['accepted'] and np.all(x>=guard.lower-2e-7) and np.all(x<=guard.upper+2e-7))
 return dict(accepted=valid,status=int(fit.status),iterations=int(fit.nit),minimum_constraint_m=ind,candidate=x.tolist(),independent_geometry=g)
def segment(a,b,scene):
 n=max(1,int(np.ceil(max(abs(b-a)/(guard.limits*.25)))));checks=[audit.geometry(np.clip(a+(b-a)*i/n,guard.lower,guard.upper),scene.record())[0] for i in range(1,n+1)]
 return dict(samples=n,accepted=all(x['accepted'] for x in checks),first_failure_waypoint=next((i+1 for i,g in enumerate(checks) if not g['accepted']),None),min_above_top_mm=min(g['active_above_top_m'] for g in checks)*1000,min_hand_parcel_gap_mm=min(min(g['hand_parcel_gaps_m'].values()) for g in checks)*1000,min_elbow_gap_mm=min(g['elbow_gap_m'] for g in checks)*1000)
for row in data['rows']:
 if row['path_feasible_attempts']:continue
 name=row['episode'];ep=w/'precise_interior_groups_r1'/('case_'+name.split('_')[1])/name;events=json.loads((ep/'recontact_pose.json').read_text())['rows'];ctx=next(e['context'] for e in events if e['step']==row['step']);q=np.array(ctx['current']);end=np.array(row['best_endpoint_only']['candidate']);scene=RecontactScene(guard,**ctx['scene']);attempts=[]
 for height in [.015,.030,.060]:
  start_height=max(height,scene.details(q)['point'][2]-scene.core[2]/2);a=solve_lift(scene,q,start_height);b=solve_lift(scene,end,height);segs=[]
  if a['accepted'] and b['accepted']:
   nodes=[q,np.array(a['candidate']),np.array(b['candidate']),end];segs=[segment(x,y,scene) for x,y in zip(nodes,nodes[1:])]
  count=sum(s['samples'] for s in segs);ok=bool(len(segs)==3 and all(s['accepted'] for s in segs));attempts.append(dict(height_m=height,start_lift=a,end_lift=b,segments=segs,path_geometry_passed=ok,total_waypoints=count,nominal_waypoints_within_240=bool(ok and count<=240),real_tracking_budget_verified=False))
  print(name,row['step'],height,'endpoints',a['accepted'],b['accepted'],'path',ok,'waypoints',count,flush=True)
 records.append(dict(episode=name,step=row['step'],attempts=attempts))
 report=dict(scope=__doc__,complete=False,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),records=records,source_sha256=sources,controller_changed=False,physical_validation=False,training_ready=False);(w/'FLAT_FACE_LIFT_PATH_SCREEN.json').write_text(json.dumps(report,indent=2))
assert len(records)==5
report.update(complete=True,path_feasible_cases=sum(any(a['path_geometry_passed'] for a in r['attempts']) for r in records),nominal_within_240_cases=sum(any(a['nominal_waypoints_within_240'] for a in r['attempts']) for r in records));(w/'FLAT_FACE_LIFT_PATH_SCREEN.json').write_text(json.dumps(report,indent=2));print('COMPLETE',report['path_feasible_cases'],report['nominal_within_240_cases'],flush=True)
