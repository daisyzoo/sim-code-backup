"""Shared explicit source-bound event admission for versioned region audits.
Disabled parent episodes retain original semantics; declared new paths must
pass the independent native-file audit before any reference exception is used.
"""
from pathlib import Path
import json
from audit_unloaded_wrist_prior_live import near

def verified_events(ep):
    from audit_front_projection_stage_contract import verify_front_projection_stage_source
    verify_front_projection_stage_source(ep)
    ep=Path(ep);args=json.loads((ep.parent/'provenance.json').read_text())['args'];path=ep/'recontact_pose.json'
    if not args.get('unloaded_recontact_pose',False):
        assert not path.exists() or not json.loads(path.read_text())['rows']
        assert not any(c.get('controller_kind')=='verified_unloaded_recontact_joint_path' or 'recontact_pose_override' in c for c in json.loads((ep/'coordination.json').read_text()))
        return {}
    from audit_front_projection_stage_pose_live import inspect
    result=inspect(ep);assert result==json.loads((ep/'FRONT_PROJECTION_STAGE_POSE_LIVE_V2_AUDIT.json').read_text())
    events={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads(path.read_text())['rows'] if r['kind'] in ('command','handover')}
    assert set(events)=={r['step'] for r in result['records']}
    return events

def selected_after_capture(row,selected,events):
    event=events.get(row['step'])
    if event is None or event['kind']!='handover':return selected
    assert row['mode']=='top_press' and row['active'] is False
    assert not row.get('solver') or not row['solver'].get('joint_override')
    near(row['center_local'],event['captured_center_local'],1e-9)
    near(row['selected_surface_local_xy'],event['selected_surface_local_xy'],1e-9)
    return event['selected_surface_local_xy']


def verified_front_events(ep):
    from audit_front_projection_stage_pose_live import inspect
    ep=Path(ep);result=inspect(ep)
    assert result==json.loads((ep/'FRONT_PROJECTION_STAGE_POSE_LIVE_V2_AUDIT.json').read_text())
    events={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'front_initial_center.json').read_text())['rows'] if r['kind'] in ('command','handover')}
    assert set(events)=={r['step'] for r in result['front_records']}
    return events
