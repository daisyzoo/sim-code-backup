"""Apply isolated lead candidate after complete parent evidence, never queue it."""
from pathlib import Path
import json,hashlib,shutil,datetime
root=Path(__file__).resolve().parent;repo=root.parents[1];run=root/'contact_center_groups_r1';stage=root/'staged_bounded_top_lead';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
a=json.loads((run/'AUDIT_EXECUTION.json').read_text());assert len(a)==9 and all(x['returncode']==0 for x in a)
g=json.loads((run/'COMPLETE_GROUP_READINESS.json').read_text());assert len(g['rows'])==12 and all(e.endswith(': task/pose failed') for e in g['errors'])
r=json.loads((run/'RESULT.json').read_text());assert len(r['rows'])==12 and all(x['actual_sampled_visual_review']=='completed' for x in r['rows'])
control=json.loads((run/'CONTROL_EVIDENCE_EXECUTION.json').read_text());assert control['stage']=='complete' and all(x['returncode']==0 for x in control['rows'])
expected=set()
for x in r['rows']:
 ep=run/('case_'+x['episode'].split('_')[1])/x['episode'];assert sha(ep/'raw.npz')==x['raw_sha256'] and sha(ep/'REVIEW_EVEN.jpg')==x['review_sheet_sha256']
 assert json.loads((ep/'CONTACT_NORMAL_LIVE_AUDIT.json').read_text())['summary']['recording_and_mapping_passed']
 assert json.loads((ep/'TERMINAL_HOLD_LIVE_AUDIT.json').read_text())['recorded_hold_checks_passed']
 assert json.loads((ep/'TERMINAL_HOLD_INPUT_AUDIT.json').read_text())['summary']['passed']
 assert json.loads((ep/'CONTACT_STABILITY_CONTROL_AUDIT.json').read_text())['control_checks_passed']
 scripts=['audit_contact_normal_live.py','audit_terminal_hold_live.py','audit_terminal_hold_inputs.py','audit_contact_stability_control.py']
 if (ep/'contact_center_calibration.json').exists():
  assert json.loads((ep/'CONTACT_CENTER_LIVE_AUDIT.json').read_text())['passed']
  assert json.loads((ep/'PROJECTED_SUPPORT_LIVE_AUDIT.json').read_text())['summary']['mapping_passed']
  scripts+=['audit_contact_center_live.py','audit_projected_support_live.py']
 expected|={(ep.name,s) for s in scripts}
assert {(x['episode'],x['script']) for x in control['rows']}==expected and len(control['rows'])==len(expected)
m=json.loads((stage/'MANIFEST.json').read_text());checks=json.loads((stage/'WIRING_CHECK.json').read_text());fixture=json.loads((stage/'AUDITOR_FIXTURE_CHECK.json').read_text())
assert m['parent_protocol_sha256']==sha(run/'PROTOCOL.json') and checks['candidate_sha256']==fixture['candidate_sha256']==m['candidate_sha256']
assert len(checks['cli'])==7 and checks['pure_tests_run']==6 and len(checks['actual_transition_ast'])==2
assert checks['checker_sha256']==sha(root/'check_staged_bounded_top_lead.py')
assert fixture['auditor_sha256']==sha(root/'audit_bounded_top_lead_live.py') and fixture['checker_sha256']==sha(root/'check_bounded_lead_auditor.py')
assert len(fixture['rows'])==3 and all(x['fixture_positive_passed'] and x['negative_rejected'] for x in fixture['rows'])
for p,h in m['source_sha256'].items():assert sha(p)==h,p
for n,h in m['candidate_sha256'].items():assert sha(stage/n)==h,n
protocol_path=repo/'simfoundry/data/waist_pilot_protocol.py';text=protocol_path.read_text();needle="'simfoundry/data/contact_center_calibration.py'}";assert text.count(needle)==1;text=text.replace(needle,"'simfoundry/data/contact_center_calibration.py', 'simfoundry/data/bounded_top_lead.py'}")
backup=root/'before_bounded_top_lead';backup.mkdir(exist_ok=False);changes=[]
for name,h in m['candidate_sha256'].items():
 dst=repo/('scripts' if name=='collect_paired_sorting.py' else 'simfoundry/data')/name
 if dst.exists():shutil.copy2(dst,backup/name)
 shutil.copy2(stage/name,dst);assert sha(dst)==h;changes.append(dict(path=str(dst),sha256=h))
shutil.copy2(protocol_path,backup/protocol_path.name);protocol_path.write_text(text);changes.append(dict(path=str(protocol_path),sha256=sha(protocol_path)))
(root/'BOUNDED_TOP_LEAD_INTEGRATION.json').write_text(json.dumps(dict(changes=changes,parent_protocol_sha256=sha(run/'PROTOCOL.json'),applied_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Default-off desired object-relative top lead after original guards and measured contact calibration; original Z load, direction/route, slew and gates retained. No physical result or training admission.',training_ready=False),indent=2));print('Applied default-off bounded top lead. Fresh physics pending.')
