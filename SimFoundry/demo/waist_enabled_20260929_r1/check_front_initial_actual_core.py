"""Recompute all8 first-front plans using recorded real collision-core dimensions.
Old nominal-shell fixtures are not actual-core feasibility evidence. Current/past
real states only; causal predictions remain hypotheses, not physical handovers.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os,copy
from unittest.mock import patch
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_initial_center';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_initial_center_selection import plan
from front_initial_center_lifecycle_v3 import FrontInitialCenterLifecycle
from audit_front_initial_center_planning_v2 import SelectionAudit
from audit_front_initial_center_events import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S)
source=W/'FRONT_INITIAL_CENTER_SELECTION_CHECK.json';old=json.loads(source.read_text());params=json.loads((S/'causal_response_parameters.json').read_text());prep=json.loads((S/'PREPARATION.json').read_text())
for n,h in prep['stage_sha256'].items():assert sha(S/n)==h
out=W/'FRONT_INITIAL_ACTUAL_CORE_CHECK.json';assert not out.exists();report=dict(status='running',pid=os.getpid(),scope=__doc__,records=[],simulation_started=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),source,S/'PREPARATION.json',W/'audit_front_initial_center_planning_v2.py',W/'audit_front_initial_center_events.py']})
def save():report['updated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();p=out.with_suffix('.tmp');p.write_text(json.dumps(report,indent=2));p.replace(out)
try:
 save()
 for previous in old['records']:
  ep=next((W/'fresh_closed_peak_trials_r1').glob('case_*/'+previous['episode']));fr=json.loads((ep/'frontal_bypass.json').read_text());ctx=previous['live_first_event']['context'];z=copy.deepcopy(ctx['scene']);t=ctx['step'];actual=fr['plan']['front_cop_slip_following']['edge_speed']['actual_core'];nominal=z['core_size'];z['core_size']=actual['collision_core_size_xyz'];assert z['core_size']==fr['plan']['front_cop_slip_following']['edge_speed']['actual_core_size_xyz']
  assert actual['measurement'].startswith('Enabled USD collision prim')
  with np.load(ep/'raw.npz') as raw:q=raw['q'][t,12:23].astype(float);qp=raw['q'][t-1,12:23].astype(float);prev=raw['action'][t-1,12:23].astype(float);task=str(raw['task_id'])
  scene=RecontactScene(guard,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']);a=np.array(params['tasks'][task]['decay']);report['current_episode']=ep.name;save()
  selected=plan(scene,q,step=t,previous_q=qp,previous_command=prev,decay=a)
  proof=SelectionAudit(ROOT,S).verify_selection(selected,current=q,previous_q=qp,previous_command=prev,decay=a,scene=z,step=t)
  lifecycle=FrontInitialCenterLifecycle(enabled=True)
  with patch('front_initial_center_lifecycle_v3.plan',return_value=copy.deepcopy(selected)):
   event=lifecycle.update(step=t,selected=True,parent_mode='top_cross',recontacts=0,guard_stop=False,observed_load_n=0.,filtered_load_n=0.,scene=scene,current=q,previous_q=qp,previous_command=prev,decay=a,observed_hand_pose=guard.model.fk(scene.side,q)[0],observed_inactive_hand_pose=guard.model.fk(scene.inactive,q)[0])
  assert lifecycle.ready==0 and event['kind']==('command' if selected['accepted'] else 'unchanged')
  independent=None
  if selected['accepted']:independent=EventAudit(ROOT,S).verify(event,step=t,current=q,previous_q=qp,previous_command=prev,final_command=event['command'],scene=z,decay=a,selected=True,parent_mode='top_cross',recontacts=0,guard_stop=False,observed_load_n=0.,filtered_load_n=0.)
  report['records'].append(dict(episode=ep.name,original_task_passed=previous['original_task_passed'],nominal_fixture_accepted=previous['plan']['accepted'],nominal_core_size=nominal,actual_core=actual,plan=selected,live_first_event=event,independent_selection=proof,independent_first_command=independent,source_sha256={str(ep/n):sha(ep/n) for n in ['raw.npz','frontal_bypass.json','trace.npz','parcel_orientation.npz']}));save();print(ep.name,'actual_core_selected',selected['accepted'],selected.get('selected_seed'),flush=True)
 assert len(report['records'])==8;report.update(status='complete',passed=True,current_episode=None,selected=sum(r['plan']['accepted'] for r in report['records']),parent_fallback=sum(not r['plan']['accepted'] for r in report['records']));save()
except Exception as e:report.update(status='failed',error=repr(e));save();raise
