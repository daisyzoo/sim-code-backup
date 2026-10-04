"""Reconstruct constraints and original IK objective on six recorded proposals."""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_inactive_clearance';D=W/'inactive_transport_clearance_draft_r1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from transport_constraint_certificate import verify
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();b=read(D/'TRANSPORT_PROBE.json');guard=ClearanceGuard(ROOT,S);rows=[];negative=[]
for p,h in b['source_sha256'].items():assert sha(p)==h,p
for rr in b['records']:
 r=rr.get('record',{})
 if not r.get('applied'):continue
 ep=W/rr['run']/'case_840023/layout_840023_nudge_mailer_to_bin';a=next(c['task_inputs'] for c in read(ep/'coordination.json') if c['step']==rr['step']);out=verify(r,a,root=ROOT,stage=S,guard=guard);rows.append(dict(run=rr['run'],step=rr['step'],check=out));print(json.dumps(dict(run=rr['run'],step=rr['step'],passed=out['passed'],reason=out.get('reason',out.get('certificate',{}).get('reason')),residual=out.get('certificate',{}).get('stationarity_residual'))),flush=True)
 if len(rows)==1:
  for label in ['changed_active','stale_task','widened_bounds','modified_bias','modified_prediction','active_task_depends_on_inactive','unrounded_output']:
   bad=copy.deepcopy(r);aa=copy.deepcopy(a)
   if label=='changed_active':bad['command'][0]=float(np.float32(bad['command'][0]+.001))
   elif label=='stale_task':aa['current'][1]+=.001
   elif label=='widened_bounds':aa['upper'][1]+=.01
   elif label=='modified_bias':bad['causal_bias'][8]+=.001
   elif label=='modified_prediction':bad['predicted_q'][8]+=.001
   elif label=='active_task_depends_on_inactive':aa['jacobian'][0][8]=.001
   else:bad['command'][8]+=1e-10
   try:z=verify(bad,aa,root=ROOT,stage=S,guard=guard);rejected=not z['passed']
   except (AssertionError,ValueError):rejected=True
   assert rejected,label;negative.append(label)
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=all(r['check']['passed'] for r in rows),records=rows,negative_cases=negative,source_sha256={str(p):sha(p) for p in [Path(__file__),D/'transport_constraint_certificate.py',D/'TRANSPORT_PROBE.json',S/'loaded_z_priority_stationarity.py',S/'loaded_z_priority_checks.py',W/'audit_front_recontact_center_events.py']},full_runtime_admission=False,training_ready=False)
with (D/'CONSTRAINT_CERTIFICATE_CHECK.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(passed=result['passed'],contexts=len(rows),negative=len(negative))))
