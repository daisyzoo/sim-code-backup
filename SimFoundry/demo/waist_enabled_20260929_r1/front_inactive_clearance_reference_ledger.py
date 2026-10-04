"""Independent reference/surface lifetimes for first and repeated front landing.
Callers MUST independently verify both event streams before supplying them.
This ledger checks bookkeeping only; it does not certify event physics.
The immutable initial capture and the latest recovery capture remain separate.
"""
import numpy as np
from audit_unloaded_wrist_prior_live import near


def verified_reference_lifetimes(rows, verified_front_events, verified_recovery_events, *, side):
    assert side in ('left','right')
    steps={r['step'] for r in rows}
    assert [r['step'] for r in rows]==list(range(1,len(rows)+1))
    assert set(verified_front_events)<=steps and set(verified_recovery_events)<=steps
    assert not set(verified_front_events)&set(verified_recovery_events)
    assert not verified_recovery_events or side=='left'
    initial=recovery=surface=None;first=None;previous_count=0
    centers={};initial_centers={};recovery_centers={};surfaces={};resets=[];handovers=[];completed=set()
    def vector(v,n):
        x=np.asarray(v,float);assert x.shape==(n,) and np.isfinite(x).all();return x.tolist()
    for row in rows:
        t=row['step'];count=row.get('recontacts',previous_count)
        assert type(count) is int and count in (previous_count,previous_count+1)
        changed=count>previous_count
        before=bool(row.get('direction_change_recontact',{}).get('restarted'))
        if before:
            assert changed and row['last_recontact_reason']=='front_route_direction_change'
            surface=None
        a=verified_front_events.get(t);b=verified_recovery_events.get(t)
        if a is not None:
            assert a['kind'] in ('command','handover') and count==0
            assert a['context']['recontacts']==0
            if a['kind']=='handover':
                assert first is None and row['mode']=='top_press'
                initial=vector(a['captured_center_local'],3)
                surface=vector(a['selected_surface_local_xy'],2);first=t
        if b is not None:
            assert side=='left' and b['kind'] in ('command','handover')
            assert count>0 and type(b['context']['recontacts']) is int and b['context']['recontacts']==count
            assert b['real_recontact_index']==count and count not in completed
            assert not row.get('route_stop_reason') and not row.get('release_reason')
            if b['kind']=='handover':
                assert row['mode']=='top_press' and not changed
                recovery=vector(b['captured_center_local'],3)
                surface=vector(b['selected_surface_local_xy'],2)
                completed.add(count);handovers.append(dict(step=t,recontacts=count,center_local=recovery,surface_local_xy=surface))
        if initial is None:assert 'front_initial_captured_center_local' not in row
        else:
            near(row['front_initial_captured_center_local'],initial,0);initial_centers[t]=list(initial)
        if recovery is None:assert 'front_recontact_captured_center_local' not in row
        else:
            near(row['front_recontact_captured_center_local'],recovery,0);recovery_centers[t]=list(recovery)
        center=recovery if recovery is not None else initial
        if center is not None:centers[t]=list(center)
        if surface is not None and 'parcel_top_xyz' in row:surfaces[t]=list(surface)
        if changed:
            resets.append(dict(step=t,reason=row['last_recontact_reason'],before_surface_computation=before));surface=None
        previous_count=count
    if first is not None:assert set(initial_centers)==set(range(first,len(rows)+1))
    if handovers:assert set(recovery_centers)==set(range(handovers[0]['step'],len(rows)+1))
    return dict(passed=True,centers=centers,surface_local_by_step=surfaces,handover_step=first,resets=resets,initial_centers=initial_centers,recovery_centers=recovery_centers,recovery_handovers=handovers,scope=__doc__,training_ready=False)
