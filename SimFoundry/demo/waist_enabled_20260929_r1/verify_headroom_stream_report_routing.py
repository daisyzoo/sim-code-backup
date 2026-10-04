"""Supplement the frozen runner's old-name lookup mismatch without rewriting it.
Recompute the independent native stream result, require exact saved JSON equality,
and bind original subprocess success, logs and new-name report. All original
failed rows remain untouched. Does not override any task or control failure.
"""
from pathlib import Path
import datetime,hashlib,json,sys
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_front_recontact_headroom_stream import audit
from front_recontact_headroom_v3_stage_run_contract import REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(ep):
 ep=Path(ep).resolve();run=ep.parent.parent;protocol=json.loads((run/'PROTOCOL.json').read_text());assert run.name=='front_recontact_headroom_physical_r1'
 script='audit_front_recontact_headroom_stream.py';oldname,keys=REPORTS[script];newname='FRONT_RECONTACT_HEADROOM_STREAM_AUDIT.json';assert oldname=='FRONT_RECONTACT_STREAM_AUDIT.json' and keys==('passed',)
 rows=json.loads((run/'AUDIT_STATUS.json').read_text())['rows'];matches=[r for r in rows if r['episode']==ep.name and r['script']==script];assert len(matches)==1;row=matches[0]
 assert row['process_returncode']==0 and row['returncode']==1 and row['report_passed'] is False and row['report_sha256'] is None and row['report']==oldname
 assert not (ep/oldname).exists();assert row['auditor_sha256']==sha(W/script)==protocol['frozen_files_sha256'][str(W/script)]
 assert row['raw_sha256']==sha(ep/'raw.npz') and row['log_sha256']==sha(ep/(script+'.log'))
 saved=json.loads((ep/newname).read_text());recomputed=audit(ep);assert saved==recomputed and saved['passed'] is True
 for p,h in saved['source_sha256'].items():assert sha(p)==h,p
 for p,h in saved['source_binding']['source_sha256'].items():assert sha(p)==h,p
 files=[Path(__file__),W/script,W/'front_recontact_headroom_v3_stage_run_contract.py',run/'PROTOCOL.json',ep/newname,ep/(script+'.log'),ep/'raw.npz']
 return dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=ep.name,original_audit_row=row,original_failure_retained=True,cause='Frozen run contract requested pre-headroom report filename; successful CLI wrote declared headroom filename.',correct_report=newname,correct_report_sha256=sha(ep/newname),exact_native_recomputation_matches=True,verified_commands=saved['verified_commands'],handovers=saved['handovers'],source_sha256={str(p):sha(p) for p in files},other_task_and_control_gates_unchanged=True,training_ready=False)
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=verify(ep)
 with (ep/'HEADROOM_STREAM_REPORT_ROUTING_SUPPLEMENT.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(dict(passed=True,episode=out['episode'],commands=out['verified_commands'],original_failed_row_retained=True)))
