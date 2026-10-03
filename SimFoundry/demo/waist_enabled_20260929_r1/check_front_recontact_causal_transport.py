"""Hypothetical affine transport from six bound actual recovery contexts.
No predicted readiness is actual readiness. Preserve real recovery counters,
240-command budget and original command/geometry gates. No physics or captures.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_waypoint_reconciliation';D=W/'front_bag_recontact_center_draft_r3';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_initial_center_plan import checked_scene
from front_recontact_center_tracking import propose
from audit_front_initial_center_events import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();base=json.loads((D/'STATIC_CONTEXT_PROBE.json').read_text());sources=dict(base['source_sha256'])
for name,h in sources.items():assert sha(name)==h,name
for p in [Path(__file__),D/'front_recontact_center_tracking.py',D/'TRACKING_PREPARATION.json',D/'STATIC_CONTEXT_PROBE.json',S/'causal_response_parameters.json']:sources[str(p)]=sha(p)
guard=ClearanceGuard(ROOT,S);ind=EventAudit(ROOT,S);params=json.loads((S/'causal_response_parameters.json').read_text());decay=np.asarray(params['tasks']['nudge_mailer_to_bin']['decay']);records=[]
def save(status,**kw):
 p=D/'TRANSPORT_STATUS.tmp';p.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed=len(records),**kw),indent=2));p.replace(D/'TRANSPORT_STATUS.json')
try:
 for record in base['records']:
  plan=record['planning'];s=plan['scene'];scene=RecontactScene(guard,s['side'],s['target_xyz'],s['target_quat'],s['core_size'],s['other_xyz'],s['other_quat'],s['other_size']);trials=[];save('running',run=record['run'],recontacts=record['recontacts'])
  for candidate in sorted([a for a in plan['attempts'] if a['endpoint_accepted'] and a['nominal_path']['accepted']],key=lambda a:a['objective']):
   q=np.asarray(record['actual_start']);qp=np.asarray(record['previous_q']);previous=np.asarray(record['previous_command']);waypoints=np.asarray(candidate['nominal_path']['waypoints']);endpoint=np.asarray(candidate['endpoint']);index=ready=0;events=[];accepted=False
   for tick in range(240):
    if max(abs(q-waypoints[index]))<=.003 and index<len(waypoints)-1:index+=1
    command,check=propose(enabled=True,selected=True,mode='top_cross',recontacts=record['recontacts'],observed_load_n=0.,filtered_load_n=0.,current=q,previous_q=qp,previous_command=previous,waypoint=waypoints[index],decay=decay,guard=guard,scene_check=lambda v:checked_scene(scene,v))
    event=dict(tick=tick,real_recontacts=record['recontacts'],proposal=check)
    if command is None:event.update(outcome='command_rejected');events.append(event);break
    bias=q-previous-decay*(qp-previous);predicted=(1-decay)*command+decay*q+bias;np.testing.assert_allclose(predicted,check['predicted_q'],atol=1e-12,rtol=0)
    low=np.maximum.reduce([ind.lo,q-ind.limits,previous-.055]);high=np.minimum.reduce([ind.hi,q+ind.limits,previous+.055]);assert np.all(low<=high);request=(waypoints[index]-decay*q-bias)/(1-decay);np.testing.assert_array_equal(command,np.clip(request,low,high).astype(np.float32));assert np.all(abs(command-q)<=ind.limits+2e-7) and np.max(abs(command-previous))<=.0550002 and min(ind.elbows.gap(command))>=.005-2e-7
    independent=[]
    for x in [q,command,predicted]:
     g,_=ind.geometry(x,s);assert g['accepted'];independent.append(g)
    g,detail=ind.geometry(q,s);axis=np.linalg.eigh(np.cov(ind.hand.vertices['left'].T))[1][:,0];alignment=abs(detail['rotation'][:,2]@detail['pose'][:3,:3]@axis);point=detail['point'];endpoint_close=max(abs(q-endpoint))<=.003
    predicted_ready=bool(endpoint_close and max(abs(point[:2]))<=.002+2e-7 and min(scene.core[:2]/2-abs(point[:2]))>=.01 and .004<=point[2]-scene.core[2]/2<=.01 and alignment>=.8-2e-7)
    ready=ready+1 if predicted_ready else 0;event.update(independent_geometry=independent,waypoint_index=index,predicted_ready_count=ready,predicted_lowest_local=point.tolist(),outcome='hypothetical_ready' if ready>=3 else 'command');events.append(event)
    if ready>=3:accepted=True;break
    qp,q,previous=q,predicted,command
   trials.append(dict(seed=candidate['seed'],accepted=accepted,commands=len(events),events=events))
   if accepted:break
  result=dict(run=record['run'],step=record['step'],recontacts=record['recontacts'],accepted=any(x['accepted'] for x in trials),trials=trials,predicted_capture_discarded=True);records.append(result);print(json.dumps(dict(run=result['run'],step=result['step'],recontacts=result['recontacts'],accepted=result['accepted'],trials=[dict(seed=x['seed'],accepted=x['accepted'],commands=x['commands'],reason=x['events'][-1]['proposal']['reason']) for x in trials])),flush=True)
 # Disabled and ineligible contexts must return no command before touching inputs.
 for enabled,counter in [(False,1),(True,0),(True,-1),(True,None)]:
  cmd,why=propose(enabled=enabled,selected=True,mode='top_cross',recontacts=counter,observed_load_n=0.,filtered_load_n=0.,current=None,previous_q=None,previous_command=None,waypoint=None,decay=None,guard=None,scene_check=None);assert cmd is None
 assert len(records)==6
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed_independent_arithmetic_and_geometry=True,accepted_contexts=sum(r['accepted'] for r in records),records=records,ineligible_checks=4,source_sha256=sources,simulation_started=False,collector_integrated=False,training_ready=False,limitations=['Affine response extrapolation assumes unloaded rigid object poses; future real contact/tracking can differ.','Only real measured three-frame readiness may hand control to loading in a future runtime implementation.','Task progress and whole1200-frame completion are not inferred from hypothetical transfers.'])
 with (D/'CAUSAL_TRANSPORT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
 save('complete',accepted_contexts=out['accepted_contexts'],report_sha256=sha(D/'CAUSAL_TRANSPORT_CHECK.json'))
except Exception as e:save('failed',error=repr(e));raise
