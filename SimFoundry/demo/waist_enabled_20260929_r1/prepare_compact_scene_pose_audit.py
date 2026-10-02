"""Isolate the compact-rejection coverage fix; leave all frozen originals intact."""
from pathlib import Path
import json,hashlib,datetime,ast
W=Path(__file__).resolve().parent;src=W/'audit_joint_edge_stage_pose_live.py';out=W/'audit_joint_edge_stage_pose_live_v2.py';text=src.read_text();edits=[]
def replace(old,new):
 global text
 assert text.count(old)==1,old;text=text.replace(old,new);edits.append(dict(old=old,new=new))
replace('from audit_closed_peak_trial_events import EventAudit','from audit_compact_scene_rejection import EventAudit,has_compact_rejection')
replace("                audit.verify_preference(event['planning'],current=q[t],scene=scene,step=t)","""                if has_compact_rejection(event['planning']):
                    assert event['kind']=='unchanged' and event['reason']=='no_verified_endpoint' and not any(k in event for k in ['command','proposal','captured_center_local','reference'])
                    assert ctx['step']==t and ctx['selected'] is True and ctx['guard_stop'] is False and ctx['parent_mode'] in ('top_cross','top_descend') and ctx['recontacts']==f['recontacts']>0
                    assert not f.get('route_stop_reason') and not f.get('release_reason') and not regions[t]['abort_reason']
                    near(ctx['previous_q'],q[t-1],1e-7);near(ctx['previous_command'],u[t-1],0)
                    assert observed[t][0]==ctx['observed_load_n']==0 and observed[t][1]==ctx['filtered_load_n'] and 0<=observed[t][1]<=.05
                    near(ctx['observed_hand_pose'],audit.hand.fk(q[t],side),1e-4);near(ctx['observed_inactive_hand_pose'],audit.hand.fk(q[t],inactive),1e-4)
                    assert audit.hand.minz(q[t],side)>=.84
                audit.verify_preference(event['planning'],current=q[t],scene=scene,step=t)""")
replace("dependent_auditors_sha256={n:sha(w/n) for n in [", "dependent_auditors_sha256={n:sha(w/n) for n in ['audit_compact_scene_rejection.py',")
replace("out=ep/'JOINT_EDGE_STAGE_POSE_LIVE_AUDIT.json'", "out=ep/'JOINT_EDGE_STAGE_POSE_LIVE_V2_AUDIT.json'")
restored=text
for edit in reversed(edits):assert restored.count(edit['new'])==1;restored=restored.replace(edit['new'],edit['old'])
assert restored==src.read_text();ast.parse(text)
with out.open('x') as f:f.write(text)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent=str(src),parent_sha256=sha(src),auditor=str(out),auditor_sha256=sha(out),compact_helper_sha256=sha(W/'audit_compact_scene_rejection.py'),edits=edits,reverse_matches=True,training_ready=False)
with (W/'COMPACT_SCENE_POSE_AUDIT_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print('prepared isolated pose v2')
