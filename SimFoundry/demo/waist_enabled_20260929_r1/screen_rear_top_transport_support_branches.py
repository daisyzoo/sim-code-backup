"""Support-vertex branch continuation: full nominal routes using the existing12mm planning fallback after20mm failure.
All accepted initial posture branches for both previously failed box routes are
retained. This is not a20mm pass or a change to original task/data quality gates.
The complete six-layout parent result remains authoritative; this bounded retry
does not clear other failures or certify physical contact or full goal completion.
Each failed independent sample becomes an extra collocation point, up to8
solves per segment. All rejected candidates and original sample gates retained.
Quarter, half and three-quarter points preserve original endpoint geometry and
add a10um/scalar residual planning reserve; independent sampled gates unchanged.
Test all6 diagnosed rear layouts, original X-first and Y-preposition then X.
Hypothetical object translation is an offline scene parameter, never simulator
state mutation. Hand remains6..7mm above core: no physical loaded contact proof.
Only selected hand/parcel and elbow geometry checked, not entire robot sweep.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
import numpy as np
from scipy.optimize import minimize,Bounds
from scipy.spatial import ConvexHull
W=Path(__file__).resolve().parent;ROOT=W.parents[1];STAGE=W/'staged_closed_peak_trial';sys.path[:0]=[str(STAGE),str(ROOT),str(W)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from articulated_hand_geometry import skew
from audit_minimum_motion_plan_reentrant import PlanAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(run):
 run=Path(run).resolve();source=run/'INITIAL_REAR_TOP_CONTACT_SCREEN.json';data=json.loads(source.read_text());assert data['complete'];out=run/'REAR_TOP_TRANSPORT_SUPPORT_BRANCH_SCREEN.json';assert not out.exists();guard=ClearanceGuard(ROOT,STAGE);independent=PlanAudit(ROOT,STAGE);records=[];sources={str(source):sha(source)}
 def save(complete):
  files=[Path(__file__),STAGE/'clearance_runtime.py',STAGE/'recontact_scene.py',STAGE/'articulated_hand_geometry.py',STAGE/'self_clearance.py',STAGE/'elbow_torso_hulls.json',STAGE/'recontact_plan.py',STAGE/'recontact_plan_original.py',W/'audit_minimum_motion_plan_reentrant.py',W/'audit_recontact_interior_events.py',W/'audit_recontact_pose_events.py',*[Path(p) for p in guard.model.source_sha256]];sources.update({str(p):sha(p) for p in files});out.write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,complete=complete,records=records,source_sha256=sources,preferred_inset_m=.020,tested_original_fallback_inset_m=.012,original_measured_handover_inset_m=.01,runtime_changed=False,physical_validation=False,training_ready=False),indent=2))
 prior_path=run/'REAR_TOP_TRANSPORT_REFINED_SCREEN.json';prior=json.loads(prior_path.read_text());assert prior['complete'];sources[str(prior_path)]=sha(prior_path)
 pending={e['episode'] for e in prior['records'] if any(p['route']=='Y_then_X' and not p['nominal_path_passed'] for p in e['paths'])}
 trials=[]
 for ep in data['records']:
  valid=[a for a in ep['scenes'][0]['attempts'] if a['accepted']]
  if ep['episode'] not in pending or not valid:continue
  selected=min(valid,key=lambda a:a['objective'])
  trials.extend((ep,a) for a in valid)
 for ep,alternative in trials:
  initial=ep['scenes'][0];assert initial['name']=='initial_top';available=[a for a in initial['attempts'] if a['accepted']];record=dict(episode=ep['episode'],original_task_passed=ep['original_task_passed'],initial_endpoint_available=bool(available),alternative_start_seed=alternative['seed'],paths=[]);records.append(record)
  if not available:record['reason']='no_verified_initial_endpoint_in_declared_seed_budget';save(False);continue
  start=np.array(alternative['candidate_q']);base=dict(initial['scene']);p0=np.array(base['target_xyz']);side=base['side'];axis=np.linalg.eigh(np.cov(guard.model.vertices[side].T))[1][:,0];core=np.array(base['core_size']);half=core[:2]/2-.012;vertices=guard.model.vertices[side];hull=ConvexHull(vertices).vertices
  for route_name,endrow in [('Y_then_X',ep['scenes'][2])]:
   pend=np.array(endrow['scene']['target_xyz']);nodes=[p0,pend] if route_name=='X_first' else [p0,np.array([p0[0],pend[1],p0[2]]),pend];targets=[]
   for a,b in zip(nodes,nodes[1:]):
    n=max(1,int(np.ceil(np.linalg.norm(b-a)/.010)));targets.extend([a+(b-a)*i/n for i in range(1,n+1)])
   q=start.copy();pos=p0.copy();attempts=[];finished=True
   for index,target in enumerate(targets):
    scene=RecontactScene(guard,**dict(base,target_xyz=target.tolist()));normal=scene.rotation[:,2]
    def align(x):
     T,jl,jw=guard.model.fk(side,x);v=T[:3,:3]@axis;return float(normal@v),normal@(-skew(v)@jw)
    def cost(x):d=x-q;return float(d@d),2*d
    def cons(x,context=scene,index=None):
     g=context.details(x);p=g['point'];J=g['jacobian'];a,da=align(x)
     if index is not None:
      T,jl,jw=guard.model.fk(side,x);R=T[:3,:3];p=(T[:3,3]+R@vertices[index]-context.target)@context.rotation;J=context.rotation.T@(jl-skew(R@vertices[index])@jw)
     values=np.r_[a*a-.8**2,half-p[:2],half+p[:2],p[2]-core[2]/2-.006,core[2]/2+.007-p[2],g['inactive_z']-.84,guard.geometry.constraints(x)-.005]
     jac=np.vstack([2*a*da,-J[:2],J[:2],J[2],-J[2],g['inactive_z_jacobian'],guard.geometry.jacobian(x)])
     if index is not None:
      delta=(vertices[hull]-vertices[index])@R.T
      # The named point must remain a minimum-height hull vertex. This prevents
      # treating an interior point as the actual support point to pass XY gates.
      values=np.r_[values,delta@context.rotation[:,2]+1e-10]
      jac=np.vstack([jac,np.cross(delta,context.rotation[:,2])@jw])
     return values,jac
    collocation=[(f,RecontactScene(guard,**dict(base,target_xyz=(pos+(target-pos)*f).tolist()))) for f in [.25,.5,.75,1.]]
    branch_indices=None
    def combined(x):
     values=[];grads=[]
     for ci,(f,context) in enumerate(collocation):
      v,j=cons(q+(x-q)*f,context,None if branch_indices is None else branch_indices[ci])
      # Reserve applies to original geometric constraints only, not support
      # ordering (zero at the selected vertex by construction).
      if branch_indices is None:v=v-1e-5
      else:v=np.r_[v[:-len(hull)]-1e-5,v[-len(hull):]]
      values.extend(v);grads.extend(j*f)
     return np.array(values),np.array(grads)
    def gaps(x):return np.concatenate([np.array(list(context.details(q+(x-q)*f)['gaps'].values()))-.01001 for f,context in collocation])
    refinements=[];seed=q.copy();solver_attempts=[]
    for refinement in range(8):
     branch_indices=None
     for mode in ['original','fixed_failed','fixed_start']:
      if mode!='original':
       branch_seed=x if mode=='fixed_failed' else q
       branch_indices=[context.details(q+(branch_seed-q)*f)['vertex_index'] for f,context in collocation]
       seed=branch_seed.copy()
      fit=minimize(cost,seed,jac=True,bounds=Bounds(guard.lower,guard.upper),constraints=[dict(type='ineq',fun=lambda x:combined(x)[0],jac=lambda x:combined(x)[1]),dict(type='ineq',fun=gaps)],method='SLSQP',options=dict(maxiter=140 if mode=='original' else 220,ftol=1e-12));x=np.asarray(fit.x);minimum=float(min(cons(x)[0]));good=bool(fit.success and minimum>=-2e-7 and min(combined(x)[0])>=-2e-7 and min(gaps(x))>=-2e-7 and min(scene.details(x)['gaps'].values())>=.01-2e-7 and np.all(x>=guard.lower-2e-7) and np.all(x<=guard.upper+2e-7))
      solver_attempts.append(dict(refinement=refinement,mode=mode,solver_success=bool(fit.success),status=int(fit.status),iterations=int(fit.nit),accepted_for_independent_sampling=good,candidate_q=x.tolist(),minimum_constraint=minimum,collocation_minimum=float(min(combined(x)[0])),support_vertices=branch_indices,collocation_fractions=[f for f,_ in collocation]))
      if good:break
     samples=[]
     if good:
      n=max(1,int(np.ceil(max(abs(x-q)/(guard.limits*.25)))))
      for i in range(1,n+1):
       f=i/n;sq=q+(x-q)*f;sp=pos+(target-pos)*f;ctx=dict(base,target_xyz=sp.tolist());g,d=independent.geometry(sq,ctx);a=abs(d['rotation'][:,2]@d['pose'][:3,:3]@axis);margin=float(min(a*a-.8**2,*list(half-abs(d['point'][:2])),g['active_above_top_m']-.004,.010-g['active_above_top_m'],independent.hand.minz(sq,'left' if side=='right' else 'right')-.84,g['elbow_gap_m']-.005,*list(np.array(list(g['hand_parcel_gaps_m'].values()))-.01)))
       samples.append(dict(fraction=f,minimum_margin=margin,accepted=bool(margin>=-2e-7),q=sq.tolist(),target_xyz=sp.tolist()))
     segment_ok=bool(good and min(combined(x)[0])>=-2e-7 and min(gaps(x))>=-2e-7 and samples and all(s['accepted'] for s in samples))
     refinements.append(dict(iteration=refinement,collocation_fractions=[f for f,_ in collocation],endpoint_accepted=good,segment_accepted=segment_ok,status=int(fit.status),minimum_constraint=minimum,candidate_q=x.tolist(),samples=samples,collocation_minimum=float(min(combined(x)[0])),collocation_gap_minimum=float(min(gaps(x)))))
     if segment_ok or not good or not samples:break
     worst=min(samples,key=lambda s:s['minimum_margin']);fraction=worst['fraction']
     if worst['accepted'] or any(abs(f-fraction)<1e-12 for f,_ in collocation):break
     collocation.append((fraction,RecontactScene(guard,**dict(base,target_xyz=worst['target_xyz']))));collocation.sort(key=lambda v:v[0]);seed=x.copy()
    attempts.append(dict(index=index,target_xyz=target.tolist(),endpoint_accepted=good,segment_accepted=segment_ok,solver_success=bool(fit.success),iterations=int(fit.nit),status=int(fit.status),minimum_constraint=minimum,collocation_minimum=float(min(combined(x)[0])),collocation_gap_minimum=float(min(gaps(x))),candidate_q=x.tolist(),samples=samples,refinements=refinements,solver_attempts=solver_attempts))
    if not segment_ok:finished=False;break
    q=x;pos=target
   path=dict(route=route_name,nodes=[x.tolist() for x in nodes],planned_object_steps=len(targets),attempted_object_steps=len(attempts),nominal_path_passed=finished,attempts=attempts,reason='all_selected_geometry_samples_passed' if finished else 'first_failed_endpoint_or_joint_interpolation_preserved');record['paths'].append(path);save(False);print(json.dumps(dict(episode=ep['episode'],start_seed=alternative['seed'],route=route_name,planned=len(targets),attempted=len(attempts),passed=finished)),flush=True)
 save(True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');a=p.parse_args();main(a.run)
