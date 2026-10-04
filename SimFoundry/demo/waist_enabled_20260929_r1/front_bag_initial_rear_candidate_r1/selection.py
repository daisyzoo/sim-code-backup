"""Initial-only mailer rear-route preference; unintegrated prospective candidate.
It chooses an existing object-envelope route, never commands a robot or parcel.
A positive decision proves neither robot feasibility nor physical task success.
"""
from simfoundry.data.tabletop_route_candidates import tabletop_route_candidates

def select_initial_route(*,enabled=False,episode_step,side,front_selected,
                         rear_required,target,obstacle,target_size,obstacle_size,
                         target_quat,obstacle_quat):
    if any(type(x) is not bool for x in [enabled,front_selected,rear_required]):
        raise TypeError('Selection flags must be bool')
    if type(episode_step) is not int or episode_step!=0:
        raise ValueError('Initial-only selection cannot clear or override a later guard')
    if side not in ('left','right'):
        raise ValueError('Unknown active side')
    result=dict(front_route_selected=front_selected,override=False,
                reason='original_initial_route',training_ready=False,
                physical_feasibility_proved=False)
    if not enabled or side!='left' or not front_selected or not rear_required:
        return result
    report=tabletop_route_candidates(target,obstacle,target_size,obstacle_size,
                                    target_quat,obstacle_quat,1,margin=.020)
    rear=next(x for x in report['candidates'] if x['route']=='rear')
    result['rear_object_envelope']=rear
    if not rear['object_envelope_eligible'] or rear['target_table_margin_m']<.005:
        result['reason']='rear_initial_object_envelope_rejected'
        return result
    result.update(front_route_selected=False,override=True,
                  reason='prefer_existing_rear_route_for_initial_front_mailer')
    return result
