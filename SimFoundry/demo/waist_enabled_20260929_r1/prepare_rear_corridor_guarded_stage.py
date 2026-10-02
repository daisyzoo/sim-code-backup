"""Preserve first wired stage and add explicit pending-handover fallback guard.
No existing prepared sources are edited, and no physics is launched.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;A=W/'staged_rear_corridor_recovery';B=W/'staged_rear_corridor_recovery_guarded';assert not B.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();old=json.loads((A/'PREPARATION.json').read_text());assert all(sha(A/n)==h for n,h in old['stage_sha256'].items());s=(A/'collect_paired_sorting.py').read_text();extra=[]
def replace(before,after):
 global s
 assert s.count(before)==1;s=s.replace(before,after);extra.append(dict(old=before,new=after))
anchor="                            recontact_event['old_normal_anchor']=top_contact_normal_anchor\n"
replace(anchor,"""                            if args.rear_corridor_recovery:
                                from rear_corridor_recontact_gate import guard_pending
                                recontact_event=guard_pending(enabled=True,state=frontal_state,event=recontact_event,parent_mode=waypoint['mode'])
"""+anchor)
anchor='    for path in paths:\n'
replace(anchor,"    if args.rear_corridor_recovery:\n        paths.append(STAGE/'rear_corridor_recontact_gate.py')\n"+anchor)
ast.parse(s);recovered=s
for edit in reversed(old['edits']+extra):assert recovered.count(edit['new'])==1;recovered=recovered.replace(edit['new'],edit['old'])
assert recovered==(Path(old['parent'])/'collect_paired_sorting.py').read_text();B.mkdir()
for name in old['stage_sha256']:(B/name).write_bytes((A/name).read_bytes())
(B/'collect_paired_sorting.py').write_text(s);(B/'rear_corridor_recontact_gate.py').write_bytes((W/'rear_corridor_recontact_gate.py').read_bytes())
report=dict(old,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stage=str(B),previous_stage=str(A),previous_preparation_sha256=sha(A/'PREPARATION.json'),helpers=old['helpers']+['rear_corridor_recontact_gate.py'],edits=old['edits']+extra,pending_guard_edits=extra,stage_sha256={p.name:sha(p) for p in B.iterdir() if p.is_file()},remaining='Previous full runtime check still required; guarded CLI/event checks and full independent physical audit adapters before launch',simulation_started=False,training_ready=False)
(B/'PREPARATION.json').write_text(json.dumps(report,indent=2));print('GUARDED_STAGE_PREPARED',B)
