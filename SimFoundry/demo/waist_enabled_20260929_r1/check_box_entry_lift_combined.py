"""Unwired lift+center lifecycle replay from all13 actual blocked starts.
Calibrated synthetic response only; independent lift evidence from52-plant
check and independent original center event audit. Enforce original1200 end.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_box_center_preference';sys.path[:0]=[str(stage),str(w),str(repo)]
from box_entry_lift_recontact import RecontactLifecycle
from minimum_motion_lifecycle import RecontactLifecycle as Original
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_box_center_preference_events import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();p=w/'BOX_ENTRY_LIFT_TRACKING_CHECK.json';d=json.loads(p.read_text());assert d['complete'] and d['passed'] and len(d['rows'])==52
for path,h in d['source_sha256'].items():assert sha(path)==h,path
out=w/'BOX_ENTRY_LIFT_COMBINED_CHECK.json';assert not out.exists();guard=ClearanceGuard(repo,stage);results=[];sources={str(p):sha(p)}
def save(complete):
 for f in [Path(__file__),w/'box_entry_lift_recontact.py',w/'box_recovery_entry_lift.py',w/'audit_box_center_preference_events.py',w/'audit_box_center_preference_plan.py',w/'audit_slow_drag_plan.py',w/'audit_recontact_pose_events.py',*stage.glob('*.py'),stage/'elbow_torso_hulls.json']:sources[str(f)]=sha(f)
 out.write_text(json.dumps(dict(scope=__doc__,complete=complete,all_completed_within_budget=bool(complete and all(x['completed'] for x in results)),rows=results,source_sha256=sources,physical_validation=False,training_ready=False),indent=2))
for liftproof in [r for r in d['rows'] if r['plant']=='calibrated']:
 ep=w/liftproof['run']/'case_840001/layout_840001_push_box_to_bin';events=json.loads((ep/'recontact_pose.json').read_text())['rows'];e=next(e for e in events if e['step']==liftproof['start_step']);ctx=e['context'];q0=np.array(ctx['current']);qp0=np.array(ctx['previous_q']);prev0=np.array(ctx['previous_command']);scene=RecontactScene(guard,**ctx['scene']);fr=json.loads((ep/'frontal_bypass.json').read_text());a=np.array(fr['plan']['region_causal_response']['decay']);b=q0-prev0-a*(qp0-prev0);starts=[v for v in events if v.get('planning')];seed=(starts[0]['step'],np.array(starts[0]['context']['current']));base=dict(ctx,scene=scene,decay=a)
 plain=Original(enabled=True,prefer_interior=True,box_center_preference=True);default=RecontactLifecycle(enabled=True,prefer_interior=True,box_center_preference=True);assert plain.update(**base)==default.update(**base)
 state=RecontactLifecycle(enabled=True,prefer_interior=True,box_center_preference=True,entry_lift=True);state.earliest_seed=seed;auditor=EventAudit(repo,stage);q=q0.copy();qp=qp0.copy();prev=prev0.copy();trace=[];independent=[];lift_ticks=0;budget_neg=[];finished=False
 for k in range(245):
  t=ctx['step']+k
  if t>=1200:trace.append(dict(kind='original_episode_budget_exhausted',step=t));break
  inputs=dict(base,step=t,parent_mode=ctx['parent_mode'] if k==0 else 'top_cross',current=q,previous_q=qp,previous_command=prev,observed_hand_pose=guard.model.fk('right',q)[0],observed_inactive_hand_pose=guard.model.fk('left',q)[0]);ev=state.update(**inputs);trace.append(ev)
  if ev['kind'] not in ('command','handover'):break
  assert ev['recovery_total_ticks']==k+1<=240
  if ev.get('entry_lift_phase'):
   proof=copy.deepcopy(ev);proof['kind']=proof.pop('entry_lift_phase');proof.pop('recovery_total_ticks')
   expected=copy.deepcopy(liftproof['trace'][lift_ticks])
   # Original adapter explicitly holds top_cross after any recovery command.
   # Standalone lift test kept initial top_descend; both are eligible. Only
   # this declared context label differs; compare every numeric field exactly.
   assert expected['context']['parent_mode'] in ('top_cross','top_descend')
   expected['context']['parent_mode']=inputs['parent_mode']
   assert proof==expected;lift_ticks+=1
   if lift_ticks==1 or ev['entry_lift_phase']=='lift_ready':
    capped=copy.deepcopy(state);capped.total_ticks=240;bad=capped.update(**inputs);assert bad['kind']=='stop' and bad['reason']=='combined_recovery_budget_exhausted';budget_neg.append('active' if lift_ticks==1 else 'phase_boundary')
  else:
   audited=auditor.verify(ev,**{n:inputs[n] for n in ['step','current','previous_q','previous_command','decay','selected','parent_mode','recontacts','guard_stop','observed_load_n','filtered_load_n']},scene=scene.record(),final_command=ev['command']);independent.append(audited)
  if ev['kind']=='handover':finished=True;break
  u=np.array(ev['command']);newq=(1-a)*u+a*q+b;geometry,_=auditor.geometry(newq,scene.record())
  if not geometry['accepted']:trace.append(dict(kind='synthetic_measured_geometry_rejected',geometry=geometry));break
  qp=q;q=newq;prev=u
 row=dict(run=liftproof['run'],start_step=ctx['step'],recontacts=ctx['recontacts'],completed=finished,lift_ticks=lift_ticks,total_ticks=state.total_ticks,final_step=ctx['step']+len(trace)-1,final_kind=trace[-1]['kind'],final_reason=trace[-1].get('reason'),budget_negative_cases=budget_neg,independent_normal_events=len(independent),trace=trace)
 results.append(row);save(False);print({n:v for n,v in row.items() if n!='trace'},flush=True)
assert len(results)==13;save(True);print('COMPLETE13',sum(x['completed'] for x in results),flush=True)
