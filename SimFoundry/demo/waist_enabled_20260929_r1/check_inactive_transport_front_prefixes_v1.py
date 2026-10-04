"""Causally valid selected-front prefixes ending at the first unissued correction.
Replay actual recorded q/history only while outputs remain identical. At the
first changed output, audit it and STOP: no old future state is assigned to the
new command. This is readiness evidence, not a simulated rollout or admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_inactive_transport_v2';sys.path[:0]=[str(S),str(W),str(ROOT)]
from inactive_transport_runtime import InactiveTransportRuntime
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_inactive_transport_records_v1 import TransportRecordAudit,TransportStreamAudit
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);sources={};results=[];negative=[]
for task,case,side in [('nudge_mailer_to_bin',840023,'left'),('push_box_to_bin',840020,'right')]:
 ep=W/'front_box_recenter_physical_r2'/f'case_{case}'/f'layout_{case}_{task}'
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
 with np.load(ep/'trace.npz') as z:xyz={k:z[k].copy() for k in ['box','mailer']}
 with np.load(ep/'parcel_orientation.npz') as z:quat={k:z[k].copy() for k in ['box','mailer']}
 frontal=read(ep/'frontal_bypass.json');plan=frontal['plan'];fr={r['step']:r for r in frontal['rows']};co={r['step']:r for r in read(ep/'coordination.json')};loaded=read(ep/'front_loaded_z_priority.json')['rows']
 initial=read(ep/'front_initial_center.json');recovery=read(ep/'front_recontact_center.json');capture=[r['step'] for data in [initial,recovery] for r in data['rows'] if r['kind']=='handover'];assert capture
 core=plan['front_initial_center_landing']['actual_core']['collision_core_size_xyz'];decay=read(S/'causal_response_parameters.json')['tasks'][task]['decay'];target='mailer' if side=='left' else 'box';other='box' if side=='left' else 'mailer';sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]}
 runtime=InactiveTransportRuntime(guard,ROOT,S,enabled=True);audit=TransportRecordAudit(ROOT,S,guard);stream=TransportStreamAudit(audit);terminal=None
 for t in range(len(q)):
  selected=t>=min(capture);assert loaded[t]['selected'] is selected
  scene=RecontactScene(guard,side,xyz[target][t],quat[target][t],core,xyz[other][t],quat[other][t],sizes[other]) if selected else None
  prev=np.zeros(11,dtype=np.float32) if t==0 else u[t-1];qp=None if t==0 else q[t-1];c=copy.deepcopy(co.get(t));row=fr.get(t)
  assert np.array_equal(loaded[t]['output_command'],u[t])
  kw=dict(step=t,selected=selected,side=side,row=row,coordinate=c,scene=scene,current=q[t],previous_q=qp,previous_command=prev,parent_command=u[t],decay=decay if selected else None)
  out,record=runtime.refine(**kw)
  record['collector_context']=dict(side=side,current=q[t].tolist(),previous_q=None if qp is None else qp.tolist(),previous_command=prev.tolist(),scene=None if scene is None else scene.record(),decay=decay if selected else None)
  if c is not None:c['inactive_transport_clearance']=record
  context=dict(kw,coordinate=c,scene=None if scene is None else scene.record(),final_command=out);stream.observe(record,**context)
  if t%40==0 or record['applied']:print(json.dumps(dict(task=task,step=t,selected=selected,applied=record['applied'],reason=record['reason'])),flush=True)
  if record['applied']:
   assert not np.array_equal(out,u[t]);terminal=dict(step=t,record=record,context={k:v for k,v in context.items() if k not in ['coordinate','row']});break
  assert np.array_equal(out,u[t])
 assert terminal is not None,'No verified first intervention found in recorded history'
 result=stream.finish(terminal['step']+1);assert result['applied']==1
 # An omitted or stale post-intervention history must not be accepted.
 for label in ['duplicate_last_step','original_previous_action_after_changed_output','original_previous_q_after_changed_output']:
  a=copy.deepcopy(context);r=copy.deepcopy(record)
  if label!='duplicate_last_step':
   a['step']+=1;r['step']+=1;a['previous_q']=q[t];a['previous_command']=u[t]
   if label=='original_previous_q_after_changed_output':a['previous_command']=out;a['previous_q']=q[t-1]
  try:stream.observe(r,**a)
  except (AssertionError,ValueError,KeyError):negative.append(dict(task=task,case=label,rejected=True))
  else:raise AssertionError(label)
 def serial(value):
  if isinstance(value,np.ndarray):return value.tolist()
  if isinstance(value,dict):return {k:serial(v) for k,v in value.items()}
  if isinstance(value,list):return [serial(v) for v in value]
  return value
 results.append(dict(task=task,side=side,first_capture=min(capture),first_unissued_correction=serial(terminal),actual_prefix_unchanged_until_final=True,no_future_physical_claim=True,stream=result))
 for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','front_loaded_z_priority.json','front_initial_center.json','front_recontact_center.json']:sources[str(ep/n)]=sha(ep/n)
for p in [Path(__file__),W/'audit_inactive_transport_records_v1.py',S/'COLLECTOR_PREPARATION.json',*[S/n for n in read(S/'COLLECTOR_PREPARATION.json')['stage_sha256']]]:sources[str(p)]=sha(p)
for p,h in sources.items():assert sha(p)==h
out=dict(passed=True,scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),records=results,negative_cases=negative,source_sha256=sources,recursive_post_intervention_dynamics_verified=False,physics_started=False,training_ready=False)
with (S/'FRONT_PREFIX_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,prefixes=[dict(task=r['task'],frames=r['stream']['frames'],first_correction=r['first_unissued_correction']['step']) for r in results],negative=len(negative))))
