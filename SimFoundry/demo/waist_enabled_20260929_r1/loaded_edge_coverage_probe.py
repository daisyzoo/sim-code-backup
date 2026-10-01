"""Default-off, unwired loaded-edge command proposal. Never executes an action.
The parent retains mode/terminal/region precedence and true first-loaded pushes.
Eligibility depends on actual consecutive loaded pushes, not whether a preceding
Cartesian reference governor happened to modify its waypoint. Nominal fixed
reference directions do not predict physical COP or certify contact stability.
On an eligible unsafe parent and no verified solution, return accepted=False and
NO command; a future caller must stop, never silently execute that parent.
"""
import numpy as np
from scipy.optimize import minimize,Bounds

def propose(*,enabled=False,selected=False,mode=None,previous_mode=None,
            recontacts=0,previous_recontacts=0,load_n=0.,previous_load_n=0.,
            parent_guard=False,terminal_hold=False,region_override=False,
            unloaded_override=False,current=None,previous_command=None,
            parent_command=None,jacobian=None,error=None,damping=None,
            lower=None,upper=None,step_limits=None,object_rotation=None,
            cop_local=None,core_size=None,direction=None,point_fn=None,
            point_jacobian_fn=None,geometry=None):
    flags=[enabled,selected,parent_guard,terminal_hold,region_override,unloaded_override]
    if any(type(x) is not bool for x in flags):raise ValueError('Flags must be bool')
    skip=lambda reason:dict(eligible=False,accepted=True,override=False,reason=reason)
    if not enabled:return skip('disabled')
    if not selected:return skip('not_selected_rear')
    if parent_guard or terminal_hold or region_override or unloaded_override:return skip('parent_precedence')
    if mode!='top_push':return skip('original_mode_guard')
    if any(type(x) is not int or x<0 for x in [recontacts,previous_recontacts]):raise ValueError('Invalid recontact count')
    if previous_mode!='top_push' or previous_recontacts!=recontacts:return skip('genuine_push_transition')
    if not np.isfinite([load_n,previous_load_n]).all() or min(load_n,previous_load_n)<0:raise ValueError('Invalid observed loads')
    if min(load_n,previous_load_n)<.3 or cop_local is None:return skip('not_consecutive_loaded_push')
    def vec(x,n,name):
        a=np.asarray(x,dtype=float)
        if a.shape!=(n,) or not np.isfinite(a).all():raise ValueError('Invalid '+name)
        return a.copy()
    q=vec(current,11,'q');prev=vec(previous_command,11,'previous command');parent=vec(parent_command,11,'parent')
    lo=vec(lower,11,'lower');hi=vec(upper,11,'upper');limits=vec(step_limits,11,'limits');damp=vec(damping,11,'damping')
    J=np.asarray(jacobian,dtype=float);e=vec(error,9,'error');R=np.asarray(object_rotation,dtype=float);cop=vec(cop_local,3,'COP');size=vec(core_size,3,'core')
    if J.shape!=(9,11) or not np.isfinite(J).all():raise ValueError('Invalid task Jacobian')
    if R.shape!=(3,3) or not np.isfinite(R).all() or not np.allclose(R.T@R,np.eye(3),atol=1e-6) or np.linalg.det(R)<.99999:raise ValueError('Invalid object rotation')
    if direction not in [-1,1] or isinstance(direction,bool):raise ValueError('Invalid direction')
    if (lo>=hi).any() or min(limits)<=0 or min(damp)<=0 or min(size)<=.02:raise ValueError('Invalid bounds')
    if not callable(point_fn) or not callable(point_jacobian_fn) or geometry is None:raise ValueError('Missing geometry')
    axes=[k for k in [0,1] if size[k]/2-abs(cop[k])<=.01]
    if not axes:return skip('no_near_core_edge')
    normals=np.array([-np.sign(cop[k])*R[:,k] for k in axes]);A=np.vstack([normals,[0,direction,0]])
    origin=vec(point_fn(q),3,'measured reference');low=np.maximum.reduce([lo,q-limits,prev-.055]);high=np.minimum.reduce([hi,q+limits,prev+.055]);D=damp*damp
    base=dict(eligible=True,threatened_axes=axes,measured_reference=origin.tolist(),bound_low=low.tolist(),bound_high=high.tolist())
    if (low>=high).any():return dict(base,accepted=False,override=False,reason='empty_original_bounds',command=None)
    def constraint(x):return np.r_[A@(vec(point_fn(x),3,'command reference')-origin),np.asarray(geometry.constraints(x))-.005]
    def cj(x):
        jp=np.asarray(point_jacobian_fn(x),dtype=float)
        if jp.shape!=(3,11) or not np.isfinite(jp).all():raise ValueError('Invalid reference Jacobian')
        return np.vstack([A@jp,geometry.jacobian(x)])
    def cost(x):d=x-q;res=J@d-e;return 5000*float(res@res+np.sum(D*d*d)),10000*(J.T@res+D*d)
    def check(x):
        x=np.asarray(x,dtype=np.float32).astype(float)
        if not np.isfinite(x).all():return False,None
        c=constraint(x);valid=bool(np.min(c[:len(A)])>=-1e-7 and np.min(c[len(A):])>=-2e-7 and np.min(x-low)>=-2e-7 and np.min(high-x)>=-2e-7)
        return valid,dict(command=x.tolist(),nominal_inward_and_forward_m=c[:len(A)].tolist(),elbow_margin_residual_m=c[len(A):].tolist(),cost=cost(x)[0])
    good,parent_check=check(parent)
    base['parent_check']=parent_check
    if good:return dict(base,accepted=True,override=False,reason='parent_already_valid',command=np.asarray(parent,dtype=np.float32).tolist())
    attempts=[]
    for name,seed in [('current',q),('parent',parent),('previous',prev)]:
        fit=minimize(cost,np.clip(seed,low,high),jac=True,bounds=Bounds(low,high),constraints=[dict(type='ineq',fun=constraint,jac=cj)],method='SLSQP',options=dict(maxiter=300,ftol=1e-11))
        valid,details=check(fit.x);attempts.append(dict(seed=name,accepted=bool(fit.success and valid),solver_success=bool(fit.success),status=int(fit.status),iterations=int(fit.nit),final=details))
    successes=[a for a in attempts if a['accepted']]
    if not successes:return dict(base,accepted=False,override=False,reason='no_verified_nominal_edge_command',command=None,attempts=attempts)
    best=min(successes,key=lambda a:a['final']['cost'])
    return dict(base,accepted=True,override=True,reason='consecutive_loaded_nominal_edge_repair',command=best['final']['command'],selected_seed=best['seed'],attempts=attempts,scope=__doc__)
