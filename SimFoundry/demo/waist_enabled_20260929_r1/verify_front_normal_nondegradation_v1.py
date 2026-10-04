"""Independent original-threshold numerical review of all proposed commands."""
from pathlib import Path
import datetime,hashlib,json,sys,time
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_normal_nondegradation_audit_r1';D.mkdir(exist_ok=False);sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from audit_front_exact_normal_planning_v1 import verify
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=W/'front_normal_nondegradation_probe_r1/RESULT.json';report=read(source);ep=W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin';cs={c['step']:c for c in read(ep/'coordination.json')};g=ClearanceGuard(ROOT,S);rows=[]
for r in report['rows']:
 if r['command'] is None:continue
 start=time.monotonic();cert=verify(r['command'],cs[r['step']],guard=g);row=dict(step=r['step'],certificate=cert,elapsed_s=time.monotonic()-start);rows.append(row)
 with (D/f"CONTEXT_{r['step']}.json").open('x') as f:json.dump(row,f,indent=2,allow_nan=False)
 print(json.dumps(dict(step=r['step'],passed=cert['passed'],reason=cert.get('reason'),stationarity=cert.get('certificate',{}).get('stationarity_residual'),checks=cert.get('checks'),elapsed_s=row['elapsed_s'])),flush=True)
negative=[]
for t in [1009,761]:
 c=cs[t];bad=c['joint_transport_clearance']['output_command'];cert=verify(bad,c,guard=g);assert not cert['passed'];negative.append(dict(step=t,case='actual_original_cross_track_reversal',certificate=cert))
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,contexts=len(rows),passed=sum(r['certificate']['passed'] for r in rows),negative_cases=negative,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_front_exact_normal_planning_v1.py',source,ep/'coordination.json']},training_ready=False,physics_started=False,limitations=['Independent static numerical feasibility and stationarity only, no dynamic contact proof.','Original1e-6stationarity and2e-7primal tolerances unchanged.','Explicit new exact normal interval and relative prediction bound; not the old parent-Z-equality certificate.','Original observed34contexts include2unloaded cases without proposals; completeness of full policy not established.'])
with (D/'RESULT.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
print(json.dumps(dict(contexts=result['contexts'],passed=result['passed'],negative_cases=len(negative))),flush=True)
