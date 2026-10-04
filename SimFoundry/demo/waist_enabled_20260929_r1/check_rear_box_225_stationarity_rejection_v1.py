"""Same recorded225 observation: FD sensitivity and unissued analytic-first solve.
No changed audit tolerance, actual state, later trajectory or training admission.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import nnls
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from articulated_hand_geometry import ArticulatedHandGeometry,skew
from audit_unloaded_wrist_prior_live import HandModel
from audit_box_inward_refinement import verify_refinement
from joint_edge_inward_command import refine_rear_command as original
from joint_edge_inward_analytic_first_candidate_v2 import refine_rear_command as candidate
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());R=W/'front_effective_height_physical_r1';ep=R/'case_840023/layout_840023_push_box_to_bin';t=225
urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=ROOT/'assets/robots/g1_hand_support_vertices.json';model=ArticulatedHandGeometry(urdf,vertices);hand=HandModel(urdf,vertices)
with np.load(ep/'raw.npz') as z:q=z['q'][t,12:23].astype(float);previous=z['action'][t-1,12:23].astype(float);actual=z['action'][t,12:23].astype(float)
with np.load(ep/'trace.npz') as z:xyz=z['box'][t].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['box'][t]).as_matrix()
c=next(x for x in read(ep/'coordination.json') if x['step']==t);fr=read(ep/'frontal_bypass.json');row=next(x for x in fr['rows'] if x['step']==t);a=c['task_inputs'];old=c['joint_edge_refinement'];core=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']);offset=np.array(row['control_offset_local']);J=np.array(a['jacobian']);error=np.array(a['error']);damping=np.array(a['damping']);lower=np.array(a['lower']);upper=np.array(a['upper']);limits=np.array(a['step_limits']);parent=np.array(old['parent_final_upper_command']);local=rot.T@(np.array(row['rear_cop_centering']['cop_world'])-xyz)
np.testing.assert_array_equal(q,a['current']);np.testing.assert_array_equal(previous,a['previous']);np.testing.assert_array_equal(actual,old['final_upper_command']);assert not c['joint_edge_clearance_intersection']['changed']
def point(q):
 T=model.fk('right',q)[0];return T[:3,3]+T[:3,:3]@offset
def jac(q):
 T,jl,jw=model.fk('right',q);return jl-skew(T[:3,:3]@offset)@jw
def independent_point(q):
 T=hand.fk(q,'right');return T[:3,3]+T[:3,:3]@offset
def fd(q,h):
 return np.column_stack([(independent_point(q+np.eye(11)[j]*h)-independent_point(q-np.eye(11)[j]*h))/(2*h) for j in range(11)])
np.testing.assert_allclose(point(q),row['observed_support_xyz'],rtol=0,atol=2e-6);np.testing.assert_allclose(point(actual),independent_point(actual),rtol=0,atol=1e-12)
axes=[k for k in (0,1) if core[k]/2-abs(local[k])<=.01];normals=np.array([-np.sign(local[k])*rot[:,k] for k in axes]);low=np.maximum.reduce([lower-q,-limits,previous-.055-q]);high=np.minimum.reduce([upper-q,limits,previous+.055-q]);dq=actual-q;motion=independent_point(actual)-independent_point(q);values=np.r_[normals@motion-.0005,-motion[1]];grad=J.T@(J@dq-error)+damping*damping*dq
sensitivity=[]
for label,G in [('fd1e-6',fd(actual,1e-6)),('fd2e-7',fd(actual,2e-7)),('fd5e-8',fd(actual,5e-8)),('analytic',jac(actual))]:
 gradients=np.vstack([normals@G,-G[1]]);active=[gradients[i] for i in range(len(values)) if values[i]<=1e-6]
 for i in range(11):
  if dq[i]-low[i]<=2e-6:active.append(np.eye(11)[i])
  if high[i]-dq[i]<=2e-6:active.append(-np.eye(11)[i])
 if active:
  mat=np.array(active);length=np.linalg.norm(mat,axis=1);mat=mat[length>1e-12]/length[length>1e-12,None];_,res=nnls(mat.T,grad,maxiter=1000)
 else:res=float(np.linalg.norm(grad))
 sensitivity.append(dict(method=label,stationarity=float(res),passes_original_gate=bool(res<=1e-6),jacobian_max_difference_from_analytic=float(np.max(abs(G-jac(actual))))))
kwargs=dict(enabled=True,mode=row['mode'],selected=True,current=q,previous=previous,parent_command=parent,jacobian=J,error=error,damping=damping,lower=lower,upper=upper,step_limits=limits,object_rotation=rot,cop_local=local,core_size=core,direction=-1,active_rows=[3,4,5],point_fn=point,point_jacobian_fn=jac,analytic_retry=True,parent_seed_retry=True)

from types import SimpleNamespace
import joint_edge_inward_analytic_first_candidate_v2 as module
original_minimize=module.minimize
calls=[]
def solved_but_insufficient(*args,**kw):
 calls.append(dict(ftol=kw['options']['ftol'],maxiter=kw['options']['maxiter'],has_constraint_jacobian='jac' in kw['constraints'][0]))
 return SimpleNamespace(success=True,status=0,x=actual-q,nit=old['iterations'])
module.minimize=solved_but_insufficient
try:rejected=candidate(**kwargs,analytic_first=True)
finally:module.minimize=original_minimize
assert len(calls)==1 and calls[0]==dict(ftol=1e-11,maxiter=300,has_constraint_jacobian=True)
assert not rejected['override'] and rejected['reason']=='final_stationarity_violation' and 'command' not in rejected
assert rejected['emitted_stationarity']['residual']>1e-6 and rejected['emitted_stationarity']['threshold']==1e-6
np.testing.assert_array_equal(rejected['rejected_command'],actual)
# Enabled but outside original phase/selection must never demand absent geometry.
guards=[]
for args in [dict(enabled=False),dict(enabled=True,mode='top_lift',selected=True),dict(enabled=True,mode='top_push',selected=False)]:
 a=candidate(**args,analytic_first=True);b=original(**args);assert a==b;guards.append(a['reason'])
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Inject only a successful solver result containing the real failed225 command; observer/physics unchanged.',rejected=rejected,calls=calls,original_guard_parity=guards,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'joint_edge_inward_analytic_first_candidate_v2.py',ep/'raw.npz',ep/'coordination.json',ep/'frontal_bypass.json',ep/'trace.npz',ep/'parcel_orientation.npz']},training_ready=False,installed=False)
with (R/'REAR_BOX_225_STATIONARITY_REJECTION_CHECK_V1.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(rejected=rejected['reason'],stationarity=rejected['emitted_stationarity'],guard_parity=guards)))
