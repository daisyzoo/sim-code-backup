"""Thirteen actual first-blocked starts x four synthetic response models.
Independent command/URDF path checks; no physical contact or subsequent
recontact completion claim. Entry lift remains unwired into the collector.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_box_center_preference';sys.path[:0]=[str(stage),str(w),str(repo)]
from box_recovery_entry_lift import EntryLift
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_slow_drag_plan import PlanAudit
from audit_unloaded_wrist_prior_live import near
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);auditor=PlanAudit(repo,stage);screen=json.loads((w/'BOX_RECOVERY_LIFT_SCREEN.json').read_text());assert screen['complete'];rows=[];sources={};out=w/'BOX_ENTRY_LIFT_TRACKING_CHECK.json';assert not out.exists()
def save(complete):
 files=[Path(__file__),w/'box_recovery_entry_lift.py',w/'BOX_RECOVERY_LIFT_SCREEN.json',w/'audit_slow_drag_plan.py',w/'audit_recontact_pose_events.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',*stage.glob('*.py'),stage/'elbow_torso_hulls.json',repo/'assets/robots/g1_hand_support_vertices.json']
 for p in files:sources[str(p)]=sha(p)
 out.write_text(json.dumps(dict(scope=__doc__,completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),complete=complete,passed=bool(complete and all(r['completed'] and len(r['guard_stops'])==8 for r in rows)),rows=rows,source_sha256=sources,physical_validation=False,training_ready=False),indent=2))
for candidate in screen['rows']:
 ep=w/candidate['run']/'case_840001/layout_840001_push_box_to_bin';events=json.loads((ep/'recontact_pose.json').read_text())['rows'];event=next(e for e in events if e['step']==candidate['step']);ctx=event['context'];q0=np.array(ctx['current']);qp0=np.array(ctx['previous_q']);prev0=np.array(ctx['previous_command']);scene=RecontactScene(guard,**ctx['scene']);fr=json.loads((ep/'frontal_bypass.json').read_text());decay=np.array(fr['plan']['region_causal_response']['decay']);bias=q0-prev0-decay*(qp0-prev0)
 for name in ['recontact_pose.json','frontal_bypass.json']:sources[str(ep/name)]=sha(ep/name)
 base=dict(ctx);base.pop('scene');base['scene']=scene;base['decay']=decay
 assert EntryLift().update(**base)['kind']=='unchanged'
 for change in [dict(selected=False),dict(recontacts=0),dict(parent_mode='top_push'),dict(parent_mode='top_press'),dict(guard_stop=True),dict(observed_load_n=.001),dict(filtered_load_n=.051)]:assert EntryLift(enabled=True).update(**dict(base,**change))['kind']=='unchanged'
 for plant in ['calibrated','slower_decay','faster_decay','varying_bias']:
  state=EntryLift(enabled=True);q=q0.copy();qp=qp0.copy();previous=prev0.copy();trace=[];negative=[];independent=[];endpoint=None;ready_count=0
  for k in range(45):
   inputs=dict(base,step=ctx['step']+k,current=q,previous_q=qp,previous_command=previous,observed_hand_pose=guard.model.fk('right',q)[0],observed_inactive_hand_pose=guard.model.fk('left',q)[0]);ev=state.update(**inputs);trace.append(ev)
   if ev['kind'] not in ['lift_command','lift_ready']:break
   if k==0:
    p=ev['planning'];assert p['accepted'];auditor.lift(p['lift'],q,p['lift']['height_m'],scene.record());auditor.checked_path(p['path'],[q,p['lift']['candidate']],scene.record());endpoint=np.array(p['lift']['candidate']);assert auditor.hand.minz(endpoint,'right')>=.84
    for change in [dict(parent_mode='top_push'),dict(guard_stop=True),dict(observed_load_n=.001),dict(filtered_load_n=.051),dict(recontacts=ctx['recontacts']+1)]:
     rejected=copy.deepcopy(state).update(**dict(inputs,**change));assert rejected['kind']=='stop' and rejected['requires_stop'];negative.append(rejected['reason'])
    moved=RecontactScene(guard,**dict(ctx['scene'],target_xyz=(np.array(ctx['scene']['target_xyz'])+[.003,0,0]).tolist()));rejected=copy.deepcopy(state).update(**dict(inputs,scene=moved));assert rejected['kind']=='stop';negative.append(rejected['reason'])
    expired=copy.deepcopy(state);expired.ticks=40;rejected=expired.update(**inputs);assert rejected['kind']=='stop';negative.append(rejected['reason'])
    rejected=copy.deepcopy(state).update(**dict(inputs,step=inputs['step']+3));assert rejected['kind']=='stop';negative.append(rejected['reason'])
   else:assert ev['planning'] is None
   pr=ev['proposal'];target=np.array(pr['waypoint']);cb=q-previous-decay*(qp-previous);requested=(target-decay*q-cb)/(1-decay);lo=np.maximum.reduce([auditor.lo,q-auditor.limits,previous-.055]);hi=np.minimum.reduce([auditor.hi,q+auditor.limits,previous+.055]);assert np.all(lo<=hi);expected=np.clip(requested,lo,hi).astype(np.float32);command=np.array(ev['command']);near(command,expected,0);predicted=(1-decay)*command+decay*q+cb;near(pr['predicted_q'],predicted,1e-10)
   assert np.max(abs(command-previous))<=.0550002 and np.all(abs(command-q)<=auditor.limits+2e-7) and min(auditor.elbows.gap(command))>=.005-2e-7
   for key,value in [('nominal_scene',command),('predicted_scene',predicted)]:
    geometry,_=auditor.geometry(value,scene.record());assert geometry['accepted'];auditor.compare_geometry(pr[key],geometry)
   measured,_=auditor.geometry(q,scene.record());assert measured['accepted'];z=auditor.hand.minz(q,'right');near(z,ev['measured_lowest_world_z_m'],1e-8);ready=bool(z>=.84 and np.max(abs(q-endpoint))<=.003 and np.all(q>=auditor.lo-2e-7) and np.all(q<=auditor.hi+2e-7));ready_count=ready_count+1 if ready else 0;assert ev['measured_ready_count']==ready_count and (ev['kind']=='lift_ready')==(ready_count>=3);independent.append(dict(step=inputs['step'],geometry_and_command_passed=True,measured_ready_count=ready_count))
   if ev['kind']=='lift_ready':break
   a=np.clip(decay+(.06 if plant=='slower_decay' else -.06 if plant=='faster_decay' else 0),0,.95);b=bias+(np.sin(k*.12)*np.array([.0001]+[.0003]*10) if plant=='varying_bias' else 0);nextq=(1-a)*command+a*q+b;g,_=auditor.geometry(nextq,scene.record())
   if not g['accepted']:trace.append(dict(kind='independent_plant_geometry_rejected',geometry=g));break
   qp=q;q=nextq;previous=command
  row=dict(run=candidate['run'],recontacts=ctx['recontacts'],start_step=ctx['step'],plant=plant,completed=trace[-1]['kind']=='lift_ready',ticks=len(trace),final_kind=trace[-1]['kind'],final_reason=trace[-1].get('reason'),ready_step=ctx['step']+len(trace)-1 if trace[-1]['kind']=='lift_ready' else None,guard_stops=negative,independent_events=independent,trace=trace)
  rows.append(row);save(False);print({k:v for k,v in row.items() if k not in ['trace','independent_events','guard_stops']},flush=True)
assert len(rows)==52;save(True);print('COMPLETE52',sum(r['completed'] for r in rows),flush=True)
