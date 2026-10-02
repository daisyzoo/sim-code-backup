"""Real initial observations + explicitly synthetic affine/measurement fixtures.
No simulator is run. Nominal geometry and lifecycle evidence are separate from
physical tracking/contact COP and never authorize training admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy,os
from unittest.mock import patch
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_terminal_release_margin'
sys.path[:0]=[str(W),str(S),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_minimum_motion_plan_reentrant import PlanAudit
from front_initial_center_plan import plan
from front_initial_center_lifecycle_v2 import FrontInitialCenterLifecycle
from front_initial_center_tracking import propose
from recontact_tracking import propose as parent_propose
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
output=W/'FRONT_INITIAL_CENTER_LIFECYCLE_V2_CHECK.json';assert not output.exists()
guard=ClearanceGuard(ROOT,S);ind=PlanAudit(ROOT,S)
probe=json.loads((W/'FRONT_INITIAL_CENTER_LANDING_PROBE.json').read_text())
base_path=W/'FRONT_INITIAL_CENTER_LIFECYCLE_CHECK.json';base=json.loads(base_path.read_text());assert base['status']=='complete'
assert base['source_sha256'][str(W/'front_initial_center_plan.py')]==sha(W/'front_initial_center_plan.py')
plans={r['episode']:r['planning'] for r in base['records']}
params=json.loads((S/'causal_response_parameters.json').read_text())
report=dict(status='running',pid=os.getpid(),scope=__doc__,records=[],fixtures=[],training_ready=False,collector_integrated=False,simulation_started=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'front_initial_center_plan.py',W/'front_initial_center_lifecycle_v2.py',W/'front_initial_center_tracking.py',W/'FRONT_INITIAL_CENTER_LANDING_PROBE.json',S/'causal_response_parameters.json',S/'recontact_tracking.py',S/'minimum_motion_recontact.py',S/'recontact_scene.py',S/'clearance_runtime.py',W/'audit_minimum_motion_plan_reentrant.py']})
report['source_sha256'].update(guard.model.source_sha256)
report['source_sha256'][str(base_path)]=sha(base_path)
report['numerical_fix']='Apply original solver geometric tolerance 2e-7 to new center/alignment readiness only; all task gates, force, original geometry, consecutive3 and240 ticks unchanged.'
def save():
 report['updated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();tmp=output.with_suffix('.tmp');tmp.write_text(json.dumps(report,indent=2));tmp.replace(output)
def scene_from(d):
 return RecontactScene(guard,d['side'],d['target_xyz'],d['target_quat'],d['core_size'],d['other_xyz'],d['other_quat'],d['other_size'])
def context(scene,q,qp,prev,decay,t):
 return dict(step=t,selected=True,parent_mode='top_cross',recontacts=0,guard_stop=False,observed_load_n=0.,filtered_load_n=0.,scene=scene,current=q,previous_q=qp,previous_command=prev,decay=decay,observed_hand_pose=guard.model.fk(scene.side,q)[0],observed_inactive_hand_pose=guard.model.fk(scene.inactive,q)[0])
def verify_command(event,scene):
 r=event['proposal'];q,qp,prev,target,a=[np.asarray(r[k]) for k in ['current','previous_q','previous_command','waypoint','decay']]
 bias=q-prev-a*(qp-prev);request=(target-a*q-bias)/(1-a)
 lo=np.maximum.reduce([guard.lower,q-guard.limits,prev-.055]);hi=np.minimum.reduce([guard.upper,q+guard.limits,prev+.055])
 command=np.clip(request,lo,hi).astype(np.float32);pred=(1-a)*command+a*q+bias
 assert np.array_equal(command,np.array(event['command'],dtype=np.float32))
 assert np.max(abs(pred-np.array(r['predicted_q'])))<1e-12
 for state in [q,command,pred]:
  check,_=ind.geometry(state,scene.record());assert check['accepted'] and check['elbow_gap_m']>=.005-2e-7
 assert np.all(abs(command-q)<=guard.limits+2e-7) and np.max(abs(command-prev))<=.0550002
 return pred
try:
 save()
 for prior in probe['records']:
  ep=next((W/'fresh_closed_peak_trials_r1').glob('case_*/'+prior['episode']));t=prior['step'];q=np.array(prior['actual_start_q']);scene=scene_from(prior['scene'])
  with np.load(ep/'raw.npz') as z:qp=z['q'][t-1,12:23].astype(float);previous=z['action'][t-1,12:23].astype(float)
  task='push_box_to_bin' if scene.side=='right' else 'nudge_mailer_to_bin';decay=np.array(params['tasks'][task]['decay'])
  record=dict(episode=ep.name,step=t,original_task_passed=prior['original_task_passed'],source_sha256=prior['source_sha256']);report['records'].append(record);save()
  p=copy.deepcopy(plans[ep.name]);assert p['scene']==scene.record() and p['step']==t and np.array_equal(p['start'],q);record['planning']=p
  record['planning_reused_unchanged_verified_solver_output']=True
  if not p['accepted']:
   record['first_command_accepted']=False;record['affine_fixture_result']='no_plan';save();print(ep.name,'NO PLAN',flush=True);continue
  points,checks=ind.path([q,np.array(p['endpoint'])],scene.record());assert np.max(abs(np.array(points)-np.array(p['waypoints'])))<1e-12
  assert all(c['accepted'] and c['elbow_gap_m']>=.005-2e-7 for c in checks)
  endpoint,details=ind.geometry(np.array(p['endpoint']),scene.record());axis=np.linalg.eigh(np.cov(guard.model.vertices[scene.side].T))[1][:,0]
  assert max(abs(details['point'][:2]))<=.0020002 and .0059998<=endpoint['active_above_top_m']<=.0070002
  assert abs(details['rotation'][:,2]@details['pose'][:3,:3]@axis)>=.8-2e-7
  record['independent_nominal_path_and_endpoint_passed']=True
  initial=context(scene,q,qp,previous,decay,t)
  lifecycle=FrontInitialCenterLifecycle(enabled=True)
  with patch('front_initial_center_lifecycle_v2.plan',return_value=copy.deepcopy(p)):
   event=lifecycle.update(**initial)
  record['first_event']=event;record['first_command_accepted']=event['kind'] in ['command','handover']
  if record['first_command_accepted']:
   verify_command(event,scene)
   args=dict(enabled=True,selected=True,mode='top_cross',recontacts=1,observed_load_n=0.,filtered_load_n=0.,current=q,previous_q=qp,previous_command=previous,waypoint=p['waypoints'][lifecycle.index],decay=decay,guard=guard,scene_check=lambda x: __import__('front_initial_center_plan').checked_scene(scene,x))
   old,old_record=parent_propose(**args)
   assert old is not None and np.array_equal(old,np.array(event['command'],dtype=np.float32))
   record['arithmetic_matches_parent_on_its_own_recovery_eligibility']=True
  fixture_events=[];c=initial
  for tick in range(241):
   fixture_events.append(dict(kind=event['kind'],step=c['step'],ticks=lifecycle.ticks,index=lifecycle.index,ready=lifecycle.ready,reason=event.get('reason')))
   if event['kind'] not in ('command',):break
   qnext=verify_command(event,scene)
   c=context(scene,qnext,c['current'],np.array(event['command']),decay,c['step']+1)
   event=lifecycle.update(**c)
  record['affine_fixture_result']=event['kind'];record['affine_fixture_reason']=event.get('reason');record['affine_fixture_events']=fixture_events
  record['affine_fixture_warning']='Locally exact causal response hypothesis, not physics or measured rollout.'
  # Counterexamples and handover geometry use explicitly manufactured FK measurements.
  for label,change in [('disabled',dict()),('not_selected',dict(selected=False)),('recovery_not_initial',dict(recontacts=1)),('parent_guard',dict(guard_stop=True)),('loaded',dict(observed_load_n=.1)),('filtered_loaded',dict(filtered_load_n=.051))]:
   life=FrontInitialCenterLifecycle(enabled=label!='disabled')
   with patch('front_initial_center_lifecycle_v2.plan',side_effect=AssertionError('Ineligible planning')):
    v=life.update(**dict(initial,**change))
   assert v['kind']=='unchanged';report['fixtures'].append(dict(episode=ep.name,case=label,passed=True))
  if record['first_command_accepted']:
   for label,changes,expected in [('guard_after_start',dict(guard_stop=True),'parent_guard_phase_or_contact_changed'),('load_after_start',dict(observed_load_n=.1),'parent_guard_phase_or_contact_changed'),('recovery_count_changed',dict(recontacts=1),'parent_guard_phase_or_contact_changed'),('skip_observation',dict(step=t+2),'nonconsecutive_observation')]:
    life=FrontInitialCenterLifecycle(enabled=True)
    with patch('front_initial_center_lifecycle_v2.plan',return_value=copy.deepcopy(p)):life.update(**initial)
    v=life.update(**dict(initial,step=t+1,**{k:v for k,v in changes.items() if k!='step'})) if 'step' not in changes else life.update(**dict(initial,**changes))
    assert v['kind']=='stop' and v['reason']==expected;report['fixtures'].append(dict(episode=ep.name,case=label,passed=True))
  # Only the finite-state/measured geometry boundary is tested here; not a trajectory.
  e=np.array(p['endpoint']);life=FrontInitialCenterLifecycle(enabled=True);life.active=life.attempted=True;life.plan=copy.deepcopy(p);life.scene=scene;life.index=len(p['waypoints'])-1
  ready_events=[]
  for j in range(3):
   v=life.update(**context(scene,e,e,e,decay,t+j));ready_events.append(v['kind'])
  record['manufactured_endpoint_ready_events']=ready_events
  record['manufactured_endpoint_ready_count']=life.ready
  # Save failures as evidence; do not silently loosen endpoint readiness.
  if ready_events!=['command','command','handover']:
   record['handover_boundary_passed']=False
  else:
   record['handover_boundary_passed']=True
   actual=guard.model.fk(scene.side,e)[0];center=np.array(v['captured_center_local']);world=actual[:3,3]+actual[:3,:3]@center
   assert np.max(abs(world-np.array(v['observed_support_xyz'])))<1e-8
   assert life.update(**context(scene,e,e,e,decay,t+3))['reason']=='initial_handover_already_complete'
  print(ep.name,'nodes',len(p['waypoints']),'first',record['first_command_accepted'],'affine',record['affine_fixture_result'],record['affine_fixture_reason'],'ready',ready_events,flush=True);save()
 report['status']='complete';report['all_handover_boundary_passed']=all(r.get('handover_boundary_passed') for r in report['records']);save()
except Exception as e:
 report['status']='failed';report['error']=repr(e);save();raise
