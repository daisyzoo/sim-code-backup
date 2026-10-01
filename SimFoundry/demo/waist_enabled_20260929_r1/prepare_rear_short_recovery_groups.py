"""Freeze original8push2wait with only rear short recovery after full parent closure.
Never call twice or before the complete parent/image/source audit is closed.
"""
from pathlib import Path
import json,hashlib,copy,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'micro_clearance_groups_r1';oldstage=w/'staged_micro_clearance_return';stage=w/'staged_rear_short_recovery';r=w/'rear_short_recovery_groups_r1';assert not r.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
closed=json.loads((parent/'RESULT.json').read_text());assert closed['status']=='diagnostic_closed_rejected' and closed['push_total']==8 and closed['waits_passed']==2 and closed['actual_sampled_visual_review_complete']
state=json.loads((parent/'STATUS.json').read_text());controls=json.loads((parent/'CONTROL_EVIDENCE_EXECUTION.json').read_text());extra=json.loads((parent/'ADDITIONAL_AUDIT_EXECUTION.json').read_text())
assert state['completed_conditions']==10 and controls['stage']==extra['stage']=='complete'
for pid in [state['pid'],controls['pid'],extra['pid']]:assert not Path(f'/proc/{pid}/cmdline').exists(),pid
check=json.loads((stage/'INTEGRATION_CHECK.json').read_text());replay=json.loads((stage/'RECORDED_INPUT_REPLAY.json').read_text());ik=json.loads((stage/'TASK_IK_SCREEN.json').read_text());cli=json.loads((stage/'CLI_CHECK.json').read_text())
assert check['passed'] and check['default_off_ast_equal'] and len(check['argument_checks'])==12
assert replay['passed'] and len(replay['episodes'])==4 and sum(e['frames'] for e in replay['episodes'])==4796 and all(len(e['guard_checks'])==5 for e in replay['episodes'])
assert ik['replay_sha256']==sha(stage/'RECORDED_INPUT_REPLAY.json') and sum(e['accepted_frames'] for e in ik['episodes'])==1285 and all(e['rejected_frames']==0 for e in ik['episodes'])
assert cli['passed'] and len(cli['checks'])==14 and sum(c['expected_pass'] for c in cli['checks'])==4 and cli['nonselected_front_streams']==2
for report in [check,replay,ik,cli]:
 for name,h in report['source_sha256'].items():assert sha(name)==h,name
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
for c in commands:c['args']=[x.replace(str(parent),str(r)) for x in c['args']]+['--rear-short-recovery']
for a,b in zip(old['commands'],commands):assert a['layout_id']==b['layout_id'] and a['tasks']==b['tasks'] and [x.replace(str(r),str(parent)) for x in b['args'][:-1]]==a['args']
assert sum(len(c['tasks']) for c in commands if not c['wait'])==8 and sum(len(c['tasks']) for c in commands if c['wait'])==2
for path in stage.iterdir():
 if path.suffix in ['.py','.json']:files[str(path)]=sha(path)
for name in ['run_rear_short_recovery_groups.py','prepare_rear_short_recovery_groups.py','close_rear_short_recovery_full.py','audit_rear_short_recovery_live.py','check_rear_short_recovery_integration.py','check_rear_short_recovery_integrated_replay.py','screen_rear_short_recovery_integrated_task_ik.py','check_rear_short_recovery_live_entry.py','watch_self_clearance_original_controls.py','watch_micro_additional_audits.py','audit_micro_unchanged_loaded_execution.py']:files[str(w/name)]=sha(w/name)
p=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),commands=commands,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),scope='Original full8push2wait/layouts/seeds/horizons/order; only --rear-short-recovery added. Rear region recontact height .91->.86m, initial/release .91m, loaded controller and all guards unchanged. Front micro-retention preserved. Independent initial/recovery/release/source and micro/diagonal audit; original80+extra48 and actual images remain. Extra KKT failure not waived. No training admission.',training_ready=False)
(r/'PROTOCOL.json').write_text(json.dumps(p,indent=2));(r/'INPUT_COMPARISON.json').write_text(json.dumps(dict(same_tasks_layouts_seeds_horizons_order=True,new_flag='--rear-short-recovery',commands=6,training_ready=False),indent=2));print(r)
