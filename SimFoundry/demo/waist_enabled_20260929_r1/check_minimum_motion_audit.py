"""Independent all16 plan checks and explicit synthetic first-command events.
Synthetic candidate events are never described as new physical trajectories.
Includes corrupt-plan/command/load rejection. No original reports modified.
"""
from pathlib import Path
import json,sys,hashlib,copy
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_minimum_motion_recontact';sys.path[:0]=[str(stage),str(w),str(repo)]
from audit_minimum_motion_plan import PlanAudit
from audit_minimum_motion_events import EventAudit
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from recontact_tracking import propose
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();source=stage/'RUNTIME_PLANNER_CHECK.json';data=json.loads(source.read_text());assert data['complete'];assert all(sha(p)==h for p,h in data['source_sha256'].items());guard=ClearanceGuard(repo,stage);audit=PlanAudit(repo,stage);rows=[];fixtures=[]
for row in data['records']:
 name=row['episode'];ep=w/'precise_interior_groups_r1'/('case_'+name.split('_')[1])/name;events=json.loads((ep/'recontact_pose.json').read_text())['rows'];old=next(e for e in events if e['step']==row['step']);ctx=old['context'];q=np.array(ctx['current']);scene=RecontactScene(guard,**ctx['scene']);plan=row['plan'];proof=audit.verify_preference(plan,current=q,scene=ctx['scene'],step=row['step']);assert proof['selected']=='candidate'
 waypoints=plan['waypoints'];ix=1 if max(abs(q-np.array(waypoints[0])))<=.003 and len(waypoints)>1 else 0
 command,proposal=propose(enabled=True,selected=ctx['selected'],mode='top_cross',recontacts=ctx['recontacts'],observed_load_n=ctx['observed_load_n'],filtered_load_n=ctx['filtered_load_n'],current=q,previous_q=ctx['previous_q'],previous_command=ctx['previous_command'],waypoint=waypoints[ix],decay=old['proposal']['decay'],guard=guard,scene_check=scene.check);assert command is not None
 event=dict(kind='command',command=command.tolist(),proposal=proposal,context=copy.deepcopy(ctx),waypoint_index=ix,ticks=1,measured_ready_count=0,planning=plan)
 kwargs=dict(step=row['step'],current=q,previous_q=ctx['previous_q'],previous_command=ctx['previous_command'],final_command=command,scene=ctx['scene'],decay=old['proposal']['decay'],selected=ctx['selected'],parent_mode=ctx['parent_mode'],recontacts=ctx['recontacts'],guard_stop=ctx['guard_stop'],observed_load_n=ctx['observed_load_n'],filtered_load_n=ctx['filtered_load_n']);verified=EventAudit(repo,stage).verify(event,**kwargs);rows.append(dict(episode=name,step=row['step'],independent_plan_passed=True,synthetic_first_command_passed=True,waypoints=len(waypoints),verified=verified));fixtures.append((event,kwargs));print(name,row['step'],'independent plan and synthetic first command PASS',flush=True)
first,kwargs=fixtures[0];rejections=[]
for key in ['alignment_threshold','seed_policy','endpoint','waypoint','path_check','status','objective','minimum_constraint','parent_step','event_command','observed_load','measured_ready']:
 e=copy.deepcopy(first);kw=copy.deepcopy(kwargs);p=e['planning'];m=p['minimum_motion_pose']
 if key=='alignment_threshold':m['alignment_abs_min']=.5
 elif key=='seed_policy':m['seed_policy'][1]='future_state'
 elif key=='endpoint':p['endpoint'][1]+=.01
 elif key=='waypoint':p['waypoints'][3][1]+=.01
 elif key=='path_check':m['selected_path_checks'][0]['accepted']=False
 elif key=='status':m['endpoint_attempts'][0]['status']=9
 elif key=='objective':m['endpoint_attempts'][0]['objective']+=.01
 elif key=='minimum_constraint':m['endpoint_attempts'][0]['minimum_constraint_m']+=.01
 elif key=='parent_step':m['parent_plan']['step']+=1
 elif key=='event_command':e['command'][1]+=.01
 elif key=='observed_load':kw['observed_load_n']=.1
 elif key=='measured_ready':e['measured_ready_count']=3
 try:EventAudit(repo,stage).verify(e,**kw)
 except (AssertionError,ValueError,KeyError):rejections.append(key)
 else:raise AssertionError(('corrupt case accepted',key))
assert len(rows)==16 and len(rejections)==12
out=dict(scope=__doc__,passed=True,all16_independent_plan_checks=True,synthetic_first_command_events=16,corruption_rejections=rejections,rows=rows,physical_validation=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),source,w/'audit_minimum_motion_plan.py',w/'audit_minimum_motion_events.py',w/'audit_recontact_interior_events.py',w/'audit_recontact_pose_events.py',stage/'minimum_motion_recontact.py',stage/'recontact_tracking.py']});(stage/'INDEPENDENT_AUDIT_CHECK.json').write_text(json.dumps(out,indent=2));print('COMPLETE16/12',flush=True)
