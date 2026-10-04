"""Bilateral inactive-five version; active side is taken from the verified scene.
Continuous static inactive-hand segment certificate, no dynamic guarantee."""
import numpy as np

def certify(q,end,scene,*,model,audit):
 q=np.asarray(q,float);end=np.asarray(end,float);radius=np.zeros(11);inactive='right' if scene['side']=='left' else 'left';chain=model.chains[inactive];extent=np.linalg.norm(audit.hand.vertices[inactive],axis=1).max()
 for k,(name,_,axis) in enumerate(chain):
  if name in model.names:
   if axis is None or abs(np.linalg.norm(axis)-1)>1e-9:raise ValueError('Invalid revolute axis')
   radius[model.names.index(name)]=extent+sum(np.linalg.norm(O[:3,3]) for _,O,_ in chain[k+1:])
 travel=float(radius@abs(end-q));todo=[(0.,1.,0)];leaves=[];samples=[]
 while todo:
  lo,hi,depth=todo.pop();mid=(lo+hi)/2;z=q+(end-q)*mid;pose=audit.hand.fk(z,inactive);height=audit.hand.minz(z,inactive);gaps=[audit.gap(inactive,pose,scene['target_xyz'],scene['target_quat'],scene['core_size']),audit.gap(inactive,pose,scene['other_xyz'],scene['other_quat'],scene['other_size'])];margin=np.r_[height-.84,np.array(gaps)-.01];lower=margin-travel*(hi-lo)/2;samples.append(dict(interval=[lo,hi],minimum_margin_m=float(min(margin)),minimum_lower_bound_m=float(min(lower))))
  if min(lower)>=-2e-7:leaves.append(float(min(lower)));continue
  if min(margin)<-2e-7 or depth>=16:return dict(passed=False,reason='violated_or_subdivision_limit',samples=samples)
  todo.extend([(lo,mid,depth+1),(mid,hi,depth+1)])
 return dict(passed=True,travel_bound_m=travel,minimum_certified_margin_m=min(leaves),samples=samples)
