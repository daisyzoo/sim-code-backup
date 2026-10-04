"""Entire isolated lifecycle under its causal hypothesis, not a physical rollout.
Starts at two real measured contexts. Every subsequent state is synthetic;
all reference captures are discarded and no training data is produced.
"""
from pathlib import Path
import sys,json,datetime,hashlib,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_headroom';D=W/'inactive_hand_headroom_draft_r1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from inactive_clearance_lifecycle import InactiveClearanceLifecycle
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_front_initial_center_planning_v2 import SelectionAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();bound=D/'LIFECYCLE_CHECK.json';bd=json.loads(bound.read_text());assert bd['passed']
for f,h in bd['source_sha256'].items():assert sha(f)==h
origin=W/'front_recontact_headroom_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin/front_recontact_center.json';rows=json.loads(origin.read_text())['rows'];guard=ClearanceGuard(ROOT,S);audit=SelectionAudit(ROOT,S);results=[]
for t in [405,528]:
 c=copy.deepcopy(next(r['context'] for r in rows if r['step']==t));ss=c.pop('scene');scene=RecontactScene(guard,ss['side'],ss['target_xyz'],ss['target_quat'],ss['core_size'],ss['other_xyz'],ss['other_quat'],ss['other_size']);c['scene']=scene
 life=InactiveClearanceLifecycle(recontact_index=c['recontacts'],enabled=True);events=[];independent=[]
 for j in range(241):
  e=life.update(**c);events.append(e)
  geo,_=audit.geometry(c['current'],ss);assert geo['accepted'];independent.append(geo)
  if e['kind'] not in ('command','handover'):raise AssertionError(('unexpected',t,j,e['kind'],e.get('reason')))
  q,qp,prev,a=[np.asarray(c[k],float) for k in ['current','previous_q','previous_command','decay']];u=np.asarray(e['command'],float);assert np.max(abs(u-prev))<=.0550002;assert np.all(abs(u-q)<=guard.limits+2e-7)
  if e['kind']=='handover':
   assert e['measured_ready_count']>=3 and life.finished and not life.active and life.ticks<=240;break
  b=q-prev-a*(qp-prev);pred=(1-a)*u+a*q+b;np.testing.assert_allclose(pred,e['proposal']['predicted_q'],atol=1e-12,rtol=0)
  for point in [u,pred]:
   geo,_=audit.geometry(point,ss);assert geo['accepted'];independent.append(geo)
  c.update(step=c['step']+1,parent_mode='top_cross',current=pred,previous_q=q,previous_command=u,observed_hand_pose=guard.model.fk('left',pred)[0],observed_inactive_hand_pose=guard.model.fk('right',pred)[0])
 assert events[-1]['kind']=='handover' and life.preparation_ticks==1 and life.ticks==len(events)
 assert not any('captured_center_local' in e for e in events[:-1]);assert sum(e['kind']=='handover' for e in events)==1
 results.append(dict(original_actual_step=t,hypothetical_events=events,preparation_ticks=life.preparation_ticks,total_shared_ticks=life.ticks,hypothetical_handover_step=c['step'],independent_geometry_checks=len(independent),all_capture_discarded=True));print(t,life.ticks,'hypothetical only',flush=True)
files=[Path(__file__),bound,origin,D/'inactive_clearance_lifecycle.py',D/'inactive_clearance_proposal.py',W/'audit_front_initial_center_planning_v2.py',*S.glob('*.py')]
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,results=results,source_sha256={str(f):sha(f) for f in files},physical_evidence=False,collector_integrated=False,training_ready=False)
with (D/'FULL_HYPOTHESIS_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,total_ticks=[r['total_shared_ticks'] for r in results],physical_evidence=False)))
