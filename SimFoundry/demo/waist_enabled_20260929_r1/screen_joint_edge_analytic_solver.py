"""Compare finite-difference and analytic constraint Jacobians on recorded fallbacks.
Inspect the rejected solver endpoint only; independent endpoint stationarity is not optimizer success or
controller approval, physical contact or permission to accept failed solves.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_joint_edge_command';sys.path[:0]=[str(stage),str(repo)]
import joint_edge_command as helper
from joint_edge_adapter import refine_record
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.data.top_contact_bypass import rotation_xyzw
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
from audit_joint_edge_execution_live import verify_refinement
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();ep=Path(sys.argv[1]).resolve();a=json.loads((ep/'JOINT_EDGE_EXECUTION_LIVE_AUDIT.json').read_text());assert a['passed'] and a['selected'] and a['auditor_sha256']==sha(w/'audit_joint_edge_execution_live.py')
for n,h in a['source_sha256'].items():assert sha(ep/n)==h
prov=json.loads((ep.parent/'provenance.json').read_text())
for n in ['joint_edge_command.py','joint_edge_adapter.py','articulated_hand_geometry.py']:
 key=next(k for k in prov['source_sha256'] if k.endswith('/'+n));assert sha(stage/n)==prov['source_sha256'][key]==sha(ep.parent/'source_snapshot'/key)
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';fr=json.loads((ep/'frontal_bypass.json').read_text());fs={f['step']:f for f in fr['rows']};core=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'];cs=json.loads((ep/'coordination.json').read_text())
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
with np.load(ep/'trace.npz') as z:xyz=z[key].copy()
with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].copy()
original=helper.minimize;captured=[]
def capture(*args,**kwargs):
 result=original(*args,**kwargs);captured.append((result,args,kwargs));return result
helper.minimize=capture;rows=[]
for c in cs:
 trace=c.get('joint_edge_refinement',{})
 if trace.get('reason')!='nonlinear_solver_failed':continue
 t=c['step'];captured.clear();parent=np.asarray(trace['parent_final_upper_command'],dtype=np.float32)
 command,replayed=refine_record(enabled=True,row=fs[t],coordinate=c,current=q[t],previous=u[t-1],parent_command=parent,object_xyz=xyz[t],object_rotation=rotation_xyzw(quat[t].tolist()),core_size=core,model=model,side=side)
 assert replayed['reason']==trace['reason'] and replayed['solver_status']==trace['solver_status'] and np.array_equal(command,u[t]);assert len(captured)==1
 result,args,kw=captured[0];candidate=(q[t].astype(float)+result.x).astype(np.float32);dq=candidate.astype(float)-q[t].astype(float);bounds=kw['bounds'];margins=kw['constraints'][0]['fun'](dq);slack=min(float(np.min(dq-bounds.lb)),float(np.min(bounds.ub-dq)))
 # Hypothetical endpoint checked by the independent analytic-Jacobian auditor.
 # This does not change the recorded fallback or mark the failed optimizer successful.
 rotation=np.asarray(rotation_xyzw(quat[t].tolist()));local=rotation.T@(np.asarray(fs[t]['rear_cop_centering']['cop_world'])-xyz[t]);offset=np.asarray(fs[t]['control_offset_local'])
 def point_jac(angles):
  T,jl,jw=model.fk(side,angles);off=T[:3,:3]@offset;x,y,z=off;skew=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);return T[:3,3]+off,jl-skew@jw
 J=np.vstack([np.asarray(c['control_jacobian_world'],dtype=np.float32),np.asarray(c['contact_normal_tracking']['jacobian'],dtype=np.float32)]).astype(float);errors=[]
 for hand in ['left','right']:
  goal=fs[t]['target_xyz'] if hand==side else c['inactive_anchor'];errors.extend(np.clip(np.float32(.72)*(np.asarray(goal,dtype=np.float32)-np.asarray(c['control_point_positions'][hand],dtype=np.float32)),np.float32(-.035),np.float32(.035)).tolist())
 error=np.r_[np.asarray(errors,dtype=np.float32),np.asarray(c['contact_normal_tracking']['error'],dtype=np.float32)].astype(float);lower=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();upper=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lower[0]=-.98;upper[0]=.98;limits=np.full(11,.04);limits[0]=.015;damping=np.sqrt(np.array([np.float32(.12**2)]+[np.float32(.045**2)]*10))
 shadow=dict(trace,override=True,reason='nonlinear_joint_direction',iterations=int(result.nit),command=candidate.tolist(),final_upper_command=candidate.tolist(),nominal_edge_inward_m=margins[:-1].tolist(),nominal_forward_m=float(margins[-1]))
 try:
  endpoint_check=verify_refinement(shadow,parent,candidate,u[t-1],q[t].astype(float),J,error,damping,lower,upper,limits,point_jac,rotation,local,np.asarray(core),-1 if side=='right' else 1,[3,4,5] if side=='right' else [0,1,2]);endpoint_check['passed']=True
 except AssertionError as error_check:endpoint_check=dict(passed=False,error=str(error_check))
 axes=[k for k in [0,1] if core[k]/2-abs(local[k])<=.01];normals=np.asarray([-np.sign(local[k])*rotation[:,k] for k in axes]);direction=-1 if side=='right' else 1
 def constraint_jac(dq):
  _,jac=point_jac(q[t].astype(float)+dq);return np.vstack([normals@jac,direction*jac[1]])
 x0=np.asarray(args[1]);eps=1e-6;fd=np.column_stack([(kw['constraints'][0]['fun'](x0+np.eye(11)[i]*eps)-kw['constraints'][0]['fun'](x0-np.eye(11)[i]*eps))/(2*eps) for i in range(11)]);derivative_error=float(np.max(abs(fd-constraint_jac(x0))));assert derivative_error<2e-7
 analytic_kw=dict(kw);analytic_kw['constraints']=[dict(kw['constraints'][0],jac=constraint_jac)];analytic=original(*args,**analytic_kw);acmd=(q[t].astype(float)+analytic.x).astype(np.float32);adq=acmd.astype(float)-q[t].astype(float);am=kw['constraints'][0]['fun'](adq)
 ashadow=dict(shadow,iterations=int(analytic.nit),command=acmd.tolist(),final_upper_command=acmd.tolist(),nominal_edge_inward_m=am[:-1].tolist(),nominal_forward_m=float(am[-1]))
 try:
  analytic_check=verify_refinement(ashadow,parent,acmd,u[t-1],q[t].astype(float),J,error,damping,lower,upper,limits,point_jac,rotation,local,np.asarray(core),direction,[3,4,5] if side=='right' else [0,1,2]);analytic_check['passed']=True
 except AssertionError as error_check:analytic_check=dict(passed=False,error=str(error_check))
 variant=dict(status=int(analytic.status),success=bool(analytic.success),iterations=int(analytic.nit),objective=float(analytic.fun),finite_difference_jacobian_error=derivative_error,independent_check=analytic_check,max_difference_from_rejected_endpoint_rad=float(np.max(abs(acmd-candidate))))
 rows.append(dict(analytic_variant=variant,step=t,status=int(result.status),message=str(result.message),iterations=int(result.nit),unchanged_recorded_parent=True,hypothetical_endpoint_independent_check=endpoint_check,rejected_float32_direction_margins_mm=(margins*1000).tolist(),rejected_float32_min_bound_slack_rad=slack,rejected_endpoint_feasible_under_original_numeric_tolerances=bool(margins.min()>=-1e-7 and slack>=-2e-7),rejected_endpoint_command_difference_rad=float(np.max(abs(candidate-parent))),scaled_objective=float(result.fun)))
assert len(rows)==a['numeric_fallback_frames']
out=dict(episode=ep.name,rows=rows,exact_fallbacks_reproduced=len(rows),analytic_success_and_independent_pass=sum(r['analytic_variant']['success'] and r['analytic_variant']['independent_check']['passed'] for r in rows),failed_solver_endpoints_stationary=sum(r['hypothetical_endpoint_independent_check']['passed'] for r in rows),failed_solver_endpoints_feasible=sum(r['rejected_endpoint_feasible_under_original_numeric_tolerances'] for r in rows),source_sha256={n:sha(ep/n) for n in ['JOINT_EDGE_EXECUTION_LIVE_AUDIT.json','raw.npz','frontal_bypass.json','coordination.json','trace.npz','parcel_orientation.npz']},checker_sha256=sha(Path(__file__)),training_ready=False,scope=__doc__)
(ep/'JOINT_EDGE_ANALYTIC_SOLVER_SCREEN.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['rows','source_sha256']},indent=2));print([(r['step'],r['analytic_variant']['status'],r['analytic_variant']['independent_check']['passed']) for r in rows])
