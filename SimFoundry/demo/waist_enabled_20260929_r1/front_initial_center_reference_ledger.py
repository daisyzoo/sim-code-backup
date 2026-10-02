"""Reference lifetimes after independently verified first-front handover.
Caller must verify the event with the native independent audit first. Hand-local
physical center persists. The selected parcel surface clears at recontact;
inner load/tilt resets occur after this frame's surface was computed, while an
outer direction-change reset occurs before it. No dynamics or task admission.
"""
import numpy as np
from audit_unloaded_wrist_prior_live import near


def verified_reference_lifetimes(rows, verified_front_events):
    assert [r['step'] for r in rows]==list(range(1,len(rows)+1))
    assert set(verified_front_events)<={r['step'] for r in rows}
    center=surface=None;previous_count=0;handover=None;centers={};surfaces={};resets=[]
    for row in rows:
        t=row['step'];event=verified_front_events.get(t)
        if event is not None:
            assert event['kind'] in ('command','handover') and row['recontacts']==0
            if event['kind']=='handover':
                assert handover is None and row['mode']=='top_press'
                center=list(event['captured_center_local']);surface=list(event['selected_surface_local_xy']);handover=t
        if center is None:
            assert 'front_initial_captured_center_local' not in row
            continue
        near(row['front_initial_captured_center_local'],center,0);centers[t]=center
        count=row.get('recontacts',previous_count)
        assert type(count) is int and count in (previous_count,previous_count+1)
        changed=count>previous_count
        before=bool(row.get('direction_change_recontact',{}).get('restarted'))
        if before:
            assert changed and row['last_recontact_reason']=='front_route_direction_change'
            surface=None
        if surface is not None and 'parcel_top_xyz' in row:surfaces[t]=surface
        if changed:
            resets.append(dict(step=t,reason=row['last_recontact_reason'],before_surface_computation=before))
            surface=None
        previous_count=count
    assert handover is None or set(centers)==set(range(handover,len(rows)+1))
    return dict(passed=True,centers=centers,surface_local_by_step=surfaces,handover_step=handover,resets=resets,scope=__doc__,training_ready=False)
