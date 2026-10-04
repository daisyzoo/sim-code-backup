"""Independent selected rear-inward record check, original thresholds unchanged.
The caller binds current/previous/emitted history, task inputs, actual COP and
point geometry independently. This module is neither lifecycle nor source audit.
No candidate optimizer or candidate certificate code is imported.
"""
import copy
import numpy as np
from scipy.optimize import nnls
from audit_box_inward_refinement import verify_refinement as original_verify,normalized_trace

def verify(trace,parent,actual,previous,q,J,error,damping,lower,upper,limits,point_and_jacobian,rotation,local,core,direction,active,*,enabled):
 if type(enabled) is not bool:raise ValueError('Explicit candidate configuration required')
 args=(trace,parent,actual,previous,q,J,error,damping,lower,upper,limits,point_and_jacobian,rotation,local,core,direction,active)
 if not enabled:
  assert 'analytic_first' not in trace and 'emitted_stationarity' not in trace
  return original_verify(*args,inward_enabled=True)
 assert direction==-1 and active==[3,4,5]
 if 'analytic_first' not in trace:
  assert 'emitted_stationarity' not in trace and trace['reason']!='final_stationarity_violation'
  return original_verify(*args,inward_enabled=True)
 assert trace['analytic_first']==dict(enabled=True,original_objective_and_constraints=True)
 rejection=trace['reason']=='final_stationarity_violation'
 if not rejection:
  original=original_verify(*args,inward_enabled=True)
  if not trace['override']:
   assert 'emitted_stationarity' not in trace
   return original
  evaluated=np.asarray(actual,float)
 else:
  assert trace['override'] is False and 'command' not in trace
  assert trace['solver_success'] is True and type(trace['solver_status']) is int and trace['solver_status']==0
  assert type(trace['solver_iterations']) is int and 0<trace['solver_iterations']<=300
  np.testing.assert_array_equal(actual,parent);np.testing.assert_array_equal(trace['final_upper_command'],parent);np.testing.assert_array_equal(trace['parent_final_upper_command'],parent);np.testing.assert_array_equal(trace['previous_upper_command'],previous)
  evaluated=np.asarray(trace['rejected_command'],float);assert evaluated.shape==(11,) and np.isfinite(evaluated).all();np.testing.assert_array_equal(evaluated,evaluated.astype(np.float32))
  original=dict(refined=False,reason=trace['reason'])
 tr=normalized_trace(trace,True);axes=[i for i in (0,1) if core[i]/2-abs(local[i])<=.01];assert axes==trace['threatened_axes'];normals=np.array([-np.sign(local[i])*rotation[:,i] for i in axes]);origin,_=point_and_jacobian(q)
 base,_=point_and_jacobian(parent);base_values=np.r_[normals@(base-origin)-.0005,-(base-origin)[1]];assert min(base_values)<-1e-7;np.testing.assert_allclose(base_values[:-1],tr['parent_nominal_edge_inward_m'],rtol=0,atol=2e-10);np.testing.assert_allclose(base_values[-1],tr['parent_nominal_forward_m'],rtol=0,atol=2e-10)
 low=np.maximum.reduce([lower-q,-limits,previous-.055-q]);high=np.minimum.reduce([upper-q,limits,previous+.055-q]);delta=evaluated-q;assert min(delta-low)>=-2e-7 and min(high-delta)>=-2e-7
 point,jac=point_and_jacobian(evaluated);motion=point-origin;values=np.r_[normals@motion-.0005,-motion[1]];assert min(values)>=-1e-7;G=np.vstack([normals@jac,-jac[1]]);grad=J.T@(J@delta-error)+damping*damping*delta
 active_grad=[G[i] for i in range(len(values)) if values[i]<=1e-6]
 for i in range(11):
  if delta[i]-low[i]<=2e-6:active_grad.append(np.eye(11)[i])
  if high[i]-delta[i]<=2e-6:active_grad.append(-np.eye(11)[i])
 if active_grad:
  A=np.array(active_grad);norm=np.linalg.norm(A,axis=1);A=A[norm>1e-12]/norm[norm>1e-12,None];_,res=nnls(A.T,grad,maxiter=1000)
 else:res=float(np.linalg.norm(grad))
 saved=trace['emitted_stationarity'];assert saved['threshold']==1e-6 and saved['constraint_active_tolerance']==1e-6 and saved['bound_active_tolerance']==2e-6
 assert np.isfinite(saved['residual']) and abs(saved['residual']-res)<=2e-9
 if rejection:assert res>1e-6 and saved['accepted'] is False and saved['residual']>1e-6
 else:assert res<=1e-6 and saved['accepted'] is True and saved['residual']<=1e-6
 return dict(original,independent_stationarity=float(res),stationarity_rejection_verified=rejection)
