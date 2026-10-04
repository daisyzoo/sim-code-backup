"""UNWIRED bounded support cache with original-projection boundary fallback.
Domain and absolute error derivation: SUPPORT_ERROR_BOUND.md. All source vertices
remain in support extrema. Original2e-7 tolerance, radii, depth/node limits and
joint bounds remain unchanged. No physics or production admission.
"""
import numpy as np
from scipy.spatial.transform import Rotation
from support_cache_probe import CachedSupportAudit
from audit_front_recontact_center_events import RecoveryEventAudit
from joint_transport_paths import JointTransportPaths as OriginalPaths
ERROR_M=1e-10
TOL=2e-7
class BoundedSupportAudit(CachedSupportAudit):
 def __init__(self,root,stage):
  super().__init__(root,stage);self.cached_calls=0;self.full_projection_calls=0
  self.static_domain=all(np.isfinite(self.hand.vertices[s]).all() and np.max(abs(self.hand.vertices[s]))<=2 and np.isfinite(self.axes[s]).all() and np.max(abs(self.axes[s]))<=1.000000000001 for s in ['left','right'])
 def gap(self,side,pose,position,quat,size):
  R=pose[:3,:3];t=pose[:3,3];pos=np.asarray(position);half=np.asarray(size)/2;boxR=Rotation.from_quat(quat).as_matrix()
  finite=all(np.isfinite(x).all() for x in [R,t,pos,half,boxR])
  if not finite:raise ValueError('Nonfinite cached support geometry')
  valid=self.static_domain and np.max(abs(R))<=1.000000000001 and np.max(abs(boxR))<=1.000000000001 and np.max(abs(t))<=10 and np.max(abs(pos))<=10 and np.max(abs(half))<=2 and np.min(half)>=0 and np.max(abs(R.T@R-np.eye(3)))<=1e-12
  if not valid:
   self.full_projection_calls+=1;return RecoveryEventAudit.gap(self,side,pose,position,quat,size)
  self.cached_calls+=1;return super().gap(side,pose,position,quat,size)
class BoundedSupportPaths(OriginalPaths):
 def __init__(self,root,stage):
  super().__init__(root,stage);self.original=OriginalPaths(root,stage);self.audit=BoundedSupportAudit(root,stage);self.error=np.array([0.,ERROR_M,ERROR_M,ERROR_M,0.,0.])
 def decide(self,q,scene,offset):
  m=self.margins(q,scene);bound=m-offset
  if not np.isfinite(m).all():raise ValueError('Nonfinite cached margins')
  if min(bound-self.error)>=-TOL:return True,m,bound-self.error,False
  if min(bound+self.error)<-TOL:return False,m,bound-self.error,False
  exact=self.original.margins(q,scene);self.boundary_fallbacks+=1
  return bool(min(exact-offset)>=-TOL),exact,exact-offset,True
 def certify(self,q,end,scene):
  q=np.asarray(q,float);end=np.asarray(end,float);self.boundary_fallbacks=0
  if any(z.shape!=(11,) or not np.isfinite(z).all() for z in [q,end]):raise ValueError('finite11 required')
  lower=self.audit.lo.copy();upper=self.audit.hi.copy();lower[0]=-.98;upper[0]=.98
  if any(np.any(z<lower-TOL) or np.any(z>upper+TOL) for z in [q,end]):return dict(passed=False,reason='endpoint_joint_bounds')
  for alpha,z in [(0.,q),(1.,end)]:
   accepted,m,bound,exact=self.decide(z,scene,np.zeros(6))
   if not accepted:return dict(passed=False,reason='endpoint_geometry',alpha=alpha,margins_m=dict(zip(self.labels,m.tolist())),cached_error_bound_m=ERROR_M,boundary_full_projection=exact)
  active=scene['side'];inactive='right' if active=='left' else 'left';d=abs(end-q)
  v=np.array([self.hand_radii[inactive]@d]*3+[self.hand_radii[active]@d,self.elbow_radii['left']@d,self.elbow_radii['right']@d])
  todo=[(0.,1.,0)];leaves=[];nodes=0;deepest=0
  while todo:
   lo,hi,depth=todo.pop();mid=(lo+hi)/2;z=q+(end-q)*mid;accepted,m,bound,exact=self.decide(z,scene,v*(hi-lo)/2);nodes+=1;deepest=max(deepest,depth)
   if accepted:
    leaves.append(dict(interval=[lo,hi],lower_bounds_m=bound.tolist()));continue
   midpoint_ok,measured,_,_=self.decide(z,scene,np.zeros(6)) if not exact else (bool(min(m)>=-TOL),m,None,True)
   if not midpoint_ok or depth>=24 or nodes>=20000:
    return dict(passed=False,reason='violated_or_subdivision_limit',interval=[lo,hi],depth=depth,nodes=nodes,midpoint_margins_m=measured.tolist(),lower_bounds_m=bound.tolist(),cached_error_bound_m=ERROR_M,boundary_fallbacks=self.boundary_fallbacks)
   todo.extend([(mid,hi,depth+1),(lo,mid,depth+1)])
  return dict(passed=True,nodes=nodes,max_depth=deepest,vertex_travel_bounds_m=dict(zip(self.labels,v.tolist())),minimum_certified_margin_m=min(min(z['lower_bounds_m']) for z in leaves),leaves=leaves,cached_error_bound_m=ERROR_M,boundary_fallbacks=self.boundary_fallbacks,scope='Conservative cached gaps with exact-original fallback at uncertain decisions; original continuous static paths only, not dynamics')
