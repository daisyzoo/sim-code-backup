"""Nominal top-contact transport continuation from independently checked endpoints.
Test all6 diagnosed rear layouts, original X-first and Y-preposition then X.
Hypothetical object translation is an offline scene parameter, never simulator
state mutation. Hand remains6..7mm above core: no physical loaded contact proof.
Only selected hand/parcel and elbow geometry checked, not entire robot sweep.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
import numpy as np
from scipy.optimize import minimize,Bounds
W=Path(__file__).resolve().parent;ROOT=W.parents[1];STAGE=W/'staged_closed_peak_trial';sys.path[:0]=[str(STAGE),str(ROOT),str(W)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from articulated_hand_geometry import skew
from audit_minimum_motion_plan_reentrant import PlanAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(run):
 run=Path(run).resolve();source=run/'INITIAL_REAR_TOP_CONTACT_SCREEN.json';data=json.loads(source.read_text());assert data['complete'];out=run/'REAR_TOP_TRANSPORT_PATH_SCREEN.json';assert not out.exists();guard=ClearanceGuard(ROOT,STAGE);independent=PlanAudit(ROOT,STAGE);records=[];sources={str(source):sha(source)}
 def save(complete):
  files=[Path(__file__),STAGE/'clearance_runtime.py',STAGE/'recontact_scene.py',STAGE/'articulated_hand_geometry.py',STAGE/'self_clearance.py',STAGE/'elbow_torso_hulls.json',W/'audit_minimum_motion_plan_reentrant.py',W/'audit_recontact_interior_events.py',W/'audit_recontact_pose_events.py',*[Path(p) for p in guard.model.source_sha256]];sources.update({str(p):sha(p) for p in files});out.write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,complete=complete,records=records,source_sha256=sources,runtime_changed=False,physical_validation=False,training_ready=False),indent=2))
 for ep in data['records']:
  initial=ep['scenes'][0];assert initial['name']=='initial_top';available=[a for a in initial['attempts'] if a['accepted']];record=dict(episode=ep['episode'],original_task_passed=ep['original_task_passed'],initial_endpoint_available=bool(available),paths=[]);records.append(record)
  if not available:record['reason']='no_verified_initial_endpoint_in_declared_seed_budget';save(False);continue
  start=np.array(min(available,key=lambda a:a['objective'])['candidate_q']);base=dict(initial['scene']);p0=np.array(base['target_xyz']);side=base['side'];axis=np.linalg.eigh(np.cov(guard.model.vertices[side].T))[1][:,0];core=np.array(base['core_size']);half=core[:2]/2-.020
  for route_name,endrow in [('X_first',ep['scenes'][1]),('Y_then_X',ep['scenes'][2])]:
   pend=np.array(endrow['scene']['target_xyz']);nodes=[p0,pend] if route_name=='X_first' else [p0,np.array([p0[0],pend[1],p0[2]]),pend];targets=[]
   for a,b in zip(nodes,nodes[1:]):
    n=max(1,int(np.ceil(np.linalg.norm(b-a)/.010)));targets.extend([a+(b-a)*i/n for i in range(1,n+1)])
   q=start.copy();pos=p0.copy();attempts=[];finished=True
   for index,target in enumerate(targets):
    scene=RecontactScene(guard,**dict(base,target_xyz=target.tolist()));normal=scene.rotation[:,2]
    def align(x):
     T,jl,jw=guard.model.fk(side,x);v=T[:3,:3]@axis;return float(normal@v),normal@(-skew(v)@jw)
    def cost(x):d=x-q;return float(d@d),2*d
    def cons(x):
     g=scene.details(x);p=g['point'];J=g['jacobian'];a,da=align(x);return np.r_[a*a-.8**2,half-p[:2],half+p[:2],p[2]-core[2]/2-.006,core[2]/2+.007-p[2],g['inactive_z']-.84,guard.geometry.constraints(x)-.005],np.vstack([2*a*da,-J[:2],J[:2],J[2],-J[2],g['inactive_z_jacobian'],guard.geometry.jacobian(x)])
    fit=minimize(cost,q,jac=True,bounds=Bounds(guard.lower,guard.upper),constraints=[dict(type='ineq',fun=lambda x:cons(x)[0],jac=lambda x:cons(x)[1]),dict(type='ineq',fun=lambda x:np.array(list(scene.details(x)['gaps'].values()))-.01)],method='SLSQP',options=dict(maxiter=140,ftol=1e-12));x=np.asarray(fit.x);minimum=float(min(cons(x)[0]));good=bool(fit.success and minimum>=-2e-7 and min(scene.details(x)['gaps'].values())>=.01-2e-7 and np.all(x>=guard.lower-2e-7) and np.all(x<=guard.upper+2e-7));samples=[]
    if good:
     n=max(1,int(np.ceil(max(abs(x-q)/(guard.limits*.25)))))
     for i in range(1,n+1):
      f=i/n;sq=q+(x-q)*f;sp=pos+(target-pos)*f;ctx=dict(base,target_xyz=sp.tolist());g,d=independent.geometry(sq,ctx);a=abs(d['rotation'][:,2]@d['pose'][:3,:3]@axis);margin=float(min(a*a-.8**2,*list(half-abs(d['point'][:2])),g['active_above_top_m']-.004,.010-g['active_above_top_m'],independent.hand.minz(sq,'left' if side=='right' else 'right')-.84,g['elbow_gap_m']-.005,*list(np.array(list(g['hand_parcel_gaps_m'].values()))-.01)))
      samples.append(dict(fraction=f,minimum_margin=margin,accepted=bool(margin>=-2e-7),q=sq.tolist(),target_xyz=sp.tolist()))
    segment_ok=bool(good and samples and all(s['accepted'] for s in samples));attempts.append(dict(index=index,target_xyz=target.tolist(),endpoint_accepted=good,segment_accepted=segment_ok,solver_success=bool(fit.success),iterations=int(fit.nit),status=int(fit.status),minimum_constraint=minimum,candidate_q=x.tolist(),samples=samples))
    if not segment_ok:finished=False;break
    q=x;pos=target
   path=dict(route=route_name,nodes=[x.tolist() for x in nodes],planned_object_steps=len(targets),attempted_object_steps=len(attempts),nominal_path_passed=finished,attempts=attempts,reason='all_selected_geometry_samples_passed' if finished else 'first_failed_endpoint_or_joint_interpolation_preserved');record['paths'].append(path);save(False);print(json.dumps(dict(episode=ep['episode'],route=route_name,planned=len(targets),attempted=len(attempts),passed=finished)),flush=True)
 save(True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');a=p.parse_args();main(a.run)
