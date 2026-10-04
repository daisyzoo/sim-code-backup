"""Independently include the newly constrained direction in the KKT system.
Original unscaled objective, finite-difference step and 1e-6 stationarity retained.
Only a two-context preliminary certificate; not source/lifecycle/path admission.
"""
from pathlib import Path
import datetime,hashlib,json,sys
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from audit_front_cross_track_nonreversal_candidate_v1 import verify
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();D=W/'front_cross_track_nonreversal_probe_r1';p=D/'RESULT.json';d=read(p);ep=W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin';co={c['step']:c for c in read(ep/'coordination.json')};g=ClearanceGuard(ROOT,S);rows=[]
for f,h in d['source_sha256'].items():assert sha(f)==h,f
for row in d['rows']:
 c=co[row['step']];cert=verify(row['proposal'],c['task_inputs'],c,guard=g,elbow_reserve_m=.0015,quarter_enabled=True);out=dict(step=row['step'],certificate=cert,original_missing_new_constraint_certificate_passed=row['original_certificate']['passed']);rows.append(out)
 print(json.dumps(dict(step=row['step'],passed=cert['passed'],checks=cert.get('checks'),stationarity=cert.get('certificate',{}).get('stationarity_residual'))),flush=True)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256={str(x):sha(x) for x in [Path(__file__),W/'audit_front_cross_track_nonreversal_candidate_v1.py',p,ep/'coordination.json']},installed=False,physics_started=False,training_ready=False,remaining=['Full defaultoff/no-request/nonlateral behavior, active support branch regularity, nonlinear paths, source/native/stream tests and rejection counterexamples before any physical run.','Do not interpret zero nominal transverse motion as successful sustained traction or actual parcel behavior.'])
encoded=json.dumps(report,indent=2)
with (D/'NEW_CONSTRAINT_CERTIFICATE_V1.json').open('x') as f:f.write(encoded)
