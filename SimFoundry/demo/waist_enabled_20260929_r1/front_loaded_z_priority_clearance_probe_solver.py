"""Unwired nominal loaded-Z optimization for offline diagnosis only.
Preserve the archived objective and bounds; enforce its Z task equality, no
increase of linear or exact hand-attitude residual, and original elbow5mm.
Scale variables by existing step limits. Analytic URDF orientation derivatives
avoid noisy finite differences. Solver termination is reported, not treated as
an independent feasibility/stationarity certificate. No dynamics/force claim.
"""
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import minimize,Bounds

def up_and_jacobian(model,q,side):
 M=model.base.copy();axes=[]
 for O,axis,i in model.chains[side]:
  M=M@O
  if axis is not None:
   if i is not None:axes.append((i,M[:3,:3]@axis))
   A=np.eye(4);A[:3,:3]=Rotation.from_rotvec(axis*(q[i] if i is not None else 0.)).as_matrix();M=M@A
 up=M[:3,:3].T@np.array([0.,0.,1.]);J=np.zeros((3,11))
 for i,axis in axes:J[:,i]=M[:3,:3].T@np.cross([0.,0.,1.],axis)
 return up,J

def solve(a,*,parent,side,target_up,hand,elbows):
 q=np.asarray(a['current']);prev=np.asarray(a['previous']);J=np.asarray(a['jacobian']);e=np.asarray(a['error']);dam=np.asarray(a['damping']);prior=np.asarray(a['preferred_step']);scale=np.asarray(a['step_limits']);parent=np.asarray(parent);d0=parent-q
 low=np.maximum.reduce([a['lower'],q-scale,prev-.055]);high=np.minimum.reduce([a['upper'],q+scale,prev+.055]);zrow=5 if side=='right' else 2;A=J[6:];v=e[6:];target=np.array(target_up,dtype=float);target/=np.linalg.norm(target)
 assert len(A)==3 and np.all(parent>=low-2e-7) and np.all(parent<=high+2e-7)
 oldlin=float(np.linalg.norm(A@d0-v));oldup,_=up_and_jacobian(hand,parent,side);oldexact=float(np.sum((oldup-target)**2))
 def unpack(y):return d0+scale*y
 def cost(y):
  d=unpack(y);err=J@d-e;reg=d-prior
  return float(1e6*(err@err+np.sum(dam*dam*reg*reg))),2e6*(J.T@err+dam*dam*reg)*scale
 def normal(y):
  up,G=up_and_jacobian(hand,q+unpack(y),side);diff=up-target
  return (oldexact-diff@diff)*1e6,(-2*diff@G)*scale*1e6
 constraints=[dict(type='eq',fun=lambda y:float((J[zrow]@unpack(y)-e[zrow])*1000),jac=lambda y:J[zrow]*scale*1000),dict(type='ineq',fun=lambda y:float((oldlin**2-np.sum((A@unpack(y)-v)**2))*1e6),jac=lambda y:-2*(A.T@(A@unpack(y)-v))*scale*1e6),dict(type='ineq',fun=lambda y:normal(y)[0],jac=lambda y:normal(y)[1]),dict(type='ineq',fun=lambda y:(elbows.gap(q+unpack(y))-.005)*1000,jac=lambda y:elbows.gradient(q+unpack(y))*scale[None,:]*1000)]
 result=minimize(cost,np.zeros(11),jac=True,bounds=Bounds((low-parent)/scale,(high-parent)/scale),constraints=constraints,method='SLSQP',options=dict(maxiter=150,ftol=1e-13))
 x=(q+unpack(result.x)).astype(np.float32).astype(float)
 return x,dict(solver_success=bool(result.success),solver_status=int(result.status),solver_message=str(result.message),iterations=int(result.nit),parent_command=parent.tolist(),candidate_command=x.tolist(),original_linear_attitude_residual=oldlin,original_exact_attitude_chord_squared=oldexact)
