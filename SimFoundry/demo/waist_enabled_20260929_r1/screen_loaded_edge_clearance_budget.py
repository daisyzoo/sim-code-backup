"""Isolated finite-clearance screen at8 real measured/recorded stop states.
Compare original inward-only reference motion with half-remaining local core
clearance (5mm reserve), retaining forward/bounds/slew/elbow/task objective and
independent unscaled1e-6 stationarity. Current virtual reference movement is a
proxy, not actual future COP. No collector integration or physics execution.
For stop states only, object rotation comes from logged unexecuted context.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.optimize import minimize,Bounds,nnls
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_loaded_edge_coverage';sys.path[:0]=[str(stage),str(w),str(repo)]
from clearance_runtime import ClearanceGuard
from audit_unloaded_wrist_prior_live import HandModel
from audit_unloaded_wrist_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';hand=HandModel(urdf,vertices);elbows=IndependentElbows(stage/'elbow_torso_hulls.json',urdf);records=[];sources={}
for cid,task,steps in [(840001,'push_box_to_bin',[396,403,408,862]),(840004,'nudge_mailer_to_bin',[265,266,267,268])]:
 ep=w/'loaded_edge_coverage_groups_r1'/f'case_{cid}'/f'layout_{cid}_{task}';read=lambda n:json.loads((ep/n).read_text());cs={r['step']:r for r in read('coordination.json')};fr=read('frontal_bypass.json');fs={r['step']:r for r in fr['rows']};trs={r['step']:r for r in read('loaded_edge_coverage.json')['rows']};pre={r['step']:r for r in read('self_clearance.json')['rows'] if r['phase']=='pre'};side='right' if task=='push_box_to_bin' else 'left';direction=-1 if side=='right' else 1
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float);us=z['action'][:,12:23].astype(float)
 for t in steps:
  tr=trs[t];ctx=tr['context'];inp=cs[t]['task_inputs'];q=np.array(inp['current']);assert np.array_equal(q,qs[t] if t<len(qs) else pre[t]['upper_q']);assert np.array_equal(inp['previous'],us[t-1]);parent=np.array(tr['parent_upper_command']);R=np.array(ctx['object_rotation']);cop=np.array(ctx['current_cop_local']);core=np.array(ctx['core_size']);offset=np.array(fs[t]['control_offset_local']);J=np.array(inp['jacobian']);E=np.array(inp['error']);damp=np.array(inp['damping']);lo=np.array(tr['bound_low']);hi=np.array(tr['bound_high']);fwd=np.array([0,direction,0])
  def point(x):T,_,_=guard.model.fk(side,x);return T[:3,3]+T[:3,:3]@offset
  def jac(x):T,jl,jw=guard.model.fk(side,x);a,b,c=T[:3,:3]@offset;return jl-np.array([[0,-c,b],[c,0,-a],[-b,a,0]])@jw
  def ipoint(x):T=hand.fk(x,side);return T[:3,3]+T[:3,:3]@offset
  origin=point(q);io=ipoint(q);assert np.max(abs(origin-io))<1e-8
  def cost(x):delta=x-q;res=J@delta-E;return 100*float(res@res+sum(damp*damp*delta*delta)),200*(J.T@res+damp*damp*delta)
  for mode in ['original_direction','finite_clearance_budget']:
   if mode=='original_direction':A=np.vstack([[-np.sign(cop[k])*R[:,k] for k in tr['threatened_axes']],fwd]);b=np.zeros(len(A))
   else:
    upper=.5*(core[:2]/2-.005-cop[:2]);lower=.5*(-core[:2]/2+.005-cop[:2]);A=np.vstack([-R[:,:2].T,R[:,:2].T,fwd]);b=np.r_[upper,-lower,0]
   def constraints(x):return np.r_[b+A@(point(x)-origin),guard.geometry.constraints(x)-.005]
   def cj(x):return np.vstack([A@jac(x),guard.geometry.jacobian(x)])
   def independent(x):
    x=np.asarray(x,dtype=np.float32).astype(float)
    def c(y):return np.r_[b+A@(ipoint(y)-io),elbows.gap(y)-.005]
    values=c(x);valid=bool(np.isfinite(x).all() and min(values[:len(A)])>=-1e-7 and min(values[len(A):])>=-2e-7 and min(x-lo)>=-2e-7 and min(hi-x)>=-2e-7)
    if not valid:return dict(passed=False,reason='feasibility',minimum_linear_residual_m=float(min(values[:len(A)])))
    I=np.eye(11);h=1e-5;G=np.column_stack([(c(x+I[k]*h)-c(x-I[k]*h))/(2*h) for k in range(11)]);normals=[G[k] for k in range(len(values)) if values[k]<=1e-6]
    for k in range(11):
     if x[k]-lo[k]<=2e-6:normals.append(I[k])
     if hi[k]-x[k]<=2e-6:normals.append(-I[k])
    grad=J.T@(J@(x-q)-E)+damp*damp*(x-q)
    if normals:
     B=np.array(normals);length=np.linalg.norm(B,axis=1);B=B[length>1e-12]/length[length>1e-12,None];_,residual=nnls(B.T,grad,maxiter=1000)
    else:residual=np.linalg.norm(grad)
    move=ipoint(x)-io;future=cop+R.T@move
    return dict(passed=bool(residual<=1e-6),stationarity_residual=float(residual),nominal_forward_m=float(fwd@move),command_local_motion_m=(R.T@move).tolist(),proxy_contact_margins_xy_m=(core[:2]/2-abs(future[:2])).tolist(),command=x.tolist())
   attempts=[]
   for label,x0 in [('current',q),('parent',parent),('previous',us[t-1])]:
    fit=minimize(cost,np.clip(x0,lo,hi),jac=True,bounds=Bounds(lo,hi),constraints=[dict(type='ineq',fun=constraints,jac=cj)],method='SLSQP',options=dict(maxiter=300,ftol=1e-11));v=independent(fit.x);attempts.append(dict(seed=label,status=int(fit.status),success=bool(fit.success),iterations=int(fit.nit),cost=cost(np.asarray(fit.x,dtype=np.float32).astype(float))[0],independent=v))
   accepted=[a for a in attempts if a['success'] and a['independent']['passed']];best=min(accepted,key=lambda a:a['cost']) if accepted else None
   records.append(dict(episode=ep.name,step=t,stopped=t==len(qs),mode=mode,current_contact_margins_xy_m=(core[:2]/2-abs(cop[:2])).tolist(),current_inside5mm_reserve=bool(min(core[:2]/2-abs(cop[:2]))>=.005),accepted=best is not None,best=best,attempts=attempts));print(ep.name,t,mode,'forward_mm',None if best is None else best['independent']['nominal_forward_m']*1000,flush=True)
 for name in ['raw.npz','coordination.json','frontal_bypass.json','loaded_edge_coverage.json','self_clearance.json']:sources[str(ep/name)]=sha(ep/name)
for p in [Path(__file__),stage/'clearance_runtime.py',stage/'articulated_hand_geometry.py',stage/'self_clearance.py',stage/'elbow_torso_hulls.json',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',urdf,vertices]:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,states=8,comparisons=16,records=records,source_sha256=sources,collector_connected=False,physical_validation=False,training_ready=False);(w/'LOADED_EDGE_CLEARANCE_BUDGET_SCREEN.json').write_text(json.dumps(out,indent=2));print('DONE8states16comparisons',flush=True)
