"""Recorded transport feasibility, not counterfactual rollout or training data."""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_inactive_clearance';D=W/'inactive_transport_clearance_draft_r1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from inactive_transport_clearance import propose
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_front_recontact_center_events import RecoveryEventAudit
from simfoundry.data.top_contact_bypass import rotation_xyzw
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);independent=RecoveryEventAudit(ROOT,S);a=np.array(read(S/'causal_response_parameters.json')['tasks']['nudge_mailer_to_bin']['decay']);rows=[];sources={}
for run,steps in [('front_inactive_clearance_physical_r1',[294,300,310,315,320,321,350]),('front_recontact_headroom_physical_r1',[300,305,310,315,320,330,350])]:
 ep=W/run/'case_840023/layout_840023_nudge_mailer_to_bin';fr={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};co={r['step']:r for r in read(ep/'coordination.json')}
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
 with np.load(ep/'trace.npz') as z:xyz=z['mailer'].copy();other=z['box'].copy()
 with np.load(ep/'parcel_orientation.npz') as z:quat=z['mailer'].copy();oq=z['box'].copy()
 for t in steps:
  f=fr[t];c=co[t]
  if not c.get('task_inputs'):rows.append(dict(run=run,step=t,skipped='non_task_joint_path'));continue
  scene=RecontactScene(guard,'left',xyz[t],quat[t],[.15,.145,.04],other[t],oq[t],[.14,.09,.045]);cmd,record=propose(enabled=True,selected=True,mode=f['mode'],guard_stop=bool(f.get('route_stop_reason')),scene=scene,current=q[t],previous_q=q[t-1],previous_command=u[t-1],parent_command=u[t],decay=a,task_inputs=c['task_inputs']);row=dict(run=run,step=t,mode=f['mode'],record=record,observed_load_n=f['contact_load']['observed_vertical_load_n'])
  if cmd is not None:
   heights=[];gaps=[]
   for z in [cmd,np.array(record['predicted_q'])]:
    heights.append(float(independent.hand.minz(z,'right')));I=independent.hand.fk(z,'right');gaps.append([independent.gap(I,'right',xyz[t],rotation_xyzw(quat[t]),np.array([.15,.145,.04])),independent.gap(I,'right',other[t],rotation_xyzw(oq[t]),np.array([.14,.09,.045]))])
   assert min(heights)>=.8415-2e-7 and np.min(gaps)>=.01-2e-7
   np.testing.assert_array_equal(cmd[:6],u[t,:6]);row['independent_nominal_predicted_height_m']=heights;row['independent_parcel_gap_m']=gaps
  rows.append(row);print(json.dumps(dict(run=run,step=t,applied=cmd is not None,reason=record['reason'],checks=record.get('checks'))),flush=True)
 for p in [ep/'raw.npz',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'frontal_bypass.json',ep/'coordination.json']:sources[str(p)]=sha(p)
for p in [Path(__file__),D/'inactive_transport_clearance.py',S/'causal_response_parameters.json',W/'audit_front_recontact_center_events.py',*S.glob('*.py')]:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=rows,source_sha256=sources,checked_contexts=len(rows),feasible_unissued=sum(r.get('record',{}).get('applied',False) for r in rows),physics_started=False,training_ready=False)
with (D/'TRANSPORT_PROBE.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(contexts=len(rows),feasible=out['feasible_unissued'])))
