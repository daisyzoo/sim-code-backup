"""Bounded damped position solve, independent of simulator imports."""
import numpy as np
from scipy.optimize import lsq_linear


def bounded_damped_step(jacobian, error, current, lower, upper, step_limits, damping, preferred_step=None):
    jacobian=np.asarray(jacobian,dtype=float);error=np.asarray(error,dtype=float)
    current,lower,upper,step_limits,damping=[np.asarray(v,dtype=float) for v in (current,lower,upper,step_limits,damping)]
    n=len(current)
    if jacobian.shape!=(len(error),n) or any(v.shape!=(n,) for v in (lower,upper,step_limits,damping)):
        raise ValueError('Inconsistent IK shapes')
    if not all(np.isfinite(v).all() for v in (jacobian,error,current,lower,upper,step_limits,damping)):
        raise ValueError('Nonfinite IK input')
    if (lower>=upper).any() or (step_limits<=0).any() or (damping<=0).any():
        raise ValueError('Invalid IK bounds')
    lo=np.maximum(lower-current,-step_limits);hi=np.minimum(upper-current,step_limits)
    if (lo>=hi).any():
        raise ValueError('Current state too far outside working bounds for one constrained step')
    prior=np.zeros(n) if preferred_step is None else np.asarray(preferred_step,dtype=float)
    if prior.shape!=(n,) or not np.isfinite(prior).all():raise ValueError('Invalid preferred IK step')
    design=np.vstack([jacobian,np.diag(damping)])
    rhs=np.concatenate([error,damping*prior])
    solution=lsq_linear(design,rhs,bounds=(lo,hi),tol=1e-10,max_iter=100)
    if not solution.success or not np.isfinite(solution.x).all():
        raise RuntimeError('Bounded IK failed to converge')
    return solution.x
