"""Independent KKT for the changed loaded-recovery and initial-unload tasks.
Retains original1e-6 stationarity and all support-vertex elbow certificate.
Equalities use both signed normals (free multiplier); lifted hand height uses
EVERY vertex inequality, avoiding a single-minimum derivative at tied vertices.
"""
import numpy as np
from support_vertex_stationarity import certificate


def verify(verifier, *, row, coordinate, current, previous, command, kind, geometry):
    q,prev,x=[np.asarray(v,float) for v in [current,previous,command]]
    assert all(v.shape==(11,) and np.isfinite(v).all() for v in [q,prev,x])
    assert kind in ['loaded_recovery','unload']
    inp=coordinate['task_inputs'];J=np.asarray(inp['jacobian']);e=np.asarray(inp['error']).copy();d=np.asarray(inp['damping']);assert J.shape==(9,11) and e.shape==(9,) and d.shape==(11,)
    assert np.array_equal(q,inp['current']) and np.array_equal(prev,inp['previous']) and not np.any(inp['preferred_step'])
    side=coordinate['active_side'];i=3 if side=='right' else 0;offset=np.asarray(row['control_offset_local']);T0=verifier.hand.fk(q,side);origin=T0[:3,3]+T0[:3,:3]@offset
    vertices=np.asarray(verifier.vertices[side]);z0=float((vertices@T0[:3,:3].T+T0[:3,3])[:,2].min())
    target=np.asarray(geometry['target_xyz']);other=np.asarray(geometry['obstacle_xyz']);size=np.asarray(geometry['target_size']);osize=np.asarray(geometry['obstacle_size']);R=np.asarray(geometry['target_rotation']);OR=np.asarray(geometry['obstacle_rotation']);core=np.asarray(geometry['core_size'])
    deficit=other[0]+(abs(OR)@osize/2)[0]+(abs(R)@size/2)[0]+.020-target[0];requested=min(.002,max(.001,float(deficit)));assert deficit>0
    cop=R.T@(np.asarray(row['rear_cop_centering']['cop_world'])-target);axes=[k for k in [0,1] if core[k]/2-abs(cop[k])<=.01];normals=np.array([-np.sign(cop[k])*R[:,k] for k in axes]).reshape(-1,3);inward=.0005 if side=='right' else 0.
    if kind=='loaded_recovery':e[i]=.72*requested;e[i+1]=0.
    else:e[i:i+3]=[0.,0.,.72*.003]
    def extra(y):
        T=verifier.hand.fk(y,side);delta=T[:3,3]+T[:3,:3]@offset-origin
        if kind=='loaded_recovery':return np.r_[normals@delta-inward,delta[0]-.0001,requested-delta[0],delta[1],-delta[1]]
        height=(vertices@T[:3,:3].T+T[:3,3])[:,2]
        return np.r_[delta[2]-.0005,.003-delta[2],height-z0-.0005,delta[:2],-delta[:2]]
    values=extra(x);h=2e-7;G=np.column_stack([(extra(x+np.eye(11)[j]*h)-extra(x-np.eye(11)[j]*h))/(2*h) for j in range(11)])
    gradient=J.T@(J@(x-q)-e)+d*d*(x-q)
    lower=np.maximum.reduce([verifier.lower,q-verifier.steps,prev-.055]);upper=np.minimum.reduce([verifier.upper,q+verifier.steps,prev+.055])
    result=certificate(geometry=verifier.elbows,x=x,gradient=gradient,lower=lower,upper=upper,extra_values=values,extra_jacobian=G)
    result.update(kind=kind,scope=__doc__,equality_tolerance_m=1e-7,stationarity_threshold=1e-6,finite_difference_step_rad=h,objective_gradient=gradient.tolist(),independent_task_error=e.tolist(),training_ready=False)
    return result
