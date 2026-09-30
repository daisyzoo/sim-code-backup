"""Unwired two-axis contact attitude constraint; global yaw remains free."""
import numpy as np

def contact_normal_constraint(rotation_world, angular_jacobian_world, target_local_up, weight_m=.15):
    r=np.asarray(rotation_world,dtype=float);j=np.asarray(angular_jacobian_world,dtype=float);target=np.asarray(target_local_up,dtype=float)
    if r.shape!=(3,3) or j.ndim!=2 or j.shape[0]!=3 or target.shape!=(3,):raise ValueError('Invalid normal constraint shape')
    if not all(np.isfinite(x).all() for x in (r,j,target)) or not np.isfinite(weight_m) or not 0<weight_m<=.3:raise ValueError('Nonfinite or invalid normal constraint weight')
    if np.max(abs(r.T@r-np.eye(3)))>1e-5 or abs(np.linalg.det(r)-1)>1e-5 or abs(np.linalg.norm(target)-1)>1e-5:raise ValueError('Rotation and target normal must be normalized')
    current=r.T@np.array([0.,0.,1.])
    skew_up=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,0.]])
    jac=weight_m*r.T@skew_up@j
    error=weight_m*np.clip(.72*(target-current),-.1,.1)
    return dict(jacobian=jac,error=error,current_local_up=current,target_local_up=target,angle_error_rad=float(np.arccos(np.clip(current@target,-1,1))),weight_m=float(weight_m))
