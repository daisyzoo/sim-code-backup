"""Prepare isolated opt-in phase holding. No physics is launched by this script."""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;A=W/'staged_rear_corridor_recovery_guarded';B=W/'staged_rear_corridor_latched';assert not B.exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();old=json.loads((A/'PREPARATION.json').read_text());assert all(sha(A/n)==h for n,h in old['stage_sha256'].items())
check=json.loads((W/'REAR_CORRIDOR_LATCHED_CANDIDATE_V3_CHECK.json').read_text());assert check['status']=='complete' and check['passed']
for p,h in check['frozen_sha256'].items():assert sha(p)==h
s=(A/'collect_paired_sorting.py').read_text();edits=[]
def edit(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b);edits.append(dict(old=a,new=b))
a="parser.add_argument('--rear-corridor-recovery',action='store_true',help='Diagnostic measured rear corridor recovery with verified unload and directional recontact; default off.')"
edit(a,a+"\nparser.add_argument('--rear-corridor-hysteresis',action='store_true',help='Diagnostic measured20mm entry/22mm exit rear recovery phase; requires rear-corridor-recovery, default off.')")
a="if args.rear_corridor_recovery and not (args.role=='diagnostic'"
edit(a,"if args.rear_corridor_hysteresis and not args.rear_corridor_recovery:\n    raise ValueError('Rear hysteresis requires existing diagnostic rear recovery contract')\n"+a)
a='        rear_corridor_handovers=[]'
edit(a,a+"\n        if args.rear_corridor_hysteresis:\n            from rear_corridor_latched_phase_v2 import initial_state\n            rear_corridor_phase=initial_state()")
a='            from rear_corridor_collector_adapter import propose as propose_rear_recovery'
edit(a,a+"\n            rear_phase_kwargs={}\n            if args.rear_corridor_hysteresis:\n                from rear_corridor_latched_adapter import propose as propose_rear_recovery\n                rear_phase_kwargs=dict(phase_state=rear_corridor_phase,side=side)")
a="core_size=frontal_plan['region_causal_response']['actual_core']['collision_core_size_xyz'])\n            rear_corridor_log.append(rear_recovery_record)"
edit(a,"core_size=frontal_plan['region_causal_response']['actual_core']['collision_core_size_xyz'],**rear_phase_kwargs)\n            rear_corridor_log.append(rear_recovery_record)")
a='        previous = action.copy()\n        sample = snap(env, robot, hands)'
edit(a,"        if args.rear_corridor_hysteresis and rear_recovery_record is not None:\n            from rear_corridor_latched_adapter import commit_phase\n            rear_corridor_phase=commit_phase(phase_state=rear_corridor_phase,record=rear_recovery_record,guard=clearance_guard,current=rear_current,previous=previous[12:23],command=action[12:23])\n"+a)
a="        episode.collect_meta['rear_corridor_recovery']=True"
edit(a,a+"\n        if args.rear_corridor_hysteresis:\n            episode.collect_meta['rear_corridor_hysteresis']=True\n            episode.collect_meta['rear_corridor_exit_reserve_m']=.002")
a='    for path in paths:\n'
new_helpers=['rear_corridor_latched_phase_v2.py','rear_corridor_latched_solver.py','rear_corridor_latched_adapter.py']
edit(a,"    if args.rear_corridor_hysteresis:\n        paths.extend([STAGE/name for name in "+repr(new_helpers)+"])\n"+a)
ast.parse(s);restored=s
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==(A/'collect_paired_sorting.py').read_text();B.mkdir()
for name in old['stage_sha256']:(B/name).write_bytes((A/name).read_bytes())
(B/'collect_paired_sorting.py').write_text(s)
for name in new_helpers:(B/name).write_bytes((W/name).read_bytes())
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_stage=str(A),stage=str(B),parent_preparation_sha256=sha(A/'PREPARATION.json'),edits=edits,new_helpers=new_helpers,stage_sha256={p.name:sha(p) for p in B.iterdir() if p.is_file()},component_check_sha256=sha(W/'REAR_CORRIDOR_LATCHED_CANDIDATE_V3_CHECK.json'),simulation_started=False,training_ready=False,remaining='Actual adapter commit and collector AST/CLI checks, independent native phase+new objective auditing and source contract integration; new physical10-condition comparison cannot launch yet.')
(B/'PREPARATION.json').write_text(json.dumps(report,indent=2));print('PREPARED',B)
