"""Verify causal selection over all eight already verified static plan sets.
Uses current/past real inputs only. Selected paths are affine hypotheses, not
physical passes; live handover must start at zero readiness after preflight.
"""
from pathlib import Path
import sys,json,datetime,hashlib,os,copy
from unittest.mock import patch
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_terminal_release_margin';sys.path[:0]=[str(W),str(S),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_initial_center_selection import select_planned
from front_initial_center_lifecycle_v3 import FrontInitialCenterLifecycle
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=json.loads((W/'FRONT_INITIAL_CENTER_LIFECYCLE_CHECK.json').read_text());assert base['status']=='complete';guard=ClearanceGuard(ROOT,S);parameters=json.loads((S/'causal_response_parameters.json').read_text())
out=W/'FRONT_INITIAL_CENTER_SELECTION_CHECK.json';assert not out.exists()
report=dict(status='running',pid=os.getpid(),scope=__doc__,records=[],collector_integrated=False,simulation_started=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'FRONT_INITIAL_CENTER_LIFECYCLE_CHECK.json',W/'front_initial_center_selection.py',W/'front_initial_center_lifecycle_v3.py',W/'front_initial_center_lifecycle_v2.py',W/'front_initial_center_plan.py',W/'front_initial_center_tracking.py',S/'causal_response_parameters.json']})
def save():
 report['updated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();p=out.with_suffix('.tmp');p.write_text(json.dumps(report,indent=2));p.replace(out)
try:
 save()
 for original in base['records']:
  p=original['planning'];z=p['scene'];scene=RecontactScene(guard,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']);ep=next((W/'fresh_closed_peak_trials_r1').glob('case_*/'+original['episode']));task='push_box_to_bin' if scene.side=='right' else 'nudge_mailer_to_bin';a=np.array(parameters['tasks'][task]['decay']);t=p['step']
  with np.load(ep/'raw.npz') as raw:q=raw['q'][t,12:23].astype(float);qp=raw['q'][t-1,12:23].astype(float);prev=raw['action'][t-1,12:23].astype(float)
  selected=select_planned(copy.deepcopy(p),scene,q,step=t,previous_q=qp,previous_command=prev,decay=a)
  args=dict(step=t,selected=True,parent_mode='top_cross',recontacts=0,guard_stop=False,observed_load_n=0.,filtered_load_n=0.,scene=scene,current=q,previous_q=qp,previous_command=prev,decay=a,observed_hand_pose=guard.model.fk(scene.side,q)[0],observed_inactive_hand_pose=guard.model.fk(scene.inactive,q)[0])
  life=FrontInitialCenterLifecycle(enabled=True)
  with patch('front_initial_center_lifecycle_v3.plan',return_value=copy.deepcopy(selected)):
   event=life.update(**args)
  assert event['kind'] in ('command','unchanged') and life.ready==0 and not life.finished
  assert event['kind']==('command' if selected['accepted'] else 'unchanged')
  assert not any(k.startswith('captured_') for k in event)
  row=dict(episode=original['episode'],original_task_passed=original['original_task_passed'],plan=selected,
           live_first_event=event,preflight_cannot_handover=True,parent_preserved_before_override=not selected['accepted'])
  report['records'].append(row);save();print(original['episode'],'selected',selected['accepted'],selected.get('selected_seed'),'live',event['kind'],flush=True)
 report.update(status='complete',selected=sum(r['plan']['accepted'] for r in report['records']),parent_fallback=sum(not r['plan']['accepted'] for r in report['records']));save()
except Exception as e:report.update(status='failed',error=repr(e));save();raise
