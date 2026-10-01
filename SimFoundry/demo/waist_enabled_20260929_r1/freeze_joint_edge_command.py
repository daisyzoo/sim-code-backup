"""Freeze actual collector wiring and independent action audit; no efficacy claim."""
from pathlib import Path
import json,hashlib
w=Path(__file__).resolve().parent;s=w/'staged_joint_edge_command';parent=w/'staged_rear_joint_xy';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
assert not (s/'MANIFEST.json').exists()
old=json.loads((parent/'MANIFEST.json').read_text())
for n,h in old['source_sha256'].items():assert sha(parent/n)==h
for n,h in old['checks_sha256'].items():assert sha(parent/n)==h
for n,h in old['checker_sha256'].items():assert sha(w/n)==h
sources={n:sha(s/n) for n in [*old['source_sha256'],'joint_edge_command.py','joint_edge_adapter.py']};assert len(sources)==16
unchanged=[n for n in old['source_sha256'] if n!='collect_paired_sorting.py'];assert len(unchanged)==13
for n in unchanged:assert sources[n]==old['source_sha256'][n]
assert sources['joint_edge_command.py']==sha(w/'staged_joint_edge_probe/joint_edge_command.py')
pairs=[('COLLECTOR_WIRING_CHECK.json','check_joint_edge_collector_selection.py'),('FINAL_HOOK_CHECK.json','check_joint_edge_final_hook.py'),('AUDITOR_ENTRY_CHECK.json','check_joint_edge_auditor_entry.py')]
for n,c in pairs:
 d=json.loads((s/n).read_text());assert d['passed'] and d['checker_sha256']==sha(w/c)
hook=json.loads((s/'FINAL_HOOK_CHECK.json').read_text());assert hook['default_collector_ast_identical_except_explicit_additions'] and hook['actual_final_hook_after_original_float32_bounds_before_previous_update']
for field,name in [('collector_sha256','collect_paired_sorting.py'),('adapter_sha256','joint_edge_adapter.py'),('helper_sha256','joint_edge_command.py')]:assert hook[field]==sources[name]
assert hook['counts']==dict(default_identical=4796,enabled_parent_preserved=2259,enabled_changed=139,front_excluded=2398,zero_excluded=4)
for ep in hook['episodes']:
 path=w/'rear_joint_xy_groups_r1'/('case_'+ep['episode'].split('_')[1])/ep['episode']
 for n,h in ep['source_sha256'].items():assert sha(path/n)==h
pre=json.loads((s/'PRELAUNCH_AND_SOURCE_CHECK.json').read_text());assert pre['default_off_and_enabled_cli'] and pre['actual_snapshot_writer_files']==60 and len(pre['negative_cli_rejected'])==58 and pre['source_sha256']==sources
pairs.append(('PRELAUNCH_AND_SOURCE_CHECK.json','check_joint_edge_prelaunch.py'))
probe=json.loads((w/'JOINT_EDGE_COMMAND_PROBE_CHECK.json').read_text());assert probe['passed'] and probe['helper_sha256']==sources['joint_edge_command.py'] and probe['checker_sha256']==sha(w/'check_joint_edge_command_probe.py')
(s/'HELPER_CHECK.json').write_bytes((w/'JOINT_EDGE_COMMAND_PROBE_CHECK.json').read_bytes());pairs.append(('HELPER_CHECK.json','check_joint_edge_command_probe.py'))
entry=json.loads((s/'AUDITOR_ENTRY_CHECK.json').read_text());assert entry['auditor_sha256']==sha(w/'audit_joint_edge_execution_live.py') and entry['fixtures_sha256']==sha(s/'ENTRY_FIXTURES.json');assert len(entry['rows'])==22 and sum(x['expected_accept'] for x in entry['rows'])==3
assert all(x['returncode']==(0 if x['expected_accept'] else 1) and x['independent_report_written']==x['expected_accept'] for x in entry['rows'])
fixtures=json.loads((s/'ENTRY_FIXTURES.json').read_text())
for item in fixtures['rows']:
 for n,h in item['source_sha256'].items():assert sha(Path(item['source'])/n)==h
geometry={}
for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
 path=w/f'rear_joint_xy_groups_r1/case_{cid}/layout_{cid}_{task}/JOINT_EDGE_HELPER_CONTACT_GEOMETRY.json';d=json.loads(path.read_text());assert d['helper_probe_sha256']==sha(w/'JOINT_EDGE_COMMAND_PROBE_CHECK.json') and d['checker_sha256']==sha(w/'check_joint_edge_helper_contact_geometry.py');geometry[str(path.relative_to(w))]=sha(path)
checks={n:sha(s/n) for n,_ in pairs};checks['ENTRY_FIXTURES.json']=sha(s/'ENTRY_FIXTURES.json')
checkers={c:sha(w/c) for _,c in pairs};checkers.update({c:sha(w/c) for c in ['make_joint_edge_entry_fixtures.py','check_joint_edge_helper_contact_geometry.py']})
result=w/'rear_joint_xy_groups_r1/RESULT.json';assert sha(result)=='de248d42a89a68b1fe02e377aa1a7ab538fd44bce5fe783c885bb268c22846e9'
out=dict(source_sha256=sources,unchanged_parent_helpers=unchanged,parent_manifest_sha256=sha(parent/'MANIFEST.json'),parent_result_sha256=sha(result),checks_sha256=checks,checker_sha256=checkers,geometry_report_sha256=geometry,auditor_sha256=sha(w/'audit_rear_joint_xy_live.py'),execution_auditor_sha256=sha(w/'audit_joint_edge_execution_live.py'),front_auditor_sha256=sha(w/'audit_front_edge_speed_live.py'),collector_wired=True,expected_archive_sources=60,physical_started=False,training_ready=False,scope='Original collector AST unchanged after removing explicit default-off additions;13 parent helpers byte-identical. Final upper action refined only after original guards and valid rearXY; original bounded parent IK and final nonlinear direction independently audited.4796 default identical,2398 front excluded,139 changes;3 CLI positives19 negatives,propagated shadow commands with fixed physical observations. Bag one numeric fallback preserves parent and nominal anchored contact still moves outward5.124mm; all static geometry is not future COP/collision/dynamics proof. No new physical success or training data.')
(s/'MANIFEST.json').write_text(json.dumps(out,indent=2));print('MANIFEST',sha(s/'MANIFEST.json'))
