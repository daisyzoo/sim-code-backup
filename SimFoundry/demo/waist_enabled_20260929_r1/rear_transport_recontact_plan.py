"""Default-off nominal transport qualification for an original recontact plan."""
from recontact_plan import plan as parent_plan
from rear_recontact_transport_witness import filter_plan


def plan(scene,q,*,require_rear_transport=False,**kwargs):
    if type(require_rear_transport) is not bool:raise ValueError('Invalid rear transport flag')
    original=parent_plan(scene,q,**kwargs)
    return filter_plan(scene,q,kwargs['step'],original,enabled=require_rear_transport)
