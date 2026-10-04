"""Independent descriptive count correction; original frozen reviews unchanged."""
from pathlib import Path
import collections
import datetime
import hashlib
import json

W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={};rows=[]
runs=['joint_transport_physical_r1','joint_transport_reserve_physical_r1','rear_trailing_physical_r1','front_corridor_lateral_physical_r1','front_box_trailing_physical_r1','front_box_trailing_physical_r2']
for run in runs:
    for ep in sorted((W/run).glob('case_*/layout_*')):
        if not ep.is_dir() or ep.name.endswith('wait_no_package'):continue
        reviews=list(ep.glob('*STAGE_NUMERIC_REVIEW.json'))
        if len(reviews)!=1:continue
        paths=[reviews[0],ep/'frontal_bypass.json',ep/'expert_control.json']
        for p in paths:sources[str(p)]=sha(p)
        numeric=json.loads(reviews[0].read_text());fr=json.loads(paths[1].read_text())['rows'];control=json.loads(paths[2].read_text())
        by_step={r['step']:r for r in fr};assert len(by_step)==len(fr)
        exits=[]
        for previous,current in zip(control,control[1:]):
            if previous['mode']!='top_push' or current['mode']=='top_push':continue
            step=current['step'];r=by_step[step];prior=by_step[previous['step']]
            advanced=r.get('recontacts',0)>prior.get('recontacts',0)
            if current['mode'] in {'top_release','goal_release','bypass_release'}:
                classification='release:'+str(r.get('release_reason'))
            elif advanced:
                classification=r.get('last_recontact_reason') or 'unclassified_recontact'
            else:
                classification='unclassified_transition'
            exits.append(dict(step=step,to_mode=current['mode'],retained_last_reason=r.get('last_recontact_reason'),counter_advanced=advanced,classification=classification))
        counts=collections.Counter(x['classification'] for x in exits)
        corrected=dict(tilt_exit_count=counts['incipient_tilt_independent'],lost_contact_exit_count=counts['lost_contact'])
        old={k:numeric[k] for k in corrected}
        rows.append(dict(run=run,episode=ep.name,original_reported=old,transition_verified=corrected,changed=old!=corrected,unclassified_transitions=[x for x in exits if x['classification'].startswith('unclassified')],exits=exits,original_task_and_pose_passed=numeric['original_task_and_pose_passed'],training_ready=False))
for p,h in sources.items():assert sha(p)==h,p
sources[str(Path(__file__).resolve())]=sha(__file__)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=len(rows),changed_episodes=sum(r['changed'] for r in rows),rows=rows,source_sha256=sources,limitations=['Only episodes with existing full numeric review are included; unreviewed/undumped episodes are not called passed.','This corrects descriptive exit counting, not original task/pose/control gates.','A retained last_recontact_reason at release is historical; a new recontact requires counter advancement. Unclassified transitions are retained explicitly.'],training_ready=False)
dest=W/'CONTACT_EXIT_COUNT_AUDIT_V1.json'
with dest.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(episodes=len(rows),changed_episodes=out['changed_episodes'],changed=[{k:r[k] for k in ['run','episode','original_reported','transition_verified']} for r in rows if r['changed']],unclassified=sum(len(r['unclassified_transitions']) for r in rows)),indent=2))
