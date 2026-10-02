"""Prepare the same full ten conditions, changing only causal tracking feedback."""
from pathlib import Path
import json,hashlib,datetime,ast
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();P=W/'rear_tracking_physical_preparation_r1';assert not P.exists();P.mkdir()
oldpath=W/'rear_latched_physical_preparation_r1/PLAN.json';plan=json.loads(oldpath.read_text());S=W/'staged_rear_recovery_tracking';plan.update(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(S/'collect_paired_sorting.py'),collector_sha256=sha(S/'collect_paired_sorting.py'),stage_check_sha256=sha(S/'CHECK.json'),independent_record_check_sha256=sha(W/'REAR_RECOVERY_TRACKING_NATIVE_PAIR_FIXTURE_CHECK.json'),parent_comparison_plan_sha256=sha(oldpath),scope='Same full8push2wait, bounded past-command/current-measurement XY compensation in loaded rear recovery only. No outcome inferred from component checks.',launch_allowed=False)
for item in plan['commands']:item['args'].append('--rear-recovery-tracking')
(P/'PLAN.json').write_text(json.dumps(plan,indent=2));manifest=[]
subs={'rear_latched_run_contract':'rear_tracking_run_contract','rear_corridor_latched_source_binding':'rear_recovery_tracking_source_binding','audit_rear_latched_stage_source_contract':'audit_rear_tracking_stage_source_contract','verify_rear_latched_stage_source':'verify_rear_tracking_stage_source','audit_rear_latched_stage_contacts':'audit_rear_tracking_stage_contacts','audit_rear_latched_stage_pressure':'audit_rear_tracking_stage_pressure','run_rear_latched_physical.py':'run_rear_tracking_physical.py','REAR_LATCHED_STAGE_NUMERIC_REVIEW':'REAR_TRACKING_STAGE_NUMERIC_REVIEW','REAR_LATCHED_INCOMPLETE_REVIEW':'REAR_TRACKING_INCOMPLETE_REVIEW','REAR_LATCHED_REVIEW':'REAR_TRACKING_REVIEW'}
for name in ['watch_rear_latched_physical_audits.py','review_rear_latched_stage_episode.py','review_rear_latched_incomplete_episode.py','close_rear_latched_physical.py']:
 new=name.replace('rear_latched','rear_tracking');source=(W/name).read_text();s=source;edits=[]
 for a,b in sorted(subs.items(),key=lambda x:-len(x[0])):
  count=s.count(a)
  if count:assert b not in s;s=s.replace(a,b);edits.append(dict(old=a,new=b,count=count))
 back=s
 for e in reversed(edits):assert back.count(e['new'])==e['count'];back=back.replace(e['new'],e['old'])
 assert back==source;ast.parse(s);p=W/new;assert not p.exists();p.write_text(s);manifest.append(dict(parent=name,new=new,parent_sha256=sha(W/name),new_sha256=sha(p),edits=edits))
with (W/'REAR_TRACKING_RUNTIME_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=manifest,original_plan_sha256=sha(oldpath),new_plan_sha256=sha(P/'PLAN.json'),simulation_started=False,training_ready=False),f,indent=2)
s=(W/'run_rear_latched_physical.py').read_text()
s=s.replace('rear_latched_physical_preparation_r1','rear_tracking_physical_preparation_r1').replace("PREVIOUS=W/'rear_corridor_physical_r1'","PREVIOUS=W/'rear_latched_physical_r1'")
s=s.replace('rear_corridor_latched_source_binding','rear_recovery_tracking_source_binding').replace('rear_latched_run_contract','rear_tracking_run_contract')
a=s.index('CHECKS=');b=s.index('\ndef bound',a)
s=s[:a]+"CHECKS="+repr(['REAR_RECOVERY_TRACKING_SOLVER_V2_CHECK.json','REAR_RECOVERY_TRACKING_RECORDS_CHECK.json','REAR_RECOVERY_TRACKING_NATIVE_FALLBACK_FIXTURE_CHECK.json','REAR_RECOVERY_TRACKING_NATIVE_PAIR_FIXTURE_CHECK.json','REAR_TRACKING_ORIGINAL_AUDIT_CHECK.json','REAR_RECOVERY_TRACKING_SOURCE_PREPARATION_CHECK.json'])+"\nMANIFESTS="+repr(['REAR_TRACKING_ORIGINAL_AUDIT_PREPARATION.json','REAR_TRACKING_RUNTIME_PREPARATION.json','REAR_RECOVERY_TRACKING_RECORDS_PREPARATION.json'])+s[b:]
s=s.replace('staged_rear_corridor_latched','staged_rear_recovery_tracking').replace('rear_corridor_physical_preparation_r1/PLAN.json','rear_latched_physical_preparation_r1/PLAN.json')
s=s.replace("if x!='--rear-corridor-hysteresis'","if x!='--rear-recovery-tracking'")
s=s.replace("args.count('--rear-corridor-hysteresis')==args.count('--rear-corridor-recovery')==1","args.count('--rear-recovery-tracking')==args.count('--rear-corridor-hysteresis')==args.count('--rear-corridor-recovery')==1")
s=s.replace('audit_rear_latched_stage_contacts','audit_rear_tracking_stage_contacts').replace('audit_rear_latched_stage_pressure','audit_rear_tracking_stage_pressure')
s=s.replace('REAR_LATCHED_ORIGINAL_AUDIT_PREPARATION','REAR_TRACKING_ORIGINAL_AUDIT_PREPARATION').replace('REAR_LATCHED_RUNTIME_PREPARATION','REAR_TRACKING_RUNTIME_PREPARATION')
s=s.replace('watch_rear_latched_physical_audits.py','watch_rear_tracking_physical_audits.py')
s=s.replace("default=str(W/'rear_latched_physical_r1')","default=str(W/'rear_tracking_physical_r1')")
s=s.replace('Complete paired diagnostic of measured recovery-phase holding','Complete paired diagnostic of bounded causal recovery tracking compensation')
ast.parse(s);p=W/'run_rear_tracking_physical.py';assert not p.exists();p.write_text(s)
print('prepared full10 runtime and runner')
