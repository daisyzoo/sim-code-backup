"""Freeze original full8push2wait with only isolated high-unloaded wrist prior.
Never rerun for an existing directory. Checks are counterfactual, not physics.
"""
from pathlib import Path
import json,hashlib,copy,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'rear_short_recovery_groups_r1';oldstage=w/'staged_rear_short_recovery';stage=w/'staged_unloaded_wrist_prior';r=w/'unloaded_wrist_prior_groups_r1';assert not r.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
closed=json.loads((parent/'RESULT.json').read_text());assert closed['status']=='diagnostic_closed_rejected' and closed['push_total']==8 and closed['waits_passed']==2 and closed['actual_sampled_visual_review_complete'] and closed['supplemental_execution_audits']==8
for file in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json','SUPPLEMENTAL_AUDIT_EXECUTION.json']:
 d=json.loads((parent/file).read_text());assert not Path(f"/proc/{d['pid']}/cmdline").exists()
 if file=='STATUS.json':assert d['completed_conditions']==10
 else:assert d['stage']=='complete'
reports=[json.loads((stage/name).read_text()) for name in ['INTEGRATION_CHECK.json','RECORDED_WRAPPER_REPLAY.json','LIVE_ENTRY_CHECK.json','NUMERICAL_AUDIT_CHECK.json']]
check,replay,entry,numerical=reports
assert check['passed'] and check['default_off_collector_and_coordination_ast_exact'] and len(check['argument_checks'])==12
assert replay['passed'] and sum(e['counts']['frames'] for e in replay['episodes'])==9592 and sum(e['counts']['applied'] for e in replay['episodes'])==54 and len(replay['fallback_tests'])==2
assert entry['passed'] and entry['total_frames']==9592 and entry['applied_frames']==54 and len(entry['episodes'])==8 and len(entry['negative_checks'])==10
assert numerical['passed'] and numerical['original_kkt_math_ast_exact'] and numerical['original_loaded_math_ast_exact'] and len(numerical['episodes'])==8 and numerical['task_kkt_failed_frames']==22
for report in reports:
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
for c in commands:c['args']=[x.replace(str(parent),str(r)) for x in c['args']]+['--unloaded-wrist-prior']
for a,b in zip(old['commands'],commands):assert a['layout_id']==b['layout_id'] and a['tasks']==b['tasks'] and [x.replace(str(r),str(parent)) for x in b['args'][:-1]]==a['args']
assert sum(len(c['tasks']) for c in commands if not c['wait'])==8 and sum(len(c['tasks']) for c in commands if c['wait'])==2
for path in stage.iterdir():
 if path.suffix in ['.py','.json']:files[str(path)]=sha(path)
for name in ['run_unloaded_wrist_prior_groups.py','prepare_unloaded_wrist_prior_groups.py','close_unloaded_wrist_prior_full.py','watch_unloaded_wrist_additional_audits.py','audit_unloaded_wrist_prior_live.py','audit_unloaded_wrist_task_optimality.py','audit_unloaded_wrist_loaded_execution.py','check_unloaded_wrist_integration.py','check_unloaded_wrist_wrapper_replay.py','check_unloaded_wrist_live_entry.py','check_unloaded_wrist_numerical_audits.py']:files[str(w/name)]=sha(w/name)
p=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),commands=commands,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),scope='Original full8push2wait/layouts/seeds/1200push70wait/order preserved. Only --unloaded-wrist-prior added to closed rear-short base. Keep original normal/tasks/damping/constraints; high unloaded rear recovery wrist preference with nominal-height/failed-solve full fallback. Independent actual height/prior plus original numerical KKT and unchanged loaded math. Original80+new56 audits and all10 actual image bindings required. KKT1e-6 not relaxed; no precision change or training admission.',training_ready=False)
(r/'PROTOCOL.json').write_text(json.dumps(p,indent=2));(r/'INPUT_COMPARISON.json').write_text(json.dumps(dict(same_tasks_layouts_seeds_horizons_order=True,new_flag='--unloaded-wrist-prior',commands=6,original_control_audits=80,additional_audit_calls=56,training_ready=False),indent=2));print(r)
