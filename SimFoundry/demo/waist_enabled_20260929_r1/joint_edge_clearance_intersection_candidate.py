"""Isolated final edge-command repair retaining original task and hard limits.
Not installed in a collector. Preserve an already safe edge command exactly.
A failed joint solve returns no command; callers must stop, never emit the rejected
edge command or use an unverified fallback. Nominal geometry, not dynamic proof.
"""
import numpy as np
from scipy.optimize import minimize,Bounds

def repair(*,guard,current,previous,command,context=None):
 q,prev,old=(np.asarray(v,dtype=float) for v in [current,previous,command])
 if any(v.shape!=(11,) or not np.isfinite(v).all() for v in [q,prev,old]):raise ValueError('Invalid finite11D input')
 checked=guard.command(old,q,prev)
 if checked['accepted']:return old.copy(),dict(changed=False,reason='original_final_guard_passed',original_guard=checked)
 if not all(v for k,v in checked['checks'].items() if k!='nominal_margin'):
  return None,dict(changed=False,reason='non_clearance_guard_failure',original_guard=checked)
 if context is None:return None,dict(changed=False,reason='missing_original_edge_context',original_guard=checked)
 J=np.asarray(context['jacobian'],float);e=np.asarray(context['error'],float);d=np.asarray(context['damping'],float);normals=np.asarray(context['normals'],float);direction=context['direction'];inward=context['inward_m'];point=context['point_and_jacobian'];parent=np.asarray(context['parent'],float)
 if J.shape!=(9,11) or e.shape!=(9,) or d.shape!=(11,) or normals.shape not in [(1,3),(2,3)] or parent.shape!=(11,) or not all(np.isfinite(v).all() for v in [J,e,d,normals,parent]) or (d<=0).any():raise ValueError('Invalid original edge inputs')
 if direction not in [-1,1] or inward!=(.0005 if direction==-1 else 0.):raise ValueError('Original edge requirement must be retained')
 if not callable(point):raise ValueError('Missing original reference geometry')
 lo=np.maximum.reduce([guard.lower,q-guard.limits,prev-.055]);hi=np.minimum.reduce([guard.upper,q+guard.limits,prev+.055])
 if (lo>=hi).any():return None,dict(changed=False,reason='empty_original_bounds',original_guard=checked)
 origin,_=point(q)
 def objective(x):
  dq=x-q;v=J@dq-e;return 5000*float(v@v+sum((d*dq)**2)),10000*(J.T@v+d*d*dq)
 def edges(x):
  p,j=point(x);motion=p-origin;return np.r_[normals@motion-inward,direction*motion[1]],np.vstack([normals@j,direction*j[1]])
 def constraints(x):
  ev,ej=edges(x);return np.r_[ev,guard.geometry.constraints(x)-.005],np.vstack([ej,guard.geometry.jacobian(x)])
 attempts=[]
 for name,seed in [('rejected_edge',old),('safe_parent',parent)]:
  fit=minimize(objective,np.clip(seed,lo,hi),jac=True,bounds=Bounds(lo,hi),constraints=[dict(type='ineq',fun=lambda x:constraints(x)[0],jac=lambda x:constraints(x)[1])],method='SLSQP',options=dict(maxiter=300,ftol=1e-11));x=fit.x.astype(np.float32).astype(float);safe=guard.command(x,q,prev);ev,_=edges(x)
  accepted=bool(fit.success and safe['accepted'] and min(ev)>=-1e-7)
  attempts.append(dict(seed=name,status=int(fit.status),iterations=int(fit.nit),solver_success=bool(fit.success),candidate_q=x.tolist(),original_final_guard=safe,edge_residual_m=ev.tolist(),accepted=accepted))
  if accepted:return x,dict(changed=True,reason='joint_edge_and_clearance',original_guard=checked,attempts=attempts)
 return None,dict(changed=False,reason='joint_constraints_not_verified',original_guard=checked,attempts=attempts)
