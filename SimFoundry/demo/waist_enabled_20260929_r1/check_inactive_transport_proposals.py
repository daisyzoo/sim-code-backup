"""Independent continuous inactive-hand geometric checks of unissued proposals.
Checks straight joint interpolation with observed static parcels, not actual
tracking, dynamic collision, stationarity, or complete runtime admission.
"""
from pathlib import Path
import json,sys,hashlib,datetime,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_inactive_clearance';D=W/'inactive_transport_clearance_draft_r1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from inactive_transport_clearance import propose
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_front_recontact_center_events import RecoveryEventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());b=read(D/'TRANSPORT_PROBE.json');guard=ClearanceGuard(ROOT,S);audit=RecoveryEventAudit(ROOT,S)
for p,h in b['source_sha256'].items():assert sha(p)==h,p
radius=np.zeros(11);chain=guard.model.chains['right'];extent=np.linalg.norm(audit.hand.vertices['right'],axis=1).max()
for k,(name,_,axis) in enumerate(chain):
 if name in guard.model.names:
  assert axis is not None and abs(np.linalg.norm(axis)-1)<1e-9
  radius[guard.model.names.index(name)]=extent+sum(np.linalg.norm(O[:3,3]) for _,O,_ in chain[k+1:])
def continuous(q,end,scene):
 travel=float(radius@abs(end-q));todo=[(0.,1.,0)];leaves=[];samples=[]
 while todo:
  lo,hi,depth=todo.pop();mid=(lo+hi)/2;z=q+(end-q)*mid;pose=audit.hand.fk(z,'right');height=audit.hand.minz(z,'right');gaps=[audit.gap('right',pose,scene['target_xyz'],scene['target_quat'],scene['core_size']),audit.gap('right',pose,scene['other_xyz'],scene['other_quat'],scene['other_size'])];margin=np.r_[height-.84,np.array(gaps)-.01];lower=margin-travel*(hi-lo)/2;samples.append(dict(interval=[lo,hi],minimum_margin_m=float(min(margin)),minimum_lower_bound_m=float(min(lower))))
  if min(lower)>=-2e-7:leaves.append(float(min(lower)));continue
  if min(margin)<-2e-7 or depth>=16:return dict(passed=False,reason='violated_or_subdivision_limit',samples=samples)
  todo.extend([(lo,mid,depth+1),(mid,hi,depth+1)])
 return dict(passed=True,travel_bound_m=travel,minimum_certified_margin_m=min(leaves),samples=samples)
rows=[];negative=[]
for rr in b['records']:
 r=rr.get('record',{})
 if not r.get('applied'):continue
 q=np.array(r['current']);u=np.array(r['command']);parent=np.array(r['parent_command']);pred=np.array(r['predicted_q']);a=np.array(r['decay']);bias=np.array(r['causal_bias']);scene=r['scene']
 assert np.array_equal(u[:6],parent[:6]);np.testing.assert_allclose(audit.hand.fk(u,'left'),audit.hand.fk(parent,'left'),rtol=0,atol=0)
 pp=(1-a)*parent+a*q+bias;np.testing.assert_array_equal(pp[:6],pred[:6]);paths={kind:continuous(q,end,scene) for kind,end in [('nominal',u),('predicted',pred)]};assert all(p['passed'] for p in paths.values())
 rows.append(dict(run=rr['run'],step=rr['step'],active_nominal_transform_exactly_unchanged=True,active_predicted_q_exactly_unchanged=True,continuous_static_inactive_paths=paths))
 if len(rows)==1:
  ep=W/rr['run']/'case_840023/layout_840023_nudge_mailer_to_bin';coords={v['step']:v for v in read(ep/'coordination.json')};a0=coords[rr['step']]['task_inputs'];sceneobj=RecontactScene(guard,scene['side'],scene['target_xyz'],scene['target_quat'],scene['core_size'],scene['other_xyz'],scene['other_quat'],scene['other_size'])
  kw=dict(enabled=True,selected=True,mode=rr['mode'],guard_stop=False,scene=sceneobj,current=q,previous_q=r['previous_q'],previous_command=r['previous_command'],parent_command=parent,decay=r['decay'],task_inputs=a0)
  for label,changes in [('disabled',dict(enabled=False)),('not_selected',dict(selected=False)),('wrong_phase',dict(mode='wait')),('parent_stop',dict(guard_stop=True)),('already_lost_floor',dict(current=np.array(read(W/'front_inactive_clearance_physical_r1/INACTIVE_CLEARANCE_LOSS_TIMING.json')['rows'][321-292]['step'])*np.ones(11)))]:
   if label=='already_lost_floor':
    with np.load(ep/'raw.npz') as z:changes=dict(current=z['q'][321,12:23])
   out,meta=propose(**dict(kw,**changes));assert out is None and not meta['applied'];negative.append(dict(case=label,reason=meta['reason']))
  for label in ['stale_current','stale_previous','nonfinite_state','invalid_decay','nonfloat32_parent']:
   bad=copy.deepcopy(kw)
   if label.startswith('stale_'):bad['task_inputs']['current' if label=='stale_current' else 'previous'][0]+=.01
   elif label=='nonfinite_state':bad['current'][6]=np.nan
   elif label=='invalid_decay':bad['decay'][6]=1.
   else:bad['parent_command'][6]+=1e-10
   try:propose(**bad)
   except ValueError:negative.append(dict(case=label,rejected=True))
   else:raise AssertionError('Bad proposal context accepted '+label)
assert len(rows)==6 and len(negative)==10
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,records=rows,negative_cases=negative,source_sha256={str(p):sha(p) for p in [Path(__file__),D/'TRANSPORT_PROBE.json',D/'inactive_transport_clearance.py',W/'audit_front_recontact_center_events.py']},remaining=['Full independent original joint bounds/elbow/path/solver optimality and event admission','Actual collector/final-command/source/audit integration','Measured closed-loop physical comparison and entire-episode quality'],physics_started=False,training_ready=False)
with (D/'INDEPENDENT_PROPOSAL_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,contexts=len(rows),negative=len(negative),continuous_static_paths=2*len(rows))))
