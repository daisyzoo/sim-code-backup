from pathlib import Path
import json,ast,hashlib,datetime
W=Path('/home/user/Documents/zoo/sim/SimFoundry/demo/waist_enabled_20260929_r1');A=W/'staged_rear_corridor_latched';B=W/'staged_rear_recovery_tracking';assert not B.exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
check=json.loads((W/'REAR_RECOVERY_TRACKING_SOLVER_V2_CHECK.json').read_text());assert check['status']=='complete' and check['passed']
for p,h in {**check['frozen_sha256'],**check['source_sha256']}.items():assert sha(p)==h,p
prep=json.loads((A/'PREPARATION.json').read_text())
for n,h in prep['stage_sha256'].items():assert sha(A/n)==h,n
# A distinct adapter routes to the distinct solver. State/commit/unload retain parent code.
p=W/'rear_recovery_tracking_adapter.py';assert not p.exists();s=(W/'rear_corridor_latched_adapter.py').read_text();adapter_edits=[]
def replace(text,a,b,edits):
 assert text.count(a)==1,a;edits.append(dict(old=a,new=b));return text.replace(a,b)
s=replace(s,'from rear_corridor_latched_solver import solve','from rear_recovery_tracking_solver_v2 import solve',adapter_edits)
s=replace(s,'phase_state=None, side=None, **inputs):','phase_state=None, side=None, tracking_feedback=False, previous_recovery_record=None, **inputs):',adapter_edits)
s=replace(s,"    if type(enabled) is not bool or type(selected) is not bool:","    if type(tracking_feedback) is not bool:\n        raise ValueError('Explicit tracking option required')\n    if type(enabled) is not bool or type(selected) is not bool:",adapter_edits)
s=replace(s,"recovery_active=phase['after']['active'], **inputs)","recovery_active=phase['after']['active'], tracking_feedback=tracking_feedback,\n                              previous_recovery_record=previous_recovery_record, **inputs)",adapter_edits)
ast.parse(s);p.write_text(s)
s=(A/'collect_paired_sorting.py').read_text();edits=[]
def edit(a,b):
 global s
 s=replace(s,a,b,edits)
a="parser.add_argument('--rear-corridor-hysteresis',action='store_true',help='Diagnostic measured20mm entry/22mm exit rear recovery phase; requires rear-corridor-recovery, default off.')"
edit(a,a+"\nparser.add_argument('--rear-recovery-tracking',action='store_true',help='Diagnostic causal prior-command XY tracking correction during loaded rear recovery; requires hysteresis, default off.')")
a='if args.rear_corridor_hysteresis and not args.rear_corridor_recovery:'
edit(a,"if args.rear_recovery_tracking and not args.rear_corridor_hysteresis:\n    raise ValueError('Tracking requires the existing hysteresis diagnostic contract')\n"+a)
a='                rear_phase_kwargs=dict(phase_state=rear_corridor_phase,side=side)'
edit(a,a+"\n            if args.rear_recovery_tracking:\n                from rear_recovery_tracking_adapter import propose as propose_rear_recovery\n                rear_phase_kwargs.update(tracking_feedback=True,previous_recovery_record=rear_corridor_log[-1] if rear_corridor_log else None)")
a="            episode.collect_meta['rear_corridor_exit_reserve_m']=.002"
edit(a,a+"\n        if args.rear_recovery_tracking:\n            episode.collect_meta['rear_recovery_tracking']=True\n            episode.collect_meta['rear_recovery_tracking_max_bias_xy_m']=[.0015,.0005]")
helpers=['rear_recovery_tracking_adapter.py','rear_recovery_tracking_solver_v2.py','rear_recovery_tracking_observation_v2.py']
a='    for path in paths:\n';edit(a,"    if args.rear_recovery_tracking:\n        paths.extend([STAGE/name for name in "+repr(helpers)+"])\n"+a)
ast.parse(s);restored=s
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==(A/'collect_paired_sorting.py').read_text()
B.mkdir()
for n in prep['stage_sha256']:(B/n).write_bytes((A/n).read_bytes())
(B/'collect_paired_sorting.py').write_text(s)
for n in helpers:(B/n).write_bytes((W/n).read_bytes())
(B/'PREPARATION.json').write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_stage=str(A),stage=str(B),parent_preparation_sha256=sha(A/'PREPARATION.json'),edits=edits,adapter_edits=adapter_edits,new_helpers=helpers,stage_sha256={p.name:sha(p) for p in B.iterdir() if p.is_file()},component_check_sha256=sha(W/'REAR_RECOVERY_TRACKING_SOLVER_V2_CHECK.json'),simulation_started=False,training_ready=False,remaining='Actual parser/adapter/phase commit checks and independent trajectory audits/source bindings required before fixed paired physics.'),indent=2))
print('PREPARED',B)
