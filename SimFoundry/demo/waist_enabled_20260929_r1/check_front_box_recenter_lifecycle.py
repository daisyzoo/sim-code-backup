"""Recorded right-box recovery prefixes plus explicitly hypothetical follow-up.
Not new physical data. Every issued proposal is independently reconstructed.
"""
from pathlib import Path
import copy,sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_headroom';D=W/'front_box_recenter_draft_r1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_box_recenter_lifecycle import FrontRecontactCenterLifecycle
from audit_front_box_recenter_events import RecoveryEventAudit
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
probe=read(D/'RECENTER_WINDOW_PROBE.json');guard=ClearanceGuard(ROOT,S);decay=np.asarray(read(S/'causal_response_parameters.json')['tasks']['push_box_to_bin']['decay']);ep=W/'front_corridor_midpoint_physical_r1/case_840020/layout_840020_push_box_to_bin';original={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};records=[];negative=[]
def args(scene,q,qp,u,t,counter):return dict(step=t,selected=True,parent_mode=original[t]['mode'] if t in original else 'top_cross',recontacts=counter,guard_stop=False,observed_load_n=0.,filtered_load_n=0.,scene=scene,current=q,previous_q=qp,previous_command=u,decay=decay,observed_hand_pose=guard.model.fk('right',q)[0],observed_inactive_hand_pose=guard.model.fk('left',q)[0])
for row in probe['probes']:
 c=row['actual_context'];z=row['planning']['scene'];scene=RecontactScene(guard,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']);counter=row['counter'];start=row['step'];q,qp,u=[np.array(c[k]) for k in ['current','previous_q','previous_command']];life=FrontRecontactCenterLifecycle(recontact_index=counter,enabled=True);audit=RecoveryEventAudit(ROOT,S);events=[];proofs=[]
 for tick in range(241):
  kw=args(scene,q,qp,u,start+tick,counter);kw['parent_mode']='top_cross'
  if tick==0:
   kw['parent_mode']=original[start]['mode'];kw['filtered_load_n']=original[start]['contact_load']['filtered_vertical_load_n'];assert original[start]['contact_load']['observed_vertical_load_n']==0
  event=life.update(**kw);events.append(event)
  if event['kind'] not in ('command','handover'):break
  cmd=np.array(event['command']);checkkeys={k:kw[k] for k in ['step','current','previous_q','previous_command','decay','selected','parent_mode','recontacts','guard_stop','observed_load_n','filtered_load_n']}
  proofs.append(audit.verify(event,**checkkeys,final_command=cmd,scene=scene.record()))
  if tick==0:
   # Make next observation from the stated response hypothesis; none of these
   # arrays are actual simulator measurements after the recorded prefix.
   nextq=np.array(event['proposal']['predicted_q']);nkw=args(scene,nextq,q,cmd,start+1,counter);nkw['parent_mode']='top_cross'
   cases={'guard':dict(guard_stop=True),'observed_load':dict(observed_load_n=.1),'filtered_load':dict(filtered_load_n=.051),'phase':dict(parent_mode='top_push'),'counter':dict(recontacts=counter+1),'gap_in_observations':dict(step=start+2),'unselected':dict(selected=False)}
   moved=RecontactScene(guard,'right',np.array(z['target_xyz'])+[.003,0,0],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']);cases['object_moved']=dict(scene=moved)
   for name,changes in cases.items():
    clone=copy.deepcopy(life);bad=clone.update(**dict(nkw,**changes));assert bad['kind']=='stop',(name,bad['kind']);again=clone.update(**nkw);assert again['kind']=='stop';negative.append(dict(counter=counter,case=name,reason=bad['reason']))
   clone=copy.deepcopy(life);clone.ticks=240;assert clone.update(**nkw)['kind']=='stop';negative.append(dict(counter=counter,case='budget'))
  if event['kind']=='handover':break
  qp,q,u=q,np.array(event['proposal']['predicted_q']),cmd
 records.append(dict(counter=counter,recorded_step=start,actual_prefix_frames_used=2,subsequent_observations_hypothetical=True,outcome=events[-1]['kind'],reason=events[-1].get('reason'),events=events,independent_proofs=proofs,predicted_capture_discarded=True));print(json.dumps(dict(counter=counter,outcome=events[-1]['kind'],events=len(events),reason=events[-1].get('reason'))),flush=True)
# Disabled and loaded-before-commit behavior must not create or capture a path.
base=args(scene,np.array(c['current']),np.array(c['previous_q']),np.array(c['previous_command']),start,counter)
for name,kw in [('disabled',base),('initial_contact',dict(base,recontacts=0)),('wrong_side',dict(base,scene=RecontactScene(guard,'left',z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']))),('loaded',dict(base,observed_load_n=.1))]:
 obj=FrontRecontactCenterLifecycle(recontact_index=counter,enabled=name!='disabled');ev=obj.update(**kw);assert ev['kind']=='unchanged' and not obj.active and not obj.finished;negative.append(dict(case=name))
files=[Path(__file__),D/'RECENTER_WINDOW_PROBE.json',D/'LIFECYCLE_PREPARATION.json',ep/'frontal_bypass.json',*D.glob('*.py'),*S.glob('*.py'),S/'causal_response_parameters.json',S/'elbow_torso_hulls.json']
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,negative_cases=negative,source_sha256={str(p):sha(p) for p in files},passed=True,physical_success_proven=False,unwired=True,training_ready=False)
with (D/'LIFECYCLE_PROBE.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(passed=True,contexts=len(records),hypothetical_handovers=sum(r['outcome']=='handover' for r in records),negative=len(negative),new_physics=False)))
