"""Offline causal-seed minimum joint-motion endpoints, PCA alignment >=0.8.
Seeds are original causal planner endpoint and current observed q only.
0.8 is a diagnostic comparison, not a physical palm/contact or training gate.
Retains original20mm inset,6..7mm height,parcel/elbow gaps and joint bounds.
Whole independent nominal path verified; no live controller changes.
"""
from pathlib import Path
import json,hashlib,sys,datetime
import numpy as np
from scipy.optimize import minimize,Bounds
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_precise_parent_seed';sys.path[:0]=[str(stage),str(repo),str(w)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from articulated_hand_geometry import skew
from audit_recontact_pose_events import EventAudit
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);independent=EventAudit(repo,stage);records=[];sources={};axes={}

for side in ['left','right']:
 values,vectors=np.linalg.eigh(np.cov(guard.model.vertices[side].T));axes[side]=vectors[:,0]
for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
 ep=w/'precise_interior_groups_r1'/f'case_{cid}'/f'layout_{cid}_{task}';events=json.loads((ep/'recontact_pose.json').read_text())['rows'];starts=[e for e in events if e.get('planning') is not None]
 for event in starts:
  ctx=event['context'];q=np.array(ctx['current']);scene=RecontactScene(guard,**ctx['scene']);assert scene.check(q)['accepted'];wi=5 if scene.side=='left' else 10;axis=axes[scene.side];normal=scene.rotation[:,2];half=scene.core[:2]/2-.020
  def alignment(x):
   T,jl,jw=guard.model.fk(scene.side,x);v=T[:3,:3]@axis;return float(normal@v),normal@(-skew(v)@jw)
  def cost(x):
   delta=x-q;return float(delta@delta),2*delta
  def cons(x):
   g=scene.details(x);p=g['point'];J=g['jacobian'];a,da=alignment(x);return np.r_[a*a-.8**2,half-p[:2],half+p[:2],p[2]-scene.core[2]/2-.006,scene.core[2]/2+.007-p[2],g['inactive_z']-.84,guard.geometry.constraints(x)-.005],np.vstack([2*a*da,-J[:2],J[:2],J[2],-J[2],g['inactive_z_jacobian'],guard.geometry.jacobian(x)])
  old=event['planning'];original=np.array(old['endpoint']) if old['accepted'] else q.copy();seeds=[('original_endpoint',original)]
  seeds.append(('current_observed',q.copy()))
  attempts=[]
  for label,seed in seeds:
   fit=minimize(cost,np.clip(seed,guard.lower,guard.upper),jac=True,bounds=Bounds(guard.lower,guard.upper),constraints=[dict(type='ineq',fun=lambda x:cons(x)[0],jac=lambda x:cons(x)[1]),dict(type='ineq',fun=lambda x:np.array(list(scene.details(x)['gaps'].values()))-.01)],method='SLSQP',options=dict(maxiter=220,ftol=1e-12));x=np.array(fit.x);g=scene.details(x);minimum=float(min(cons(x)[0]));accepted=bool(fit.success and minimum>=-2e-7 and min(g['gaps'].values())>=.01-2e-7)
   fd=np.array([(cost(x+np.eye(11)[i]*1e-6)[0]-cost(x-np.eye(11)[i]*1e-6)[0])/2e-6 for i in range(11)]);err=float(max(abs(fd-cost(x)[1])));assert err<1e-6
   ig,idata=independent.geometry(x,ctx['scene']);margins=idata['core'][:2]/2-abs(idata['point'][:2]);height=ig['active_above_top_m'];minimum_ind=float(min(alignment(x)[0]**2-.8**2,*list(margins-.020),height-.006,.007-height,independent.hand.minz(x,'right' if scene.side=='left' else 'left')-.84,ig['elbow_gap_m']-.005));assert abs(minimum-minimum_ind)<2e-8
   verified=bool(accepted and minimum_ind>=-2e-7 and min(ig['hand_parcel_gaps_m'].values())>=.01-2e-7 and np.all(x>=guard.lower-2e-7) and np.all(x<=guard.upper+2e-7));assert verified==accepted
   path_ok=False;count=0
   if verified:
    count=max(1,int(np.ceil(max(abs(x-q)/(guard.limits*.25)))));path=[np.clip(q+(x-q)*i/count,guard.lower,guard.upper) for i in range(1,count+1)];checks=[independent.geometry(y,ctx['scene'])[0]['accepted'] for y in path];path_ok=all(checks)
   attempts.append(dict(seed=label,status=int(fit.status),iterations=int(fit.nit),accepted=accepted,objective=float(fit.fun),thin_axis_alignment_abs=abs(alignment(x)[0]),wrist_rad=float(x[wi]),waist_rad=float(x[0]),minimum_constraint_m=minimum_ind,gradient_max_error=err,independent_path_geometry_passed=path_ok,path_samples=count,candidate=x.tolist()))
  best=min(attempts,key=lambda a:(not(a['accepted'] and a['independent_path_geometry_passed']),a['objective']))
  records.append(dict(episode=ep.name,step=event['step'],original_accepted=old['accepted'],original_alignment_abs=abs(alignment(original)[0]),original_selected_inset_m=old.get('interior_preference',{}).get('selected_inset_m'),best=best,attempts=attempts));print(ep.name,event['step'],'old align',records[-1]['original_alignment_abs'],'new',best['thin_axis_alignment_abs'],'endpoint',best['accepted'],'path',best['independent_path_geometry_passed'],flush=True)
  for p in [ep/'recontact_pose.json',ep/'raw.npz']:sources[str(p)]=sha(p)
  report=dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),complete=False,records=records,axes={k:v.tolist() for k,v in axes.items()},source_sha256=sources,physical_validation=False,controller_changed=False,training_ready=False);(w/'CAUSAL_MINIMUM_MOTION_FACE_SCREEN.json').write_text(json.dumps(report,indent=2))
assert len(records)==16
for p in [Path(__file__),w/'audit_recontact_pose_events.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',stage/'clearance_runtime.py',stage/'recontact_scene.py',stage/'articulated_hand_geometry.py',stage/'self_clearance.py',stage/'elbow_torso_hulls.json',repo/'assets/robots/g1_hand_support_vertices.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
report.update(complete=True,source_sha256=sources);(w/'CAUSAL_MINIMUM_MOTION_FACE_SCREEN.json').write_text(json.dumps(report,indent=2));print('COMPLETE16',flush=True)
