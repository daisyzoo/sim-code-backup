"""Re-solve exact four failed nominal top-transport segments, no gate change.
Compare original nonsmooth lowest-point constraints against fixed supporting
vertex branches with all convex-hull heights constrained above that vertex.
No global infeasibility or physical path/contact claim; preserve failed attempts.
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
 run=Path(run).resolve();source=run/'REAR_TOP_TRANSPORT_ALTERNATIVE_STARTS_SCREEN.json';prior=json.loads(source.read_text());assert prior['complete'];initpath=run/'INITIAL_REAR_TOP_CONTACT_SCREEN.json';initials={e['episode']:e for e in json.loads(initpath.read_text())['records']};guard=ClearanceGuard(ROOT,STAGE);audit=PlanAudit(ROOT,STAGE);records=[];out=run/'FAILED_TOP_PATH_SEGMENT_PROBE.json';assert not out.exists();sources={str(p):sha(p) for p in [Path(__file__),source,initpath,STAGE/'clearance_runtime.py',STAGE/'recontact_scene.py',STAGE/'articulated_hand_geometry.py',STAGE/'self_clearance.py',STAGE/'elbow_torso_hulls.json',W/'audit_minimum_motion_plan_reentrant.py',W/'audit_recontact_pose_events.py',*[Path(p) for p in guard.model.source_sha256]]}
 def save(complete):out.write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,complete=complete,records=records,source_sha256=sources,runtime_changed=False,training_ready=False),indent=2))
 for old in prior['records']:
  ep=initials[old['episode']];base=ep['scenes'][0]['scene'];side=base['side'];inactive='left' if side=='right' else 'right';core=np.array(base['core_size']);half=core[:2]/2-.020;vertices=guard.model.vertices[side];hull=ConvexHull(vertices).vertices;axis=np.linalg.eigh(np.cov(vertices.T))[1][:,0]
  p=old['paths'][0];a=p['attempts'][-1];before=p['attempts'][-2] if len(p['attempts'])>1 else None;first=next(x for x in ep['scenes'][0]['attempts'] if x['seed']==old['alternative_start_seed']);q=np.array(before['candidate_q'] if before else first['candidate_q']);pos=np.array(before['target_xyz'] if before else base['target_xyz']);target=np.array(a['target_xyz']);bad=np.array(a['candidate_q']);fractions=a['refinements'][-1]['collocation_fractions'];contexts=[(f,RecontactScene(guard,**dict(base,target_xyz=(pos+(target-pos)*f).tolist()))) for f in fractions];scene=RecontactScene(guard,**dict(base,target_xyz=target.tolist()));normal=scene.rotation[:,2]
  def cost(x):d=x-q;return float(d@d),2*d
  def one(x,ctx,index=None):
   g=ctx.details(x);T,jl,jw=guard.model.fk(side,x);R=T[:3,:3];v=R@axis;align=float(normal@v);da=normal@(-skew(v)@jw);P=g['point'];J=g['jacobian']
   if index is not None:P=(T[:3,3]+R@vertices[index]-ctx.target)@ctx.rotation;J=ctx.rotation.T@(jl-skew(R@vertices[index])@jw)
   values=np.r_[align*align-.64,half-P[:2],half+P[:2],P[2]-core[2]/2-.006,core[2]/2+.007-P[2],g['inactive_z']-.84,guard.geometry.constraints(x)-.005];jac=np.vstack([2*align*da,-J[:2],J[:2],J[2],-J[2],g['inactive_z_jacobian'],guard.geometry.jacobian(x)])
   if index is None:return values-1e-5,jac
   delta=(vertices[hull]-vertices[index])@R.T;support=delta@normal;support_jac=np.cross(delta,normal)@jw
   return np.r_[values-1e-5,support+1e-10],np.vstack([jac,support_jac])
  def gaps(x):return np.concatenate([np.array(list(ctx.details(q+(x-q)*f)['gaps'].values()))-.01001 for f,ctx in contexts])
  entry=dict(episode=old['episode'],alternative_start_seed=old['alternative_start_seed'],failed_segment_index=a['index'],original_status=a['status'],target_xyz=target.tolist(),attempts=[]);records.append(entry)
  for mode,branch_seed,budget in [('original',bad,560),('fixed_branch_failed',bad,220),('fixed_branch_start',q,220)]:
   indices=[None if mode=='original' else ctx.details(q+(branch_seed-q)*f)['vertex_index'] for f,ctx in contexts]
   def combined(x):
    values=[];grads=[]
    for (f,ctx),index in zip(contexts,indices):
     v,j=one(q+(x-q)*f,ctx,index);values.extend(v);grads.extend(j*f)
    return np.array(values),np.array(grads)
   fit=minimize(cost,bad if mode!='fixed_branch_start' else q,jac=True,bounds=Bounds(guard.lower,guard.upper),constraints=[dict(type='ineq',fun=lambda x:combined(x)[0],jac=lambda x:combined(x)[1]),dict(type='ineq',fun=gaps)],method='SLSQP',options=dict(maxiter=budget,ftol=1e-12));x=np.asarray(fit.x);cm=float(min(combined(x)[0]));gm=float(min(gaps(x)));samples=[];n=max(1,int(np.ceil(max(abs(x-q)/(guard.limits*.25)))))
   for i in range(1,n+1):
    f=i/n;point=q+(x-q)*f;ctx=dict(base,target_xyz=(pos+(target-pos)*f).tolist());g,d=audit.geometry(point,ctx);align=abs(d['rotation'][:,2]@d['pose'][:3,:3]@axis);margin=float(min(align*align-.64,*list(half-abs(d['point'][:2])),g['active_above_top_m']-.004,.010-g['active_above_top_m'],audit.hand.minz(point,inactive)-.84,g['elbow_gap_m']-.005,*list(np.array(list(g['hand_parcel_gaps_m'].values()))-.01)));samples.append(dict(fraction=f,minimum_margin=margin))
   valid=bool(fit.success and cm>=-2e-7 and gm>=-2e-7 and np.all(x>=guard.lower-2e-7) and np.all(x<=guard.upper+2e-7) and all(s['minimum_margin']>=-2e-7 for s in samples));attempt=dict(mode=mode,max_iterations=budget,status=int(fit.status),iterations=int(fit.nit),solver_success=bool(fit.success),candidate_q=x.tolist(),collocation_minimum=cm,hand_gap_minimum=gm,support_vertices=indices,convex_hull_vertices=len(hull),samples=samples,segment_passed=valid);entry['attempts'].append(attempt);save(False);print(json.dumps({k:v for k,v in attempt.items() if k not in ['samples','candidate_q','support_vertices']}|dict(episode=entry['episode'],seed=entry['alternative_start_seed'])),flush=True)
 save(True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');a=p.parse_args();main(a.run)
