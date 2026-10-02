"""Original planner plus explicitly selected unchanged directional qualification."""
import numpy as np
from recontact_plan import plan as parent_plan
from rear_transport_feasible_retry_candidate import witness

def qualify(scene,current,step,parent_plan,*,required=False,retry=False):
    if type(required) is not bool or type(retry) is not bool:raise ValueError('Explicit transport flags required')
    if not required:return parent_plan
    if type(parent_plan.get('accepted')) is not bool:raise ValueError('Invalid parent plan')
    if not parent_plan['accepted']:return parent_plan
    if parent_plan['step']!=step or parent_plan['scene']!=scene.record() or not np.array_equal(parent_plan['start'],np.asarray(current,float)):raise ValueError('Parent plan must match current observation')
    result=witness(scene,parent_plan['endpoint'],retry_feasible=retry)
    if not result['accepted']:return dict(accepted=False,reason='rear_transport_endpoint_unverified',step=step,start=list(current),scene=scene.record(),parent_plan=parent_plan,rear_transport_witness=result)
    return dict(parent_plan,rear_transport_witness=result)

def plan(scene,q,*,require_rear_transport=False,transport_feasible_retry=False,**kwargs):
    if type(require_rear_transport) is not bool or type(transport_feasible_retry) is not bool:raise ValueError('Explicit transport flags required')
    original=parent_plan(scene,q,**kwargs)
    return qualify(scene,q,kwargs['step'],original,required=require_rear_transport,retry=transport_feasible_retry)
