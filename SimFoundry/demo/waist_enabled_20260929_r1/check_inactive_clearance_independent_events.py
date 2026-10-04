"""Exercise independent preparation audit with native unissued and hypothetical segments.
No physical success, raw native full-stream coverage or dataset admission claim.
"""
from pathlib import Path
import json,sys,copy,datetime,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_inactive_clearance';D=W/'inactive_hand_headroom_draft_r1';sys.path[:0]=[str(W),str(ROOT)]
from audit_inactive_clearance_events import InactivePreparationAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();native=S/'RUNTIME_JOINT_CHECK.json';hyp=D/'FULL_HYPOTHESIS_CHECK.json';a=json.loads(native.read_text());b=json.loads(hyp.read_text());assert a['passed'] and b['passed']
for bound in [a,b]:
 for p,h in bound['source_sha256'].items():assert sha(p)==h,p
checker=InactivePreparationAudit(ROOT,S);single=[];segments=[];negative=[]
for row in a['records']:
 e=row['event'];c=e['context'];args={k:c[k] for k in ['step','current','previous_q','previous_command','scene','decay']};args.update(final_command=e['command'],counter=c['recontacts'],preparation_ticks=1,total_ticks=1);single.append(checker.verify_preparation(e,**args))
 for label in ['wrong_final','changed_active','wrong_prediction','wrong_bias','missing_path_point','wrong_height','wrong_load','wrong_ticks','captured_anchor','wrong_native_alias','wrong_measured_pose']:
  bad=copy.deepcopy(e);aa=copy.deepcopy(args)
  if label=='wrong_final':aa['final_command'][0]+=.001
  elif label=='changed_active':bad['command'][0]+=.001;aa['final_command']=bad['command'];bad['proposal']['command']=bad['command']
  elif label=='wrong_prediction':bad['proposal']['predicted_q'][0]+=.001
  elif label=='wrong_bias':bad['proposal']['causal_bias'][0]+=.001
  elif label=='missing_path_point':bad['proposal']['sampled_paths']['nominal']['states'].pop()
  elif label=='wrong_height':bad['proposal']['predicted']['inactive_lowest_z_m']=.84
  elif label=='wrong_load':bad['context']['observed_load_n']=.1
  elif label=='wrong_ticks':bad['ticks']=0
  elif label=='captured_anchor':bad['captured_inactive_anchor_world']=[0,0,0]
  elif label=='wrong_native_alias':bad['proposal']['candidate_command']=[x+.001 for x in bad['command']]
  else:bad['context']['observed_inactive_hand_pose'][0][3]+=.001
  try:checker.verify_preparation(bad,**aa)
  except (AssertionError,ValueError,KeyError):negative.append(dict(step=c['step'],case=label))
  else:raise AssertionError(('corrupt preparation accepted',label))
 print(c['step'],'independent preparation passed',flush=True)
for row in b['results']:
 ev=row['hypothetical_events'];proof=checker.verify_committed_sequence(ev,ROOT,S);assert proof['combined_ticks']==row['total_shared_ticks'];segments.append(proof);print(row['original_actual_step'],'independent segment passed',proof['combined_ticks'],flush=True)
 # Early rejection fixtures avoid changing the supplied original report.
 for label in ['total_count_omits_preparation','missing_preparation','step_discontinuity','previous_command_changed']:
  bad=copy.deepcopy(ev)
  if label=='total_count_omits_preparation':bad[1]['ticks']-=1
  elif label=='missing_preparation':bad=bad[1:]
  elif label=='step_discontinuity':bad[1]['context']['step']+=1
  else:bad[1]['context']['previous_command'][0]+=.001
  try:checker.verify_committed_sequence(bad,ROOT,S)
  except (AssertionError,ValueError,KeyError):negative.append(dict(step=row['original_actual_step'],case=label))
  else:raise AssertionError(('corrupt committed segment accepted',label))
files=[Path(__file__),W/'audit_inactive_clearance_events.py',native,hyp,W/'audit_front_recontact_center_events.py',W/'audit_front_initial_center_planning_v2.py',W/'audit_front_initial_center_preflight.py']
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,actual_context_preparation=single,hypothetical_committed_segments=segments,negative_cases=negative,source_sha256={str(p):sha(p) for p in files},native_complete_stream_ready=False,physical_evidence=False,training_ready=False)
with (S/'INDEPENDENT_EVENT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,unissued_actual_contexts=len(single),hypothetical_segments=len(segments),negative=len(negative))))
