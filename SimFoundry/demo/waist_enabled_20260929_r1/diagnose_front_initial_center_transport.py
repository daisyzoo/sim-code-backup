"""Bounded cause diagnosis for baseline budget/command-rejected initial paths.
Every accepted static alternative is tested with the same causal affine fixture,
240 tick budget and original guards. This is neither physics nor data admission.
"""
from pathlib import Path
import sys,json,hashlib,copy,datetime,os
from unittest.mock import patch
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_terminal_release_margin';sys.path[:0]=[str(W),str(S),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_initial_center_lifecycle_v2 import FrontInitialCenterLifecycle
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=json.loads((W/'FRONT_INITIAL_CENTER_LIFECYCLE_CHECK.json').read_text());assert base['status']=='complete'
guard=ClearanceGuard(ROOT,S);parameters=json.loads((S/'causal_response_parameters.json').read_text())
out=W/'FRONT_INITIAL_CENTER_TRANSPORT_DIAGNOSIS.json';assert not out.exists()
report=dict(status='running',pid=os.getpid(),scope=__doc__,records=[],simulation_started=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'FRONT_INITIAL_CENTER_LIFECYCLE_CHECK.json',W/'front_initial_center_lifecycle_v2.py',W/'front_initial_center_tracking.py',W/'front_initial_center_plan.py',S/'causal_response_parameters.json']})
def save():
 report['updated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();p=out.with_suffix('.tmp');p.write_text(json.dumps(report,indent=2));p.replace(out)
try:
 save()
 for old in base['records']:
  if old['planning']['nominal_path_nodes']<240 and old.get('affine_fixture_reason')!='no_verified_initial_front_command':continue
  p0=old['planning'];z=p0['scene'];scene=RecontactScene(guard,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']);ep=next((W/'fresh_closed_peak_trials_r1').glob('case_*/'+old['episode']));task='push_box_to_bin' if scene.side=='right' else 'nudge_mailer_to_bin';decay=np.array(parameters['tasks'][task]['decay']);t=old['step']
  with np.load(ep/'raw.npz') as raw:q0=raw['q'][t,12:23].astype(float);qp0=raw['q'][t-1,12:23].astype(float);prev0=raw['action'][t-1,12:23].astype(float)
  for attempt in p0['attempts']:
   if not attempt['endpoint_accepted'] or not attempt['nominal_path']['accepted']:continue
   p=copy.deepcopy(p0);p.update(endpoint=attempt['endpoint'],waypoints=attempt['nominal_path']['waypoints'],selected_seed=attempt['seed'],nominal_path_nodes=len(attempt['nominal_path']['waypoints']))
   life=FrontInitialCenterLifecycle(enabled=True);q,qp,prev=q0.copy(),qp0.copy(),prev0.copy();last=None
   for j in range(241):
    c=dict(step=t+j,selected=True,parent_mode='top_cross',recontacts=0,guard_stop=False,observed_load_n=0.,filtered_load_n=0.,scene=scene,current=q,previous_q=qp,previous_command=prev,decay=decay,observed_hand_pose=guard.model.fk(scene.side,q)[0],observed_inactive_hand_pose=guard.model.fk(scene.inactive,q)[0])
    with patch('front_initial_center_lifecycle_v2.plan',return_value=p):event=life.update(**c)
    if event['kind']!='command':break
    command=np.array(event['command']);bias=q-prev-decay*(qp-prev);nextq=(1-decay)*command+decay*q+bias
    assert np.max(abs(nextq-np.array(event['proposal']['predicted_q'])))<1e-12
    last=event;qp,q,prev=q,nextq,command
   g=scene.details(q);a=abs(scene.rotation[:,2]@g['hand_pose'][:3,:3]@p['thin_axis_local'])
   row=dict(episode=old['episode'],seed=attempt['seed'],nodes=p['nominal_path_nodes'],outcome=event['kind'],reason=event.get('reason'),ticks=life.ticks,waypoint_index=life.index,ready_count=life.ready,final_q=q.tolist(),endpoint_max_joint_error_rad=float(max(abs(q-np.array(p['endpoint'])))),final_lowest_xy_m=g['point'][:2].tolist(),final_height_m=float(g['point'][2]-scene.core[2]/2),final_alignment_abs=float(a),terminal_event=event,last_command_event=last)
   report['records'].append(row);print(old['episode'],attempt['seed'],event['kind'],event.get('reason'),'ticks',life.ticks,flush=True);save()
 report['status']='complete';save()
except Exception as e:report.update(status='failed',error=repr(e));save();raise
