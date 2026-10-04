"""Same objective/constraints/tolerances, alternate derivatives or start only.
Isolated archived frame655 numerical probe, not a physical controller change.
"""
from pathlib import Path
import copy,datetime,hashlib,json,sys
import numpy as np
from scipy.optimize import minimize,linprog,Bounds
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_early_edge_v1';D=W/'rear_early_bag_stationarity_probe_r1';D.mkdir(exist_ok=False);sys.path[:0]=[str(S),str(W),str(ROOT)]
from articulated_hand_geometry import ArticulatedHandGeometry,skew
from audit_unloaded_wrist_prior_live import HandModel
from audit_box_inward_refinement import verify_refinement
from joint_edge_command import refine_rear_command
from clearance_runtime import ClearanceGuard
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=W/'rear_early_edge_physical_r1/case_840020/layout_840020_nudge_mailer_to_bin';prov=read(ep.parent/'provenance.json');sources={}
def archived(name):
 ks=[k for k in prov['source_sha256'] if Path(k).name==name];assert len(ks)==1;p=ep.parent/'source_snapshot'/ks[0];assert sha(p)==prov['source_sha256'][ks[0]];sources[str(p)]=sha(p);return p
urdf=archived('g1_23dof_rev_1_0_u1_black.urdf');vertices=archived('g1_hand_support_vertices.json');model=ArticulatedHandGeometry(urdf,vertices);hand=HandModel(urdf,vertices)
assert sha(archived('joint_edge_command.py'))==sha(S/'joint_edge_command.py')
f=read(W/'rear_early_bag_stationarity_r1/CONTEXT_655.json');c=f['coordinate'];row=f['frontal_row'];old=c['joint_edge_refinement'];a=c['task_inputs'];q=np.asarray(f['current']);prev=np.asarray(f['previous']);parent=np.asarray(old['parent_final_upper_command']);x=np.asarray(old['final_upper_command']);J=np.asarray(a['jacobian']);e=np.asarray(a['error']);damp=np.asarray(a['damping']);lo=np.asarray(a['lower']);hi=np.asarray(a['upper']);lim=np.asarray(a['step_limits']);R=np.asarray(f['object_rotation']);core=np.asarray(f['core_size']);local=R.T@(np.asarray(row['rear_cop_centering']['cop_world'])-np.asarray(f['object_xyz']));off=np.asarray(row['control_offset_local']);axes=old['threatened_axes'];normals=np.asarray([-np.sign(local[k])*R[:,k] for k in axes])
def point(v):
 T,_,_=model.fk('left',v);return T[:3,3]+T[:3,:3]@off
def jac(v):
 T,jl,jw=model.fk('left',v);return jl-skew(T[:3,:3]@off)@jw
def ipoint(v):
 T=hand.fk(v,'left');return T[:3,3]+T[:3,:3]@off
def ipj(v):
 h=2e-7;return ipoint(v),np.stack([(ipoint(v+np.eye(11)[j]*h)-ipoint(v-np.eye(11)[j]*h))/(2*h) for j in range(11)],axis=1)
for v in [q,x,parent]:assert np.max(abs(point(v)-ipoint(v)))<2e-12 and np.max(abs(jac(v)-ipj(v)[1]))<2e-8
low=np.maximum.reduce([lo-q,-lim,prev-.055-q]);high=np.minimum.reduce([hi-q,lim,prev+.055-q]);origin=point(q)
def constraints(dq):
 motion=point(q+dq)-origin;return np.r_[normals@motion,motion[1]]
def derivative(dq):
 g=jac(q+dq);return np.vstack([normals@g,g[1]])
design=np.vstack([J,np.diag(damp)]);rhs=np.r_[e,np.zeros(11)];H=design.T@design;g=design.T@rhs;fun=lambda d:5000*float(d@H@d-2*g@d);grad=lambda d:10000*(H@d-g)
A=np.vstack([normals@J[:3],J[1]]);lp=linprog(np.zeros(11),A_ub=-A,b_ub=np.zeros(len(A)),bounds=list(zip(low,high)),method='highs');assert lp.success
kwargs=dict(enabled=True,mode='top_push',selected=True,current=q,previous=prev,parent_command=parent,jacobian=J,error=e,damping=damp,lower=lo,upper=hi,step_limits=lim,object_rotation=R,cop_local=local,core_size=core,direction=1,active_rows=[0,1,2],point_fn=point,point_jacobian_fn=jac,analytic_retry=True,parent_seed_retry=True)
reproduced=refine_rear_command(**kwargs);assert reproduced['override'];reproduced_u=np.asarray(reproduced['command']);reproduction=dict(command_exact=np.array_equal(reproduced_u,x),maximum_delta_rad=float(np.max(abs(reproduced_u-x))),iterations=reproduced.get('iterations'))
guard=ClearanceGuard(ROOT,S);rows=[]
for name,start,analytic in [('original_reproduced',None,False),('analytic_lp',lp.x,True),('analytic_original_output',x-q,True),('analytic_parent',np.clip(parent-q,low,high),True)]:
 if start is None:u=reproduced_u;status=0;iterations=reproduced['iterations']
 else:
  solve=minimize(fun,start,jac=grad,bounds=Bounds(low,high),constraints=[dict(type='ineq',fun=constraints,jac=derivative)] if analytic else [dict(type='ineq',fun=constraints)],method='SLSQP',options=dict(ftol=1e-11,maxiter=300));u=(q+solve.x).astype(np.float32).astype(float);status=int(solve.status);iterations=int(solve.nit)
 values=constraints(u-q);trace=copy.deepcopy(old);trace.update(command=u.tolist(),final_upper_command=u.tolist(),iterations=iterations,nominal_edge_inward_m=values[:-1].tolist(),nominal_forward_m=float(values[-1]))
 try:cert=verify_refinement(trace,parent,u,prev,q,J,e,damp,lo,hi,lim,ipj,R,local,core,1,[0,1,2],inward_enabled=False);error=None
 except AssertionError as exc:cert=None;error=str(exc)
 r=dict(case=name,solver_status=status,iterations=iterations,independent_certificate=cert,error=error,command=u.tolist(),maximum_change_from_original_rad=float(np.max(abs(u-x))),objective=.5*float(np.linalg.norm(J@(u-q)-e)**2+np.linalg.norm(damp*(u-q))**2),direction_m=values.tolist(),final_guard=guard.command(u,q,prev),task_math_unchanged=True)
 rows.append(r);print(json.dumps({k:v for k,v in r.items() if k not in ['command','final_guard']}),flush=True)
for p in [Path(__file__),W/'rear_early_bag_stationarity_r1/RESULT.json',W/'rear_early_bag_stationarity_r1/CONTEXT_655.json',S/'joint_edge_command.py',S/'articulated_hand_geometry.py',W/'audit_unloaded_wrist_prior_live.py',W/'audit_box_inward_refinement.py',W/'audit_box_entry_pose_loaded_execution.py']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,reproduction=reproduction,rows=rows,source_sha256=sources,original_threshold=1e-6,original_failure_preserved=True,physics_started=False,training_ready=False)
(D/'RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(reproduction),flush=True)
