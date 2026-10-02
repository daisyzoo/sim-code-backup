"""Runtime lifecycle checks with recorded plans and actual measured handovers.
Recorded plans are explicit fixtures to isolate lifecycle behavior; the endpoint
witness and path-command tracker execute normally. No counterfactual physics.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_peak_load_guard';sys.path[:0]=[str(S),str(W),str(ROOT)]
import minimum_motion_lifecycle as original
import rear_transport_recontact_lifecycle as candidate
from rear_recontact_transport_witness import filter_plan
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);inputs=json.loads((W/'REAR_CORRIDOR_LOSS_FINDINGS.json').read_text());dest=W/'REAR_TRANSPORT_LIFECYCLE_CHECK.json';assert not dest.exists();rows=[];sources={};negative=[]
def scene_of(d):return RecontactScene(guard,d['side'],d['target_xyz'],d['target_quat'],d['core_size'],d['other_xyz'],d['other_quat'],d['other_size'])
def save(status,**kw):
 tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,negative_checks=negative,training_ready=False,**kw),indent=2));tmp.replace(dest)
try:
 save('running')
 for item in inputs['episodes']:
  ep=W/item['episode'];fr=json.loads((ep/'frontal_bypass.json').read_text());events=json.loads((ep/'recontact_pose.json').read_text())['rows'];last_plan=None;last_scene=None
  for name in ['frontal_bypass.json','recontact_pose.json']:sources[str(ep/name)]=sha(ep/name)
  for event in events:
   if event.get('entry_lift_phase'):continue
   planning=event.get('planning');handover=event['kind']=='handover'
   if planning and planning['accepted']:last_plan=planning;last_scene=scene_of(event['context']['scene'])
   if not planning and not handover:continue
   context=copy.deepcopy(event['context']);scene=scene_of(context.pop('scene'));args=dict(context,scene=scene,decay=fr['plan']['region_causal_response']['decay']);required=bool(scene.side=='right')
   # Fixture supplies the same recorded original plan to both lifecycle versions.
   original.plan=lambda *a,_plan=planning,**k:copy.deepcopy(_plan)
   candidate.plan=lambda scene,q,_plan=planning,**k:filter_plan(scene,q,k['step'],copy.deepcopy(_plan),enabled=k.pop('require_rear_transport',False))
   states=[]
   for cls in [original.RecontactLifecycle,candidate.RecontactLifecycle,candidate.RecontactLifecycle]:
    state=cls(enabled=True,prefer_interior=True,box_center_preference=scene.side=='right')
    if handover:
     assert last_plan is not None;state.active=True;state.attempted=context['recontacts'];state.index=len(last_plan['waypoints'])-1;state.ticks=event['ticks']-1;state.ready=2;state.plan=copy.deepcopy(last_plan);state.scene=last_scene
     if cls is candidate.RecontactLifecycle:state.require_rear_transport=len(states)==2
    states.append(state)
   old=states[0].update(**args);off=states[1].update(**args,require_rear_transport=False);assert old==off,(ep.name,context['step'],'disabled lifecycle differs')
   on=states[2].update(**args,require_rear_transport=True)
   if handover:assert old['kind']=='handover'
   if on['kind']=='handover':assert on['rear_transport_handover_witness']['accepted'] and on['observed_support_xyz']==old['observed_support_xyz']
   if planning and not planning['accepted']:assert on['kind']=='stop' and on['reason']=='rear_transport_recontact_unverified'
   rows.append(dict(episode=item['episode'],step=context['step'],case='actual_measured_handover' if handover else 'recorded_plan_event',original_kind=old['kind'],default_off_equal=True,enabled_kind=on['kind'],enabled_reason=on.get('reason'),measured_witness=on.get('rear_transport_handover_witness'),planning_witness=on.get('planning',{}).get('rear_transport_witness') if on.get('planning') else None))
   if not negative:
    bad=candidate.RecontactLifecycle(enabled=True,prefer_interior=True,box_center_preference=scene.side=='right')
    try:bad.update(**args,require_rear_transport=1)
    except ValueError:negative.append('non_boolean_transport_requirement_rejected')
    else:raise AssertionError('Invalid flag accepted')
   save('running')
 for m in list(sys.modules.values()):
  p=getattr(m,'__file__',None)
  if p and str(ROOT) in str(p) and str(p).endswith('.py') and Path(p).exists():sources[str(Path(p).resolve())]=sha(p)
 sources[str(Path(__file__).resolve())]=sha(__file__)
 save('complete',planning_events=sum(r['case']=='recorded_plan_event' for r in rows),actual_handover_events=sum(r['case']=='actual_measured_handover' for r in rows),enabled_stops=sum(r['enabled_kind']=='stop' for r in rows))
except Exception as e:save('check_failed',error=repr(e));raise
