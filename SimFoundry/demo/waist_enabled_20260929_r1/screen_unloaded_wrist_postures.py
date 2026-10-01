"""Unexecuted static and interpolated posture screen at recorded unloaded crossings.
Compare preserved current palm normal versus free normal ONLY in these unloaded
states. Keep both hand reference positions, original joint limits and elbow5mm.
Interpolation checks command rates, hand height and inactive15mm displacement;
not a full-body/substep/contact/dynamic certificate. No simulator writes.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.optimize import minimize,Bounds
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_micro_clearance_return';sys.path[:0]=[str(stage),str(repo)]
from clearance_runtime import ClearanceGuard
from articulated_hand_geometry import skew
from simfoundry.data.projected_support_reference import projected_support_reference,projected_support_jacobian
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);out=[]
for run in ['micro_clearance_groups_r1','rear_short_recovery_groups_r1']:
 for cid,task,side,wi in [(840001,'push_box_to_bin','right',10),(840004,'nudge_mailer_to_bin','left',5)]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())}
  with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float);commands=z['action'][:,12:23].astype(float)
  crosses=[];last=None
  for r in fr['rows']:
   if r['mode']=='top_cross' and last!='top_cross' and r['recontacts']>0:crosses.append(r)
   last=r['mode']
  assert crosses
  for r in [crosses[0],crosses[-1]]:
   assert r['contact_load']['observed_vertical_load_n']==0.;t=r['step'];c=cs[t];q=qs[t];inactive='left' if side=='right' else 'right';reference=c['active_support_reference'];normal=np.array(reference['world_normal']);center=np.array(reference['center_local']);vertices=guard.model.vertices[side]
   def geom(x):
    T,jl,jw=guard.model.fk(side,x);R=T[:3,:3];ref=projected_support_reference(vertices,R,normal,center_local=center);active=T[:3,3]+R@ref['reference_local'];J=projected_support_jacobian(jl,jw,R,ref)
    Ti,jli,jwi=guard.model.fk(inactive,x);off=Ti[:3,:3]@np.array([.20,0,.007]);palm=Ti[:3,3]+off;Ji=jli-skew(off)@jwi;world=vertices@R.T+T[:3,3];low=int(np.argmin(world[:,2]));zj=(jl-skew(R@vertices[low])@jw)[2];up=R[2];upj=R.T@skew([0.,0.,1.])@jw
    return np.r_[active,palm],np.vstack([J,Ji]),float(world[low,2]),zj,up,upj
   goal,_,initial_minz,_,up0,_=geom(q);floor=min(initial_minz,.84)
   def cost(x):d=x-q;return float(x[wi]**2+.002*(d@d)),2*np.eye(11)[wi]*x[wi]+.004*d
   candidates=[]
   for hold in [True,False]:
    def cons(x):
     pos,jac,minz,zjac,up,uj=geom(x);e=pos-goal;values=np.r_[.0005-e,.0005+e,minz-floor,guard.geometry.constraints(x)-.005];J=np.vstack([-jac,jac,zjac,guard.geometry.jacobian(x)])
     if hold:values=np.r_[values,.001-(up-up0),.001+(up-up0)];J=np.vstack([J,-uj,uj])
     return values,J
    starts=[np.clip(q,guard.lower,guard.upper)];second=starts[0].copy();second[wi]=0.;starts.append(second)
    best=None
    for initial in starts:
     fit=minimize(cost,initial,jac=True,bounds=Bounds(guard.lower,guard.upper),constraints=[dict(type='ineq',fun=lambda x:cons(x)[0],jac=lambda x:cons(x)[1])],method='SLSQP',options=dict(maxiter=250,ftol=1e-12));cand=fit.x;res=cons(cand)[0];valid=bool(fit.success and min(res)>=-2e-7)
     entry=dict(hold_normal=hold,success=valid,solver_status=int(fit.status),iterations=int(fit.nit),minimum_constraint_m=float(min(res)),wrist_rad=float(cand[wi]),wrist_reduction_rad=float(abs(q[wi])-abs(cand[wi])),candidate=cand.tolist(),objective=float(fit.fun))
     if best is None or (valid and not best['success']) or (valid==best['success'] and fit.fun<best['objective']):best=entry
    if best['success']:
     target=np.array(best['candidate']);n=max(1,int(np.ceil(max(abs(target-q)/np.r_[.0075,np.full(10,.02)]))));path=np.array([np.clip(q+(target-q)*i/n,guard.lower,guard.upper) for i in range(n+1)]);pgeom=[geom(x) for x in path];checks=[];prev=commands[t-1]
     for i,x in enumerate(path):checks.append(guard.command(x,q if i==0 else path[i-1],prev));prev=x
     minz=min(g[2] for g in pgeom);inactive_delta=max(float(np.linalg.norm(g[0][3:]-goal[3:])) for g in pgeom);min_gap=min(float(guard.geometry.constraints(x).min()) for x in path)
     best['interpolation']=dict(steps=n+1,all_command_geometry_checks=all(a['accepted'] for a in checks),minimum_active_hand_z_m=minz,required_floor_m=floor,minimum_elbow_gap_m=min_gap,max_inactive_palm_displacement_m=inactive_delta,max_active_reference_displacement_m=max(float(np.linalg.norm(g[0][:3]-goal[:3])) for g in pgeom),passed=bool(all(a['accepted'] for a in checks) and minz>=floor-2e-7 and inactive_delta<=.015))
    candidates.append(best)
   row=dict(run=run,episode=ep.name,step=t,mode=r['mode'],observed_load_n=0.,initial_wrist_rad=float(q[wi]),initial_min_hand_z_m=initial_minz,candidates=candidates,source_sha256={name:sha(ep/name) for name in ['raw.npz','coordination.json','frontal_bypass.json']});out.append(row);print(run,ep.name,t,[(a['hold_normal'],a['success'],round(a['wrist_reduction_rad'],3),a.get('interpolation',{}).get('passed')) for a in candidates],flush=True)
report=dict(scope=__doc__,rows=out,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'clearance_runtime.py',stage/'articulated_hand_geometry.py',stage/'self_clearance.py',stage/'elbow_torso_hulls.json',repo/'simfoundry/data/projected_support_reference.py']},model_source_sha256=guard.model.source_sha256,controller_changed=False,training_ready=False)
(w/'UNLOADED_WRIST_POSTURE_SCREEN.json').write_text(json.dumps(report,indent=2))
