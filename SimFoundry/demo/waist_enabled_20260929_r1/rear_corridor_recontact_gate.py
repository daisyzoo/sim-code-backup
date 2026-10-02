"""Do not resume descent/press/push before a pending measured recontact handover.
Original safety withdrawal/release and verified unloaded path commands retain
priority. This gate is applied before logging or emitting the lifecycle result.
"""

def guard_pending(*,enabled=False,state,event,parent_mode):
    if type(enabled) is not bool:raise ValueError('Explicit boolean gate required')
    if not enabled or not getattr(state,'rear_corridor_recontact_pending',False):return event
    if event['kind']=='stop':return event
    if event['kind'] in ('command','handover'):
        if parent_mode not in ('top_cross','top_descend'):
            raise ValueError('Verified recontact event in incompatible parent mode')
        return event
    if event['kind']!='unchanged':raise ValueError('Unknown recontact event kind')
    if parent_mode in ('top_descend','top_press','top_push'):
        return dict(kind='stop',requires_stop=True,reason='rear_corridor_handover_not_measured',
                    original_event=event,parent_mode=parent_mode,
                    scope='Required unloaded direction-checked recontact has not handed over; no old descent/push fallback')
    return event
