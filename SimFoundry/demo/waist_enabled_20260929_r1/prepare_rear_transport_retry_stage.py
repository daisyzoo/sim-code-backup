"""Isolate a one-retry transport witness option; no new physics from preparation."""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;A=W/'staged_rear_recovery_tracking';B=W/'staged_rear_transport_retry';assert not B.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();old=json.loads((A/'PREPARATION.json').read_text())
for n,h in old['stage_sha256'].items():assert sha(A/n)==h,n
for name in ['REAR_TRANSPORT_FEASIBLE_RETRY_REGRESSION.json','rear_tracking_physical_r1/case_840015/layout_840015_push_box_to_bin/REAR_TRANSPORT_RETRY_LIFECYCLE_FAILURE_CHECK.json']:
 report=json.loads((W/name).read_text());assert report['status']=='complete' and report['passed']
 for field in ['source_sha256','frozen_sha256']:
  for p,h in report[field].items():assert sha(p)==h,p
s=(A/'collect_paired_sorting.py').read_text();edits=[]
def edit(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b);edits.append(dict(old=a,new=b))
a="parser.add_argument('--rear-recovery-tracking',action='store_true',help='Diagnostic causal prior-command XY tracking correction during loaded rear recovery; requires hysteresis, default off.')"
edit(a,a+"\nparser.add_argument('--rear-transport-feasible-retry',action='store_true',help='Diagnostic one extra initialization of an iteration-limited feasible unloaded witness; original problem and gates, default off.')")
a='if args.rear_recovery_tracking and not args.rear_corridor_hysteresis:'
edit(a,"if args.rear_transport_feasible_retry and not args.rear_corridor_recovery:\n    raise ValueError('Transport retry requires existing diagnostic recovery contract')\n"+a)
a='        recontact_lifecycle=RecontactLifecycle(enabled=True,prefer_interior=args.recontact_interior_preference,**recontact_extra)'
edit(a,"        if args.rear_transport_feasible_retry:\n            from rear_transport_retry_lifecycle import RecontactLifecycle\n            if args.rear_box_entry_lift and side=='right':\n                from rear_transport_retry_entry_lifecycle import RecontactLifecycle\n            recontact_extra['transport_feasible_retry']=True\n"+a)
a="            episode.collect_meta['rear_recovery_tracking_max_bias_xy_m']=[.0015,.0005]"
edit(a,a+"\n        if args.rear_transport_feasible_retry:\n            episode.collect_meta['rear_transport_feasible_retry']=True\n            episode.collect_meta['rear_transport_max_extra_retries']=1")
helpers=['rear_transport_feasible_retry_candidate.py','rear_transport_retry_plan.py','rear_transport_retry_lifecycle.py','rear_transport_retry_entry_lifecycle.py']
a='    for path in paths:\n';edit(a,"    if args.rear_transport_feasible_retry:\n        paths.extend([STAGE/name for name in "+repr(helpers)+"])\n"+a)
ast.parse(s);back=s
for e in reversed(edits):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'])
assert back==(A/'collect_paired_sorting.py').read_text();B.mkdir()
for n in old['stage_sha256']:(B/n).write_bytes((A/n).read_bytes())
(B/'collect_paired_sorting.py').write_text(s)
for n in helpers:(B/n).write_bytes((W/n).read_bytes())
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_stage=str(A),stage=str(B),parent_preparation_sha256=sha(A/'PREPARATION.json'),edits=edits,new_helpers=helpers,stage_sha256={p.name:sha(p) for p in B.iterdir() if p.is_file()},simulation_started=False,training_ready=False,remaining='Independent retry metadata/lifecycle V2 check, actual CLI selection/flags and source binding, original audit integration, full fixed10 physics. No candidate policy result exists.')
(B/'PREPARATION.json').write_text(json.dumps(report,indent=2));print('prepared',B)
