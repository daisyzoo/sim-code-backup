"""Future contract mapping regression check; preserves frozen active contract.
The report filename is checked against actual CLI AST and verified real reports.
"""
from pathlib import Path
import ast,datetime,hashlib,json,sys
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
import front_recontact_headroom_v3_stage_run_contract as old
import front_recontact_headroom_v4_stage_run_contract as new
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();script='audit_front_recontact_headroom_stream.py';tree=ast.parse((W/script).read_text());declared=[n.right.value for n in ast.walk(tree) if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Div) and isinstance(n.right,ast.Constant) and isinstance(n.right.value,str) and n.right.value.endswith('_AUDIT.json')];assert declared==['FRONT_RECONTACT_HEADROOM_STREAM_AUDIT.json'];assert new.REPORTS[script][0]==declared[0] and old.REPORTS[script][0]!=declared[0]
assert set(old.REPORTS)==set(new.REPORTS) and all(old.REPORTS[k]==new.REPORTS[k] for k in old.REPORTS if k!=script);assert old.REPORTS[script][1]==new.REPORTS[script][1];assert old.ADDITIONAL==new.ADDITIONAL
for wait in [True,False]:assert old.primary(wait)==new.primary(wait)
r=W/'front_recontact_headroom_physical_r1';sources=[Path(__file__),W/script,W/'front_recontact_headroom_v3_stage_run_contract.py',W/'front_recontact_headroom_v4_stage_run_contract.py'];recs=[]
for task in ['push_box_to_bin','nudge_mailer_to_bin']:
 ep=r/'case_840022'/('layout_840022_'+task);p=ep/'HEADROOM_STREAM_REPORT_ROUTING_SUPPLEMENT.json';s=json.loads(p.read_text());assert s['passed'] and s['exact_native_recomputation_matches'] and s['original_failure_retained'];native=ep/new.REPORTS[script][0];assert native.is_file() and sha(native)==s['correct_report_sha256'];recs.append(dict(episode=ep.name,actual_report_matches_contract=True));sources+=[p,native]
with (W/'HEADROOM_STREAM_REPORT_ROUTING_FIX_CHECK.json').open('x') as f:json.dump(dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,actual_reports=recs,only_report_filename_changed=True,original_all_checks_and_failure_records_retained=True,source_sha256={str(p):sha(p) for p in sources},training_ready=False),f,indent=2)
print('passed real2 reports and CLI filename; old mapping rejected; inventory unchanged')
