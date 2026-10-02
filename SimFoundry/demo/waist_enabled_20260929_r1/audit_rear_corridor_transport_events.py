"""Original complete recovery event audit plus independent direction witnesses.
Only already verified additional witness fields are removed from the input passed
to the unchanged parent audit; all original plans, path events and bounds remain.
The caller must derive require_rear_transport from the verified pending timeline.
"""
import copy
from audit_closed_peak_trial_lift_events import EventAudit as ParentAudit
from audit_rear_transport_witness import EventAudit as GeometryAudit,verify_witness


class EventAudit(ParentAudit):
    def __init__(self,repo,stage):
        super().__init__(repo,stage)
        self.transport_geometry=GeometryAudit(repo,stage)

    def verify(self,event,*,require_rear_transport=False,**inputs):
        if type(require_rear_transport) is not bool:raise ValueError('Explicit pending recovery flag required')
        cleaned=copy.deepcopy(event);proof={};plan=cleaned.get('planning')
        landing=plan is not None and not cleaned.get('entry_lift_phase')
        if landing:
            witness=plan.pop('rear_transport_witness',None)
            if require_rear_transport:
                assert witness is not None and plan['accepted'] is True
                proof['planned_transport']=verify_witness(self.transport_geometry,witness,endpoint=plan['endpoint'],scene=inputs['scene'])
            else:assert witness is None,'Unexpected direction requirement on original recovery'
        measured=cleaned.pop('rear_transport_handover_witness',None)
        if event['kind']=='handover' and require_rear_transport:
            assert measured is not None and inputs['observed_load_n']==0. and 0.<=inputs['filtered_load_n']<=.05
            proof['measured_transport']=verify_witness(self.transport_geometry,measured,endpoint=inputs['current'],scene=inputs['scene'])
        else:assert measured is None
        result=super().verify(cleaned,**inputs)
        if require_rear_transport:result=dict(result,requires_transport=True,independent_transport=proof)
        return result
