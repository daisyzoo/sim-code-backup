"""Check complete audit inventory, native historical measurement binding and old-source rejection.
No old episode is promoted or changed. New physical data still required.
"""
from pathlib import Path
import json,hashlib,datetime,ast,importlib
from audit_terminal_margin_stage_release import verify_files
from terminal_margin_stage_source_binding import verify_trial_provenance
import terminal_margin_stage_run_contract as new
import joint_edge_stage_run_contract as old
W=Path(__file__).resolve().parent;B=W/'joint_edge_intersection_physical_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((W/'TERMINAL_MARGIN_STAGE_AUDIT_PREPARATION.json').read_text())
for r in prep['files']:
 assert sha(W/r['parent'])==r['parent_sha256'] and sha(W/r['new'])==r['new_sha256'];ast.parse((W/r['new']).read_text())
# Import only import-safe modules; remaining CLI auditors are syntax checked above.
for mod in ('audit_terminal_margin_stage_pose_live','audit_terminal_margin_stage_contract','terminal_margin_stage_audit_context','audit_terminal_margin_stage_pressure','audit_terminal_margin_stage_contacts'):importlib.import_module(mod)
rows=[]
for case in sorted(B.glob('case_*')):
 if not case.is_dir():continue
 try:verify_trial_provenance(case)
 except AssertionError:pass
 except KeyError as e:assert e.args[0]=='terminal_release_margin'
 else:raise AssertionError('old provenance accepted as new experiment')
 for ep in sorted(case.glob('layout_*')):
  if not (ep/'raw.npz').exists():continue
  wait=ep.name.endswith('wait_no_package');f=None if wait else json.loads((ep/'frontal_bypass.json').read_text())
  original=old.primary(wait)+['audit_joint_edge_stage_contacts.py','audit_joint_edge_stage_pressure.py']
  adapted=new.primary(wait)+['audit_terminal_margin_stage_contacts.py','audit_terminal_margin_stage_pressure.py']
  if f:original+=old.controls(f['plan'])+old.ADDITIONAL;adapted+=new.controls(f['plan'])+new.ADDITIONAL
  assert len(original)==len(adapted)
  for a,b in zip(original,adapted):
   assert b==a.replace('joint_edge_stage','terminal_margin_stage')
   report,keys=new.REPORTS[b];assert keys==old.REPORTS[a][1] and report in (W/b).read_text(),(b,report)
  historical=verify_files(ep,enabled=False)
  try:margin=verify_files(ep,enabled=True)
  except AssertionError:margin={'passed':False,'expected_historical_early_release_rejected':True}
  rows.append(dict(episode=str(ep),original_audits=len(set(original)),historical_measurement_check=historical,margin_on_old_history=margin,files_sha256={p.name:sha(p) for p in [ep/'raw.npz',*([ep/'trace.npz',ep/'frontal_bypass.json'] if f else [])]}))
assert len(rows)==10 and sum(r['original_audits'] for r in rows)==184
result=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,old_source_rejected=True,source_sha256={str(W/r['new']):sha(W/r['new']) for r in prep['files']},checker_sha256=sha(__file__),simulation_started=False,training_ready=False)
(W/'TERMINAL_MARGIN_STAGE_AUDIT_ADAPTER_CHECK.json').write_text(json.dumps(result,indent=2));print('passed',len(rows),'conditions',sum(r['original_audits'] for r in rows),'original audits, old-source rejected')
