"""Read-only parent task view after verified transport and final-normal ledgers.
Only logged unexecuted waist targets are restored, in reverse override order.
Current q, previous actual command, task, contact, geometry and raw stay intact.
Requires independently verified full native command ledger at the file caller.
"""
import numpy as np
from joint_transport_parent_coordinate_v1 import parent_coordinate as transport_parent_coordinate

def parent_coordinate(coordinate,parent,final,*,normal_enabled):
 assert type(normal_enabled) is bool
 if coordinate is None:return None
 if not normal_enabled:
  assert 'front_normal_nondegradation' not in coordinate
  assert 'normal_planning_unexecuted_parent_waist_target_rad' not in coordinate
  return transport_parent_coordinate(coordinate,parent,final)
 r=coordinate['front_normal_nondegradation'];tr=coordinate['joint_transport_clearance']
 assert type(r['step']) is int and r['step']==coordinate['step']==tr['step']
 assert r['enabled'] is True and type(r['applied']) is bool and r['requires_stop'] is False and r['training_ready'] is False
 u=np.asarray(final,float);mid=np.asarray(tr['output_command'],float)
 for a in [u,mid]:assert a.shape==(11,) and np.isfinite(a).all() and np.array_equal(a,a.astype(np.float32))
 assert np.array_equal(r['output_command'],u) and np.array_equal(r['parent_command'],mid)
 key='normal_planning_unexecuted_parent_waist_target_rad';view=coordinate
 if r['applied']:
  assert r['reason'] in ['verified_exact_normal_nondegrading_command','verified_hold_then_original_recontact']
  assert coordinate['waist_target_rad']==float(u[0])
  value=coordinate[key];assert type(value) in (float,int) and np.isfinite(value) and abs(value-mid[0])<=1e-7
  view=dict(coordinate);view['waist_target_rad']=value
 else:assert key not in coordinate and np.array_equal(u,mid)
 result=transport_parent_coordinate(view,parent,mid)
 assert all(result[k] is coordinate[k] for k in coordinate if k!='waist_target_rad')
 return result
