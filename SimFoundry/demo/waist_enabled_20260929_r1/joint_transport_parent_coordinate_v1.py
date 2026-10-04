"""Read-only coordinate view at the verified pre-joint command boundary.
Restore only the then-current waist target for original parent math. Final raw
commands and previous actual actions are never replaced. The enclosing native
stream/ledger must already have independently verified every joint command.
"""
import numpy as np

def parent_coordinate(coordinate,parent,final):
 if coordinate is None:return None
 p,u=np.asarray(parent,float),np.asarray(final,float)
 assert p.shape==u.shape==(11,) and np.isfinite(p).all() and np.isfinite(u).all()
 r=coordinate['joint_transport_clearance'];assert r['step']==coordinate['step'] and type(r['applied']) is bool
 assert np.array_equal(r['parent_command'],p) and np.array_equal(r['output_command'],u)
 key='joint_transport_unexecuted_parent_waist_target_rad'
 if not r['applied']:
  assert key not in coordinate and np.array_equal(p,u)
  return coordinate
 assert r['reason']=='verified_joint_transport_proposal' and r['certificate']['passed'] is True
 assert set(r['paths'])=={'nominal','predicted'} and all(v['passed'] is True for v in r['paths'].values())
 assert coordinate['waist_target_rad']==float(u[0])
 value=coordinate[key];assert isinstance(value,(float,int)) and np.isfinite(value) and abs(value-p[0])<=1e-7
 view=dict(coordinate);view['waist_target_rad']=value
 assert all(view[k] is coordinate[k] for k in coordinate if k!='waist_target_rad')
 return view
