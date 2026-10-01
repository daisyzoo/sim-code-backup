"""Independent audit of all lifecycle synthetic traces and deliberate corruptions.
First states bind archived physical inputs; later q belongs to a declared
synthetic response plant, not a physical episode or training sample.
"""
from pathlib import Path
import sys,json,hashlib,copy
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_recontact_pose_events import EventAudit
from audit_unloaded_wrist_prior_live import near
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
stage=w/'staged_recontact_pose';fixture=w/'staged_recontact_pose_probe/LIFECYCLE_CHECK.json';d=json.loads(fixture.read_text());results=[];first=None;last=None
for case in d['rows']:
 ep=w/'unloaded_wrist_prior_groups_r1'/('case_'+case['episode'].split('_')[1])/case['episode']
 for name,h in case['source_sha256'].items():assert sha(ep/name)==h
 with np.load(ep/'raw.npz') as z:q0=z['q'][case['step'],12:23].astype(float);qp0=z['q'][case['step']-1,12:23].astype(float);prev0=z['action'][case['step']-1,12:23].astype(float)
 fr=json.loads((ep/'frontal_bypass.json').read_text());a=np.array(fr['plan']['region_causal_response']['decay']);side='right' if 'push_box' in case['episode'] else 'left';target='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box'
 with np.load(ep/'trace.npz') as z:xyz=z[target][case['step']].astype(float);oxyz=z[other][case['step']].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[target][case['step']].astype(float);oquat=z[other][case['step']].astype(float)
 scene=dict(side=side,target_xyz=xyz.tolist(),target_quat=quat.tolist(),core_size=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'],other_xyz=oxyz.tolist(),other_quat=oquat.tolist(),other_size=[.15,.145,.04] if other=='mailer' else [.14,.09,.045])
 row=next(r for r in fr['rows'] if r['step']==case['step']);bias=q0-prev0-a*(qp0-prev0)
 for plant in case['plants']:
  audit=EventAudit(repo,stage);q=q0.copy();qp=qp0.copy();prev=prev0.copy();records=[]
  for k,event in enumerate(plant['trace']):
   args=dict(step=case['step']+k,current=q,previous_q=qp,previous_command=prev,final_command=np.array(event['command']),scene=scene,decay=a,selected=True,parent_mode='top_cross',recontacts=row['recontacts'],guard_stop=False,observed_load_n=0.,filtered_load_n=0.)
   if first is None:first=(copy.deepcopy(audit),copy.deepcopy(event),copy.deepcopy(args))
   if event['kind']=='handover' and last is None:last=(copy.deepcopy(audit),copy.deepcopy(event),copy.deepcopy(args))
   records.append(audit.verify(event,**args))
   if event['kind']=='handover':break
   name=plant['summary']['plant'];response=np.clip(a+(.06 if name=='slower_decay' else -.06 if name=='faster_decay' else 0),0,.95);local_bias=bias+(np.sin(k*.12)*np.array([.0001]+[.0003]*10) if name=='varying_bias' else 0)
   following=(1-response)*args['final_command']+response*q+local_bias;qp=q;q=following;prev=args['final_command']
  assert records[-1]['kind']=='handover' and len(records)==len(plant['trace'])
  results.append(dict(episode=case['episode'],start=case['step'],plant=plant['summary']['plant'],events=len(records),passed=True));print(results[-1],flush=True)
negative=[]
mutations={
 'false_load':lambda e:e['context'].__setitem__('observed_load_n',.01),
 'false_scene':lambda e:e['context']['scene']['target_xyz'].__setitem__(0,e['context']['scene']['target_xyz'][0]+.003),
 'false_pose':lambda e:e['context']['observed_hand_pose'][0].__setitem__(3,0.),
 'false_previous_action':lambda e:e['proposal']['previous_command'].__setitem__(1,0.),
 'false_bias':lambda e:e['proposal']['causal_bias'].__setitem__(1,.1),
 'false_requested':lambda e:e['proposal']['requested_command'].__setitem__(2,0.),
 'false_predicted':lambda e:e['proposal']['predicted_q'].__setitem__(1,0.),
 'false_command':lambda e:e['command'].__setitem__(1,0.),
 'false_geometry_gap':lambda e:e['proposal']['nominal_scene']['hand_parcel_gaps_m'].__setitem__('active_other',1.),
 'false_elbow_gap':lambda e:e['proposal']['predicted_scene'].__setitem__('elbow_gap_m',1.),
 'false_acceptance':lambda e:e['proposal']['predicted_scene'].__setitem__('accepted',False),
 'false_endpoint':lambda e:e['planning']['endpoint'].__setitem__(1,0.),
 'false_waypoint':lambda e:e['planning']['waypoints'][0].__setitem__(1,0.),
 'false_counter':lambda e:e.__setitem__('ticks',9),
 'early_handover':lambda e:e.__setitem__('kind','handover'),
}
for name,mutate in mutations.items():
 audit,event,args=copy.deepcopy(first);mutate(event)
 try:audit.verify(event,**args)
 except (AssertionError,ValueError):negative.append(name)
 else:raise AssertionError('Accepted corruption '+name)
for key in ['captured_center_local','captured_normal_local_up','captured_inactive_anchor_world','observed_support_xyz','selected_surface_local_xy']:
 audit,event,args=copy.deepcopy(last);event[key][0]+=.01
 try:audit.verify(event,**args)
 except AssertionError:negative.append(key)
 else:raise AssertionError('Accepted corrupt capture '+key)
audit,event,args=copy.deepcopy(first);args['final_command'][1]+=.001
try:audit.verify(event,**args)
except AssertionError:negative.append('final_action_changed_after_proposal')
else:raise AssertionError('Accepted final action mutation')
assert len(results)==16 and sum(r['events'] for r in results)==1768
report=dict(passed=True,scope=__doc__,rows=results,event_count=1768,handovers=16,rejected_corruptions=negative,fixture_sha256=sha(fixture),source_sha256={str(p):sha(p) for p in [Path(__file__),w/'audit_recontact_pose_events.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',repo/'assets/robots/g1_hand_support_vertices.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'simfoundry/robots/g1_assets.py',repo/'simfoundry/calibration/sorting_station.py',stage/'elbow_torso_hulls.json']},physical_validation=False,training_ready=False)
(stage/'INDEPENDENT_EVENTS_CHECK.json').write_text(json.dumps(report,indent=2));print('PASS',report['event_count'],len(negative),flush=True)
