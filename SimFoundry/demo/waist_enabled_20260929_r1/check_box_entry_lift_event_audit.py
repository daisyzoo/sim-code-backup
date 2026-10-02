"""Independent event auditor over52 saved synthetic lift traces, plus corruption rejection."""
from pathlib import Path
import sys,json,copy,hashlib,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_box_entry_lift_events import LiftAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();source=w/'BOX_ENTRY_LIFT_TRACKING_CHECK.json';d=json.loads(source.read_text());assert d['complete'] and d['passed']
for p,h in d['source_sha256'].items():assert sha(p)==h,p
stage=w/'staged_box_center_preference';rows=[];negative=[]
def kwargs(e):
 c=e['context'];return dict(step=c['step'],current=c['current'],previous_q=c['previous_q'],previous_command=c['previous_command'],final_command=e['command'],scene=c['scene'],decay=e['proposal']['decay'],selected=c['selected'],parent_mode=c['parent_mode'],recontacts=c['recontacts'],guard_stop=c['guard_stop'],observed_load_n=c['observed_load_n'],filtered_load_n=c['filtered_load_n'])
def mapped(e):
 e=copy.deepcopy(e);e['entry_lift_phase']=e['kind'];e['kind']='command';return e
for row in d['rows']:
 audit=LiftAudit(repo,stage)
 for event in row['trace']:
  e=mapped(event);audit.verify(e,**kwargs(e))
 assert not audit.active
 rows.append(dict(run=row['run'],start_step=row['start_step'],plant=row['plant'],events=len(row['trace']),passed=True))
 print(row['run'],row['start_step'],row['plant'],len(row['trace']),flush=True)
first=mapped(d['rows'][0]['trace'][0]);original_kwargs=kwargs(first)
for label,mutate in [
 ('false_ready',lambda e:e.update(entry_lift_phase='lift_ready')),
 ('false_height',lambda e:e.update(measured_lowest_world_z_m=.9)),
 ('wrong_command',lambda e:e['command'].__setitem__(0,0.)),
 ('wrong_path',lambda e:e['planning']['path']['waypoints'][0].__setitem__(0,0.)),
 ('lower_lift_goal',lambda e:e['planning']['lift'].update(height_m=.01)),
 ('missing_initial_plan',lambda e:e.update(planning=None)),
 ('wrong_counter',lambda e:e.update(ticks=40)),
 ('wrong_causal_bias',lambda e:e['proposal']['causal_bias'].__setitem__(0,10.)),
 ('undeclared_anchor_capture',lambda e:e.update(captured_center_local=[0,0,0])),
 ('false_load',lambda e:e['context'].update(observed_load_n=.1))]:
 e=copy.deepcopy(first);mutate(e)
 try:LiftAudit(repo,stage).verify(e,**original_kwargs)
 except (AssertionError,ValueError,TypeError,KeyError):negative.append(label)
 else:raise AssertionError('Corruption accepted '+label)
assert len(rows)==52 and len(negative)==10
files=[Path(__file__),source,w/'audit_box_entry_lift_events.py',w/'audit_slow_drag_plan.py',w/'audit_recontact_pose_events.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',stage/'elbow_torso_hulls.json',repo/'assets/robots/g1_hand_support_vertices.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']
out=dict(completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,rows=rows,negative_cases=negative,source_sha256={str(p):sha(p) for p in files},physical_validation=False,training_ready=False)
(w/'BOX_ENTRY_LIFT_EVENT_AUDIT_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS52 traces10bad',flush=True)
