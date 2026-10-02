"""Prepare fixed complete comparison and diagnostic review tools; no launch."""
from pathlib import Path
import json,hashlib,datetime,ast
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();P=W/'rear_latched_physical_preparation_r1';assert not P.exists();P.mkdir()
oldpath=W/'rear_corridor_physical_preparation_r1/PLAN.json';old=json.loads(oldpath.read_text());plan=json.loads(oldpath.read_text());stage=W/'staged_rear_corridor_latched';plan.update(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),collector_sha256=sha(stage/'collect_paired_sorting.py'),stage_check_sha256=sha(stage/'CHECK.json'),independent_record_check_sha256=sha(W/'REAR_CORRIDOR_LATCHED_NATIVE_FIXTURE_CHECK.json'),parent_comparison_plan_sha256=sha(oldpath),scope='Same full8push2wait, new measured20mm entry/22mm exit phase only; no inference of success from component checks.',launch_allowed=False,launch_requirements=['All specified source/component/native/unchanged-audit checks pass; original30GiB startup and remaining-budget storage; idle GPU; full paired groups and actual visual review.'])
byid={r['layout_id']:r for r in plan['commands']};plan['commands']=[byid[i] for i in [840004,840015,840005,840014,841002,841007]]
for item in plan['commands']:item['args'].append('--rear-corridor-hysteresis')
(P/'PLAN.json').write_text(json.dumps(plan,indent=2));manifest=[]
subs={'rear_corridor_stage_run_contract_v2':'rear_latched_run_contract','rear_corridor_stage_source_binding':'rear_corridor_latched_source_binding','audit_rear_corridor_stage_source_contract':'audit_rear_latched_stage_source_contract','verify_rear_corridor_stage_source':'verify_rear_latched_stage_source','audit_rear_corridor_stage_contacts':'audit_rear_latched_stage_contacts','audit_rear_corridor_stage_pressure':'audit_rear_latched_stage_pressure','run_rear_corridor_physical_v4.py':'run_rear_latched_physical.py','REAR_CORRIDOR_STAGE_NUMERIC_REVIEW':'REAR_LATCHED_STAGE_NUMERIC_REVIEW','REAR_CORRIDOR_INCOMPLETE_REVIEW':'REAR_LATCHED_INCOMPLETE_REVIEW','REAR_CORRIDOR_REVIEW':'REAR_LATCHED_REVIEW'}
for parent,new in [('watch_rear_corridor_physical_audits_v4.py','watch_rear_latched_physical_audits.py'),('review_rear_corridor_stage_episode.py','review_rear_latched_stage_episode.py'),('review_rear_corridor_incomplete_episode.py','review_rear_latched_incomplete_episode.py'),('close_rear_corridor_physical.py','close_rear_latched_physical.py')]:
 source=(W/parent).read_text();s=source;edits=[]
 for a,b in sorted(subs.items(),key=lambda x:-len(x[0])):
  count=s.count(a)
  if count:assert b not in s;s=s.replace(a,b);edits.append(dict(old=a,new=b,count=count))
 back=s
 for e in reversed(edits):assert back.count(e['new'])==e['count'];back=back.replace(e['new'],e['old'])
 assert back==source;ast.parse(s);out=W/new;assert not out.exists();out.write_text(s);manifest.append(dict(parent=parent,new=new,parent_sha256=sha(W/parent),new_sha256=sha(out),edits=edits))
(W/'REAR_LATCHED_RUNTIME_PREPARATION.json').write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=manifest,original_plan_sha256=sha(oldpath),new_plan_sha256=sha(P/'PLAN.json'),simulation_started=False,training_ready=False),indent=2));print('Prepared fixed10-condition plan, watcher, reviewers and closure.')
