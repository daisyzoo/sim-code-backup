"""Replay actual stopped handover witness; no simulator or state mutation."""
from pathlib import Path
import sys,json,hashlib,datetime,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_recovery_tracking';sys.path[:0]=[str(W),str(S),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from rear_transport_feasible_retry_candidate import witness
from rear_recontact_transport_witness import witness as parent_witness
from audit_rear_transport_witness import EventAudit,verify_witness
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ep=Path(sys.argv[1]).resolve();dest=ep/'REAR_TRANSPORT_FEASIBLE_RETRY_FAILURE_CHECK.json';assert not dest.exists();source=ep/'recontact_pose.json';event=json.loads(source.read_text())['rows'][-1];assert event['kind']=='stop' and event['reason']=='measured_rear_transport_unverified';ctx=event['context'];r=ctx['scene'];guard=ClearanceGuard(ROOT,S);scene=RecontactScene(guard,r['side'],r['target_xyz'],r['target_quat'],r['core_size'],r['other_xyz'],r['other_quat'],r['other_size']);q=np.array(ctx['current']);sources={str(source):sha(source)};frozen={str(p):sha(p) for p in [Path(__file__),W/'rear_transport_feasible_retry_candidate.py',W/'rear_recontact_transport_witness.py',W/'audit_rear_transport_witness.py',S/'recontact_scene.py',S/'clearance_runtime.py']}
def save(status,**kw):
 p=dest.with_suffix('.tmp');p.write_text(json.dumps(dict(status=status,pid=os.getpid(),created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,source_sha256=sources,frozen_sha256=frozen,simulation_started=False,training_ready=False,**kw),indent=2));p.replace(dest)
try:
 save('running');parent=parent_witness(scene,q);off=witness(scene,q);assert parent==off;assert parent['solver_status']==event['witness']['solver_status']==9 and not parent['accepted'];assert np.array_equal(parent['candidate'],event['witness']['candidate'])
 enabled=witness(scene,q,retry_feasible=True);assert enabled['feasible_endpoint_retry']['attempted'];proof=verify_witness(EventAudit(ROOT,S),enabled,endpoint=q,scene=r) if enabled['accepted'] else None
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 save('complete',passed=True,default_off_identical=True,original_failure_exactly_reproduced=True,parent=parent,candidate=enabled,independent_proof=proof,remaining='If new witness passes, regress original successful/failed contexts and integrate an explicit source-bound lifecycle option before any new physical run. This is not a successful measured handover.')
 print(json.dumps(dict(original_status=parent['solver_status'],retry_accepted=enabled['accepted'],retry_status=enabled['solver_status'],independent_proof=proof),indent=2))
except BaseException as e:save('check_failed',passed=False,error=repr(e));raise
