"""Bounded smooth perturbations of frozen expert trajectories; no object control."""
import numpy as np

MIRROR=np.array([1.,-1.,-1.,1.,-1.])

def residual_actions(template,task_ids,parameters,lower,upper):
    base=np.asarray(template,dtype=np.float32);tasks=np.asarray(task_ids);params=np.asarray(parameters,dtype=float)
    if base.shape!=(160,len(tasks),23) or params.shape!=(4,5):raise ValueError('Invalid residual/template shape')
    if not np.isfinite(base).all() or not np.isfinite(params).all() or np.abs(params).max()>.250000001:raise ValueError('Invalid or excessive residual')
    if np.any((tasks!=0)&(tasks!=1)):raise ValueError('Only paired push tasks supported')
    if np.abs(base[0,:,12:]).max()>=1e-4 or np.any(base[:,:,12]!=0) or np.abs(np.diff(base,axis=0)).max()>.055001:raise ValueError('Template violates expert constraints')
    lo=np.asarray(lower);hi=np.asarray(upper)
    if np.any(base<lo-1e-6) or np.any(base>hi+1e-6):raise ValueError('Template outside joint limits')
    if not np.any(params):return base.copy()
    knots=np.concatenate([np.zeros((1,5)),params,params[-1:]],axis=0);times=np.array([56,80,100,120,140,159]);out=base.copy()
    for t in range(56,160):
        segment=min(int(np.searchsorted(times,t,side='right'))-1,4);s=(t-times[segment])/(times[segment+1]-times[segment]);s=s*s*(3-2*s)
        delta=knots[segment]*(1-s)+knots[segment+1]*s
        for i,task in enumerate(tasks):
            start=18 if task==0 else 13;change=delta*MIRROR if task==0 else delta
            target=np.clip(base[t,i,start:start+5]+change,lo[start:start+5],hi[start:start+5])
            out[t,i,start:start+5]=np.clip(target,out[t-1,i,start:start+5]-.055,out[t-1,i,start:start+5]+.055)
    if np.abs(np.diff(out,axis=0)).max()>.055001 or np.abs(out-base).max()>.250002:raise ValueError('Generated action violates slew/residual bounds')
    assert np.array_equal(out[:56],base[:56]) and np.array_equal(out[:,:,:13],base[:,:,:13])
    for i,task in enumerate(tasks):
        inactive=slice(13,18) if task==0 else slice(18,23)
        assert np.array_equal(out[:,i,inactive],base[:,i,inactive])
    return out
