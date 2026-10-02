"""Verify additional retry metadata before original complete event mathematics."""
import copy
from audit_rear_tracking_transport_events_v2 import EventAudit as ParentAudit
from audit_rear_transport_retry_witness import verify_retry_witness

class EventAudit(ParentAudit):
    def verify(self,event,*,require_rear_transport=False,transport_feasible_retry=False,**inputs):
        assert type(transport_feasible_retry) is bool
        cleaned=copy.deepcopy(event);proof={};plan=cleaned.get('planning')
        if plan is not None and not cleaned.get('entry_lift_phase'):
            witness=plan.get('rear_transport_witness')
            if require_rear_transport:
                assert witness is not None
                proof['planning']=verify_retry_witness(self.transport_geometry,witness,endpoint=plan['endpoint'],scene=inputs['scene'],retry_enabled=transport_feasible_retry)
                witness.pop('feasible_endpoint_retry',None)
        measured=cleaned.get('rear_transport_handover_witness')
        if event['kind']=='handover' and require_rear_transport:
            assert measured is not None
            proof['measured']=verify_retry_witness(self.transport_geometry,measured,endpoint=inputs['current'],scene=inputs['scene'],retry_enabled=transport_feasible_retry)
            measured.pop('feasible_endpoint_retry',None)
        result=super().verify(cleaned,require_rear_transport=require_rear_transport,**inputs)
        if transport_feasible_retry and require_rear_transport:return dict(result,independent_retry=proof)
        return result
