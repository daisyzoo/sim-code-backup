"""Replay all actual unloaded recovery contexts through the stopped handover.
The recorded original plan is a declared fixture; command tracking, measured
readiness, directional witnesses and original independent event checks execute.
No new simulated state, no physical completion beyond the stopped observation.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_recovery_tracking';sys.path[:0]=[str(S),str(W),str(ROOT)]
import rear_transport_recontact_lifecycle as old_base
import rear_transport_retry_lifecycle as new_base
from rear_transport_entry_lift_lifecycle import RecontactLifecycle as Old
from rear_transport_retry_entry_lifecycle import RecontactLifecycle as New
from rear_transport_retry_plan import qualify
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_rear_transport_retry_events import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ep=Path(sys.argv[1]).resolve();dest=ep/'REAR_TRANSPORT_RETRY_LIFECYCLE_FAILURE_V2_CHECK.json';assert not dest.exists();events=json.loads((ep/'recontact_pose.json').read_text())['rows'];fr=json.loads((ep/'frontal_bypass.json').read_text());events=[e for e in events if 398<=e['step']<=529];assert events[0]['step']==398 and events[-1]['step']==529 and len(events)==132
plans={e['step']:e['planning'] for e in events if e.get('planning') and not e.get('entry_lift_phase')};assert list(plans)==[418]
old_base.plan=lambda scene,q,**kw:copy.deepcopy(plans[kw['step']])
def planned(scene,q,**kw):
 p=copy.deepcopy(plans[kw['step']]);p.pop('rear_transport_witness',None)
 return qualify(scene,q,kw['step'],p,required=kw['require_rear_transport'],retry=kw['transport_feasible_retry'])
new_base.plan=planned
guard=ClearanceGuard(ROOT,S);audit=EventAudit(ROOT,S);settings=dict(enabled=True,prefer_interior=True,box_center_preference=True,entry_lift=True);old=Old(**settings);off=New(**settings);on=New(**settings,transport_feasible_retry=True)
with np.load(ep/'raw.npz') as z:rawu=z['action'][:,12:23].astype(float)
rows=[];sources={str(ep/n):sha(ep/n) for n in ['raw.npz','recontact_pose.json','frontal_bypass.json','self_clearance.json']};frozen={str(p):sha(p) for p in [Path(__file__),W/'rear_transport_retry_plan.py',W/'rear_transport_retry_lifecycle.py',W/'rear_transport_retry_entry_lifecycle.py',W/'rear_transport_feasible_retry_candidate.py',S/'rear_transport_recontact_lifecycle.py',S/'rear_transport_entry_lift_lifecycle.py',W/'audit_rear_tracking_transport_events_v2.py',W/'audit_rear_transport_retry_events.py',W/'audit_rear_transport_retry_witness.py',W/'audit_rear_transport_witness.py']}
def clean(v):
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k!='feasible_endpoint_retry'}
 if isinstance(v,(tuple,list)):return [clean(x) for x in v]
 return v
def save(status,**kw):
 p=dest.with_suffix('.tmp');p.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,frozen_sha256=frozen,simulation_started=False,training_ready=False,**kw),indent=2));p.replace(dest)
try:
 save('running')
 for recorded in events:
  ctx=copy.deepcopy(recorded['context']);record_scene=ctx.pop('scene');scene=RecontactScene(guard,record_scene['side'],record_scene['target_xyz'],record_scene['target_quat'],record_scene['core_size'],record_scene['other_xyz'],record_scene['other_quat'],record_scene['other_size']);args=dict(ctx,scene=scene,decay=fr['plan']['region_causal_response']['decay'],require_rear_transport=True)
  before=old.update(**args);disabled=off.update(**args);enabled=on.update(**args);assert before==disabled
  if ctx['step']<529:
   assert clean(enabled)==clean(before)
   if enabled['kind'] in ['command','handover']:assert np.array_equal(enabled['command'],rawu[ctx['step']])
  else:
   assert before['kind']=='stop' and before['reason']=='measured_rear_transport_unverified' and before['witness']==recorded['witness'];assert enabled['kind']=='handover' and enabled['measured_ready_count']==3
  proof=None
  if enabled['kind'] in ['command','handover']:
   proof=audit.verify(enabled,require_rear_transport=True,transport_feasible_retry=True,step=ctx['step'],current=ctx['current'],previous_q=ctx['previous_q'],previous_command=ctx['previous_command'],final_command=enabled['command'],scene=record_scene,decay=args['decay'],selected=ctx['selected'],parent_mode=ctx['parent_mode'],recontacts=ctx['recontacts'],guard_stop=ctx['guard_stop'],observed_load_n=ctx['observed_load_n'],filtered_load_n=ctx['filtered_load_n'])
  rows.append(dict(step=ctx['step'],original_kind=before['kind'],disabled_identical=True,enabled_kind=enabled['kind'],independent_proof=proof,actual_prefix_command_identical=ctx['step']<529));
  if ctx['step']%20==0:save('running');print(ctx['step'],enabled['kind'],flush=True)
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 save('complete',passed=True,replayed_contexts=len(rows),independent_event_checks=sum(x['independent_proof'] is not None for x in rows),final_proposed_handover=enabled,remaining='Actual collector flags/source/adapters and full paired physical comparison; no 529 command was physically executed here.')
 print('verified',len(rows),'contexts; final proposed handover at529')
except BaseException as e:save('check_failed',passed=False,error=repr(e));raise
