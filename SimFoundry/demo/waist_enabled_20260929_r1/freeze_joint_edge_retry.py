"""Freeze verified diagnostic retry stage; no physics or training claim."""
from pathlib import Path
import json,hashlib,ast,types
w=Path(__file__).resolve().parent;s=w/'staged_joint_edge_retry';probe=w/'staged_joint_edge_retry_probe';parent=w/'staged_joint_edge_command';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (s/'MANIFEST.json').exists()
m=json.loads((parent/'MANIFEST.json').read_text())
for n,h in m['source_sha256'].items():assert sha(parent/n)==h
sources={n:sha(s/n) for n in m['source_sha256']};assert len(sources)==16
unchanged=[n for n in sources if n not in ['collect_paired_sorting.py','joint_edge_command.py','joint_edge_adapter.py']]
assert len(unchanged)==13
for n in unchanged:assert sources[n]==m['source_sha256'][n]
for n in ['joint_edge_command.py','joint_edge_adapter.py']:assert sha(probe/n)==sources[n]
pairs=[('ALL_RECORDS_CHECK.json','check_joint_edge_retry_probe.py'),('SEQUENTIAL_HISTORY_CHECK.json','check_joint_edge_retry_history.py'),('FAILURE_PATH_CHECK.json','check_joint_edge_retry_failures.py')]
for n,c in pairs:
 d=json.loads((probe/n).read_text());assert d['passed'] and d['checker_sha256']==sha(w/c)
 assert all(sources[f]==h for f,h in d['probe_source_sha256'].items())
 for ep in d.get('episodes',[]):
  path=w/'joint_edge_groups_r1'/('case_'+ep['episode'].split('_')[1])/ep['episode']
  for f,h in ep['source_sha256'].items():assert sha(path/f)==h
 (s/n).write_bytes((probe/n).read_bytes())
pairs += [('FINAL_HOOK_CHECK.json','check_joint_edge_retry_hook.py'),('PRELAUNCH_AND_SOURCE_CHECK.json','check_joint_edge_retry_prelaunch.py'),('RETRY_METADATA_CHECK.json','check_joint_edge_retry_metadata.py'),('AUDITOR_ENTRY_CHECK.json','check_joint_edge_retry_auditor_entry.py'),('ENTRY_FIXTURES.json','make_joint_edge_retry_entry_fixtures.py')]
for n,c in pairs:
 d=json.loads((s/n).read_text());assert d.get('passed',d.get('default_off_and_enabled_cli',n=='ENTRY_FIXTURES.json')) and d['checker_sha256']==sha(w/c)
hook=json.loads((s/'FINAL_HOOK_CHECK.json').read_text());pre=json.loads((s/'PRELAUNCH_AND_SOURCE_CHECK.json').read_text());entry=json.loads((s/'AUDITOR_ENTRY_CHECK.json').read_text());meta=json.loads((s/'RETRY_METADATA_CHECK.json').read_text())
assert hook['source_sha256']==pre['source_sha256']==sources
assert hook['default_ast_identical_except_explicit_additions'] and hook['hook_after_original_limits_before_previous']
assert sum(e['counts']['default_identical'] for e in hook['episodes'])==9592
assert sum(e['counts']['retry_checked'] for e in hook['episodes'])==9592
assert sum(e['counts']['front_excluded'] for e in hook['episodes'])==7194
assert sum(e['counts']['zero_excluded'] for e in hook['episodes'])==16
assert pre['actual_snapshot_writer_files']==60 and len(pre['negative_cli_rejected'])==59
assert len(entry['rows'])==32 and sum(r['expected_accept'] for r in entry['rows'])==3
assert all(r['returncode']==(0 if r['expected_accept'] else 1) and r['independent_report_written']==r['expected_accept'] for r in entry['rows'])
assert entry['fixtures_sha256']==sha(s/'ENTRY_FIXTURES.json')
assert entry['auditor_sha256']==meta['auditor_sha256']==sha(w/'audit_joint_edge_retry_execution_live.py')
fixtures=json.loads((s/'ENTRY_FIXTURES.json').read_text())
for row in fixtures['rows']:
 for n,h in row['source_sha256'].items():assert sha(Path(row['source'])/n)==h
# Execute actual route-plan addition, so runtime config cannot drift from fixtures.
tree=ast.parse((s/'collect_paired_sorting.py').read_text());node=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.rear_joint_edge_analytic_retry');env=dict(args=types.SimpleNamespace(rear_joint_edge_analytic_retry=True),frontal_plan={});exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual_plan_hook>','exec'),env)
bag=json.loads((Path(fixtures['rows'][1]['fixture'])/'frontal_bypass.json').read_text());assert env['frontal_plan']['rear_joint_edge_analytic_retry']==bag['plan']['rear_joint_edge_analytic_retry']
result=w/'joint_edge_groups_r1/RESULT.json';assert sha(result)=='3facc6b7a07557647627ecb3d8ae4755c03456f3813b3c9886a794a163887a97'
out=dict(source_sha256=sources,unchanged_parent_helpers=unchanged,parent_manifest_sha256=sha(parent/'MANIFEST.json'),parent_result_sha256=sha(result),checks_sha256={n:sha(s/n) for n,_ in pairs},checker_sha256={c:sha(w/c) for _,c in pairs},auditor_sha256=sha(w/'audit_rear_joint_xy_live.py'),execution_auditor_sha256=sha(w/'audit_joint_edge_retry_execution_live.py'),front_auditor_sha256=sha(w/'audit_front_edge_speed_live.py'),collector_wired=True,expected_archive_sources=60,physical_started=False,training_ready=False,scope='Default-off finite-primary-status8 one-shot analytic retry from originalLP; objective/bounds/tolerances/guards unchanged.9592 default identical; complete CLI3positive29negative and60archives; sequential fixed physical observations, no efficacy guarantee. Original raw-force,parentIK,finalFK/KKT independently verified; numeric solver termination reason source-bound, not independently reproduced.')
(s/'MANIFEST.json').write_text(json.dumps(out,indent=2));print('MANIFEST',sha(s/'MANIFEST.json'))
