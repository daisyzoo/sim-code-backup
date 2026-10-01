"""Freeze unchanged full8push2wait with one new micro-clearance contact-retention flag."""
from pathlib import Path
import json,hashlib,copy,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'front_diagonal_entry_groups_r1';oldstage=w/'staged_front_diagonal_entry';stage=w/'staged_micro_clearance_return';r=w/'micro_clearance_groups_r1';assert not r.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
closed=json.loads((parent/'RESULT.json').read_text());assert closed['status']=='diagnostic_closed_rejected' and closed['push_total']==8 and closed['waits_passed']==2
check=json.loads((stage/'INTEGRATION_CHECK.json').read_text());assert check['passed'] and check['default_off_ast_equal']
replay=json.loads((stage/'RECORDED_INPUT_REPLAY.json').read_text());assert replay['passed'] and sum(x['frames'] for x in replay['episodes'])==2398 and len(replay['guard_checks'])==9 and len(replay['tamper_checks'])==6
ik=json.loads((stage/'TASK_IK_SCREEN.json').read_text());assert ik['replay_sha256']==sha(stage/'RECORDED_INPUT_REPLAY.json') and all(x['rejected_frames']==0 for x in ik['episodes']) and sum(x['accepted_frames'] for x in ik['episodes'])==54
assert len(replay['independent_replay'])==2 and all(x['passed'] for x in replay['independent_replay'])
cli=json.loads((stage/'CLI_CHECK.json').read_text());assert cli['passed'] and len(cli['checks'])==9
guard=json.loads((w/'staged_micro_clearance_probe/GUARD_CHECK.json').read_text());assert guard['passed'] and len(guard['checks'])==13 and sha(stage/'micro_clearance_return.py')==sha(w/'staged_micro_clearance_probe/micro_clearance_return.py')
for report in [check,replay,ik,cli,guard]:
 for name,h in report['source_sha256'].items():assert sha(name)==h
old=json.loads((parent/'PROTOCOL.json').read_text());files={}
for name,h in old['frozen_files_sha256'].items():
 assert sha(name)==h,name
 path=Path(name.replace(str(oldstage),str(stage)))
 if str(path).startswith(str(parent/'layouts')):continue
 if path.exists():files[str(path)]=sha(path)
r.mkdir();(r/'layouts').mkdir()
for src in (parent/'layouts').glob('*.json'):
 dest=r/'layouts'/src.name;dest.write_bytes(src.read_bytes());files[str(dest)]=sha(dest)
commands=copy.deepcopy(old['commands'])
for c in commands:c['args']=[x.replace(str(parent),str(r)) for x in c['args']]+['--front-micro-repair-retention']
for a,b in zip(old['commands'],commands):assert a['layout_id']==b['layout_id'] and a['tasks']==b['tasks'] and [x.replace(str(r),str(parent)) for x in b['args'][:-1]]==a['args']
assert sum(len(c['tasks']) for c in commands if not c['wait'])==8 and sum(len(c['tasks']) for c in commands if c['wait'])==2
for path in stage.iterdir():
 if path.suffix in ['.py','.json']:files[str(path)]=sha(path)
for name in ['run_micro_clearance_groups.py','prepare_micro_clearance_groups.py','audit_micro_clearance_live.py','audit_micro_clearance_return.py','audit_front_diagonal_entry_live.py','check_micro_clearance_integration.py','check_micro_clearance_integrated_replay.py','check_micro_clearance_live_entry.py','screen_micro_clearance_integrated_task_ik.py','check_micro_clearance_guards.py','watch_self_clearance_original_controls.py','watch_micro_additional_audits.py','audit_micro_unchanged_loaded_execution.py']:files[str(w/name)]=sha(w/name)
p=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),commands=commands,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),scope='Same original8push2wait/layouts/seeds/horizons/order; only --front-micro-repair-retention added; source-bound independent micro-return eligibility replaces unconditional direction-change restart audit, preserving initial turns, load loss and original guards. Independent diagonal/COP/actual-direction edge audit unchanged. Geometry constraints unchanged. Original guards precede loaded direction-change recontact, no data admission. Extra IK optimality failure from parent remains unresolved and must be reported; not silently waived.',training_ready=False)
(r/'PROTOCOL.json').write_text(json.dumps(p,indent=2));(r/'INPUT_COMPARISON.json').write_text(json.dumps(dict(same_tasks_layouts_seeds_horizons_order=True,new_flag='--front-micro-repair-retention',commands=6,training_ready=False),indent=2));print(r)
