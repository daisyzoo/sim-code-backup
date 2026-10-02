"""Explicit internal withdrawal0.05rad, never a change to formal0.20rad gate.
Same frozen inward collector; source/plan/raw identity checked before new audits.
Other micro-return tilt protection remains its original0.03rad implementation.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from audit_box_inward_source_contract import verify_box_inward_source
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_configuration(args,plan,meta):
    assert type(args.get('expert_top_tilt_recontact_rad')) is float and args['expert_top_tilt_recontact_rad']==.05,'explicit0.05 internal withdrawal required'
    cfg=plan['contact_stability_candidate'];assert type(cfg['tilt_recontact_rad']) is float and cfg['tilt_recontact_rad']==.05
    assert type(cfg['original_pose_max_tilt_rad']) is float and cfg['original_pose_max_tilt_rad']==.20,'formal upright gate must remain0.20'
    assert meta['frontal_bypass_plan']==plan,'raw/frontal plan mismatch'
    assert args['role']=='diagnostic' and meta['assist_frames']==0 and meta['push_assist'] is False
    return dict(configured_internal_withdrawal_rad=.05,original_upright_gate_rad=.20,original_other_guards_unchanged=True,training_ready=False)
def verify_episode(ep):
    ep=Path(ep);verify_box_inward_source(ep)
    prov=json.loads((ep.parent/'provenance.json').read_text());plan=json.loads((ep/'frontal_bypass.json').read_text())['plan']
    with np.load(ep/'raw.npz') as z:meta=json.loads(str(z['collect_meta']))
    out=verify_configuration(prov['args'],plan,meta)
    protocol=json.loads((W/'box_inward_groups_r1/PROTOCOL.json').read_text())
    # All source used by this parameter experiment must remain frozen to its parent.
    for rel,digest in prov['source_sha256'].items():
        assert sha(ep.parent/'source_snapshot'/rel)==digest==protocol['frozen_files_sha256'][str(W.parents[1]/rel)]
    expectations=W/'TILT05_SOURCE_EXPECTATIONS.json'
    for row in json.loads(expectations.read_text())['rows']:
        assert sha(row['path'])==row['sha256']
        if row['included_in_parent_protocol']:assert row['sha256']==protocol['frozen_files_sha256'][row['path']]
    out['gate_source_expectations_sha256']=sha(expectations)
    out.update(provenance_sha256=sha(ep.parent/'provenance.json'),raw_sha256=sha(ep/'raw.npz'),frontal_sha256=sha(ep/'frontal_bypass.json'),contract_sha256=sha(__file__))
    return out
