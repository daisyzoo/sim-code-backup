"""Offline solver numerics across the complete closed8push set; no physical changes.
Only equivalent residual evaluation or one analytical-SLSQP restart varies. Objective, boundaries,
first-load/guard selection and final float32 checks stay unchanged. Recorded
states/previous actions fixed; this is not recursive rollout or task efficacy.
"""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_joint_edge_command';sys.path[:0]=[str(stage),str(repo),str(w)]
import joint_edge_command as helper
from joint_edge_adapter import refine_record
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.data.top_contact_bypass import rotation_xyzw
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
from audit_joint_edge_execution_live import verify_refinement
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();run=w/'joint_edge_groups_r1';closed=json.loads((run/'RESULT.json').read_text());assert closed['actual_review_complete'] and closed['push_total']==8
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');original=helper.minimize;variants=['baseline','residual_fd','residual_analytic','analytic_restart'];reports=[]
for ep in sorted(run.glob('case_*/layout_*')):
 if ep.name.endswith('wait_no_package'):continue
 prov=json.loads((ep.parent/'provenance.json').read_text())
 for n,h in prov['source_sha256'].items():assert sha(ep.parent/'source_snapshot'/n)==h
 for name in ['joint_edge_command.py','joint_edge_adapter.py','articulated_hand_geometry.py']:
  key=next(n for n in prov['source_sha256'] if n.endswith('/'+name));assert sha(stage/name)==prov['source_sha256'][key]
 audit=json.loads((ep/'JOINT_EDGE_EXECUTION_LIVE_AUDIT.json').read_text());assert audit['passed'] and audit['auditor_sha256']==sha(w/'audit_joint_edge_execution_live.py')
 for n,h in audit.get('source_sha256',{}).items():assert sha(ep/n)==h
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
 key='box' if 'push_box' in ep.name else 'mailer';side='right' if key=='box' else 'left';direction=-1 if side=='right' else 1;active=[3,4,5] if side=='right' else [0,1,2]
 with np.load(ep/'trace.npz') as z:xyz=z[key].copy()
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].copy()
 fr=json.loads((ep/'frontal_bypass.json').read_text());cs={c['step']:c for c in json.loads((ep/'coordination.json').read_text())};selected=bool(fr['plan'].get('rear_joint_edge_command',{}).get('enabled'));core=np.asarray(fr['plan'].get('region_causal_response',{}).get('actual_core',{}).get('collision_core_size_xyz',[.1,.1,.1]));counts={name:collections.Counter() for name in variants};rows=[];maxjac=0.
 assert np.max(abs(q[0]))==np.max(abs(u[0]))==0
 for f in fr['rows']:
  t=f['step'];c=cs[t];trace=c.get('joint_edge_refinement');parent=np.asarray(trace['parent_final_upper_command'],dtype=np.float32) if selected else u[t].copy();rotation=np.asarray(rotation_xyzw(quat[t].tolist()));eligible=selected and f['mode']=='top_push' and bool(f.get('rear_joint_xy_progress',{}).get('override')) and not c.get('region_joint_override') and not c.get('terminal_joint_hold');baseline=None;results=[]
  if eligible:
   local=rotation.T@(np.asarray(f['rear_cop_centering']['cop_world'])-xyz[t]);axes=[k for k in [0,1] if core[k]/2-abs(local[k])<=.01];normals=np.asarray([-np.sign(local[k])*rotation[:,k] for k in axes]);offset=np.asarray(f['control_offset_local'])
   def point_jac(command):
    T,jl,jw=model.fk(side,command);off=T[:3,:3]@offset;x,y,z=off;skew=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);return T[:3,3]+off,jl-skew@jw
   def constraint_jac(dq):
    _,jac=point_jac(q[t].astype(float)+dq);return np.vstack([normals@jac,direction*jac[1]])
   J=np.vstack([np.asarray(c['control_jacobian_world'],dtype=np.float32),np.asarray(c['contact_normal_tracking']['jacobian'],dtype=np.float32)]).astype(float);errors=[]
   for hand in ['left','right']:
    goal=f['target_xyz'] if hand==side else c['inactive_anchor'];errors.extend(np.clip(np.float32(.72)*(np.asarray(goal,dtype=np.float32)-np.asarray(c['control_point_positions'][hand],dtype=np.float32)),np.float32(-.035),np.float32(.035)).tolist())
   error=np.r_[np.asarray(errors,dtype=np.float32),np.asarray(c['contact_normal_tracking']['error'],dtype=np.float32)].astype(float);lower=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();upper=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lower[0]=-.98;upper[0]=.98;limits=np.full(11,.04);limits[0]=.015;damping=np.sqrt(np.array([np.float32(.12**2)]+[np.float32(.045**2)]*10)).astype(float)
  for name in variants:
   def solve(*args,**kwargs):
    if name=='baseline':return original(*args,**kwargs)
    kwargs=dict(kwargs);original_fun=kwargs['constraints'][0]['fun'];x0=np.asarray(args[1]);eps=1e-6
    if name!='residual_fd':
     fd=np.column_stack([(original_fun(x0+np.eye(11)[i]*eps)-original_fun(x0-np.eye(11)[i]*eps))/(2*eps) for i in range(11)]);jacerr=float(np.max(abs(fd-constraint_jac(x0))));assert jacerr<2e-7;jac_errors.append(jacerr)
     kwargs['constraints']=[dict(type='ineq',fun=original_fun,jac=constraint_jac)]
    if name.startswith('residual_'):
     def residual_fun(x):
      residual=J@x-error;return 5000*float(residual@residual+np.sum((damping*x)**2))
     def residual_grad(x):return 10000*(J.T@(J@x-error)+damping*damping*x)
     for sample in [x0,np.zeros(11),np.clip(parent.astype(float)-q[t].astype(float),kwargs['bounds'].lb,kwargs['bounds'].ub)]:
      assert abs(residual_fun(sample)-args[0](sample)-5000*float(error@error))<1e-11
      assert np.max(abs(residual_grad(sample)-kwargs['jac'](sample)))<1e-9
     args=(residual_fun,*args[1:]);kwargs['jac']=residual_grad
    result=original(*args,**kwargs)
    if name=='analytic_restart' and result.status==8 and np.isfinite(result.x).all():
     retry_start=np.clip(result.x,kwargs['bounds'].lb,kwargs['bounds'].ub)
     # Same objective/constraints/tolerances, reset SLSQP internal approximation once.
     result=original(args[0],retry_start,**kwargs)
    return result
   jac_errors=[];helper.minimize=solve
   try:command,newtrace=refine_record(enabled=selected,row=f,coordinate=c,current=q[t],previous=u[t-1],parent_command=parent,object_xyz=xyz[t],object_rotation=rotation,core_size=core,model=model,side=side)
   finally:helper.minimize=original
   counts[name]['frames']+=1
   if jac_errors:maxjac=max(maxjac,max(jac_errors))
   if name=='baseline':
    baseline=command.copy();assert np.array_equal(command,u[t]),(ep.name,t,float(np.max(abs(command-u[t]))))
    if selected:assert newtrace==trace,(ep.name,t,'trace mismatch')
   if not selected or not eligible:assert np.array_equal(command,parent);counts[name]['protected']+=1
   elif newtrace['override']:
    check=verify_refinement(newtrace,parent,command,u[t-1],q[t].astype(float),J,error,damping,lower,upper,limits,point_jac,rotation,local,core,direction,active);assert check['refined'];counts[name]['modified']+=1
   else:assert np.array_equal(command,parent);check=dict(refined=False,reason=newtrace['reason']);counts[name][newtrace['reason']]+=1
   if eligible:
    dq=command.astype(float)-q[t].astype(float);objective=float(np.linalg.norm(J@dq-error)**2+np.linalg.norm(damping*dq)**2)
    results.append(dict(name=name,override=newtrace['override'],reason=newtrace['reason'],solver_status=newtrace.get('solver_status'),command=command.tolist(),max_difference_from_baseline_rad=float(np.max(abs(command-baseline))),objective=objective,independent_check=check))
  if eligible:rows.append(dict(step=t,variants=results))
 reports.append(dict(episode=ep.name,selected=selected,counts={k:dict(v) for k,v in counts.items()},max_constraint_jacobian_fd_error=maxjac,rows=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','frontal_bypass.json','trace.npz','parcel_orientation.npz','JOINT_EDGE_EXECUTION_LIVE_AUDIT.json']}));print(ep.name,reports[-1]['counts'],flush=True)
assert len(reports)==8
out=dict(passed=True,episodes=reports,baseline_result_sha256=sha(run/'RESULT.json'),checker_sha256=sha(Path(__file__)),training_ready=False,scope=__doc__)
(w/'JOINT_EDGE_SOLVER_STABILITY_SCREEN.json').write_text(json.dumps(out,indent=2));print('all8passed')
