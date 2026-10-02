"""Independent unchanged objective/KKT with explicit inward constraint offset. No candidate optimizer imported."""
import numpy as np
from scipy.optimize import linprog,nnls
from audit_box_entry_pose_loaded_execution import near

def verify_refinement(trace,parent,actual,previous,q,J,error,damping,lower,upper,limits,point_and_jacobian,rotation,local,core,direction,active,inward_step_m=0.):
 assert type(trace['override']) is bool
 near(trace['parent_final_upper_command'],parent,0);near(trace['final_upper_command'],actual,0);near(trace['previous_upper_command'],previous,0)
 axes=[k for k in [0,1] if core[k]/2-abs(local[k])<=.01];assert axes
 normals=np.asarray([-np.sign(local[k])*rotation[:,k] for k in axes]);p0,_=point_and_jacobian(q)
 def directions(command):
  point,jac=point_and_jacobian(command);motion=point-p0
  return np.r_[normals@motion-inward_step_m,direction*motion[1]],np.vstack([normals@jac,direction*jac[1]])
 pd,_=directions(parent);assert trace['threatened_axes']==axes;near(trace['parent_nominal_edge_inward_m'],pd[:-1],2e-10);near(trace['parent_nominal_forward_m'],pd[-1],2e-10)
 low=np.maximum.reduce([lower-q,-limits,previous.astype(float)-.055-q]);high=np.minimum.reduce([upper-q,limits,previous.astype(float)+.055-q])
 if pd.min()>=-1e-7:
  assert trace['override'] is False and trace['reason']=='parent_direction_valid';near(actual,parent,0);return dict(refined=False,reason=trace['reason'])
 if not trace['override']:
  near(actual,parent,0);reason=trace['reason']
  if reason=='empty_original_bound_intersection':assert (low>=high).any()
  elif reason=='linear_initialization_infeasible':
   A=np.vstack([normals@J[active],direction*J[active][1]]);check=linprog(np.zeros(11),A_ub=-A,b_ub=-np.r_[np.full(len(normals),inward_step_m),0.],bounds=list(zip(low,high)),method='highs');assert check.status==2
  elif reason in ['linear_initialization_failed','nonlinear_solver_failed']:assert type(trace['solver_status']) is int and trace['solver_status']!=0
  elif reason in ['final_float32_constraint_violation','nonfinite_output']:pass
  else:raise AssertionError(('unknown fallback',reason))
  return dict(refined=False,reason=reason,numeric_fallback=reason not in ['empty_original_bound_intersection','linear_initialization_infeasible'])
 assert trace['reason']=='nonlinear_joint_direction' and type(trace['iterations']) is int and 0<trace['iterations']<=300;near(trace['command'],actual,0)
 dq=actual.astype(float)-q;assert np.min(dq-low)>=-2e-7 and np.min(high-dq)>=-2e-7
 d,G=directions(actual);assert d.min()>=-1e-7;near(trace['nominal_edge_inward_m'],d[:-1],2e-10);near(trace['nominal_forward_m'],d[-1],2e-10)
 # Independent first-order stationarity check with analytic URDF Jacobian.
 # Candidate uses finite-difference SLSQP; no candidate optimizer is executed here.
 grad=J.T@(J@dq-error)+damping*damping*dq
 active_grad=[G[i] for i in range(len(d)) if d[i]<=1e-6]
 for i in range(11):
  if dq[i]-low[i]<=2e-6:active_grad.append(np.eye(11)[i])
  if high[i]-dq[i]<=2e-6:active_grad.append(-np.eye(11)[i])
 if active_grad:
  normals_kkt=np.asarray(active_grad);length=np.linalg.norm(normals_kkt,axis=1);normals_kkt=normals_kkt[length>1e-12]/length[length>1e-12,None];_,res=nnls(normals_kkt.T,grad,maxiter=1000)
 else:res=float(np.linalg.norm(grad))
 assert res<=1e-6,('stationarity',res)
 return dict(refined=True,reason=trace['reason'],nominal_min_edge_inward_m=float(min(d[:-1])),nominal_forward_m=float(d[-1]),stationarity_residual=float(res))
