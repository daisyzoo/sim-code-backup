"""Bind lifecycle first observations to recorded nonzero filtered loads.
Earlier affine fixture holds future loads at zero; this supplement checks the
real prefix loads and mode explicitly. Predictions remain synthetic.
"""
from pathlib import Path
import sys,json,hashlib,copy,datetime
from unittest.mock import patch
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_waypoint_reconciliation';D=W/'front_bag_recontact_center_draft_r4';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_recontact_center_lifecycle import FrontRecontactCenterLifecycle
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();data=json.loads((D/'LIFECYCLE_CHECK.json').read_text());base=json.loads((W/'front_bag_recontact_center_draft_r3/STATIC_CONTEXT_PROBE.json').read_text());early=json.loads((W/'front_bag_recontact_center_draft_r2/STATIC_CONTEXT_PROBE.json').read_text());guard=ClearanceGuard(ROOT,S);records=[];sources=dict(data['source_sha256'])
for name,h in sources.items():assert sha(name)==h,name
for p in [Path(__file__),D/'LIFECYCLE_CHECK.json',W/'front_bag_recontact_center_draft_r2/STATIC_CONTEXT_PROBE.json',W/'front_bag_recontact_center_draft_r3/STATIC_CONTEXT_PROBE.json']:sources[str(p)]=sha(p)
for record in data['records']:
 e=copy.deepcopy(record['events'][0]);c=e['context'];raw=next(x for x in base['records'] if x['run']==record['run'] and x['recontacts']==record['recontacts']);before=next(x for x in early['records'] if x['run']==record['run'] and x['recontacts']==record['recontacts']);life=FrontRecontactCenterLifecycle(enabled=True,recontact_index=record['recontacts'])
 def inp(r):
  z=r['planning']['scene'];sc=RecontactScene(guard,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']);q=np.asarray(r['actual_start']);return dict(step=r['step'],selected=True,parent_mode=r['mode'],recontacts=r['recontacts'],guard_stop=False,observed_load_n=r['observed_load_n'],filtered_load_n=r['filtered_load_n'],scene=sc,current=q,previous_q=np.asarray(r['previous_q']),previous_command=np.asarray(r['previous_command']),decay=np.asarray(c['decay']),observed_hand_pose=guard.model.fk('left',q)[0],observed_inactive_hand_pose=guard.model.fk('right',q)[0])
 with patch('front_recontact_center_lifecycle.plan',side_effect=AssertionError('unqualified geometry planning')):wait=life.update(**inp(before))
 assert wait['kind']=='unchanged' and wait['reason']=='waiting_for_original_unloaded_geometry' and not life.attempted
 with patch('front_recontact_center_lifecycle.plan',return_value=copy.deepcopy(record['selected_plan'])):actual=life.update(**inp(raw))
 assert actual['context']['filtered_load_n']==raw['filtered_load_n'] and actual['context']['parent_mode']==raw['mode'];assert actual['kind']=='command' and life.ready==0
 # Gate-only differences must not change any command/geometry/readiness result.
 expected=copy.deepcopy(e);expected['context']['filtered_load_n']=raw['filtered_load_n'];expected['context']['parent_mode']=raw['mode'];assert actual==expected
 records.append(dict(run=record['run'],recontacts=record['recontacts'],early_step=before['step'],early_recorded_filtered_load_n=before['filtered_load_n'],first_command_step=raw['step'],recorded_filtered_load_n=raw['filtered_load_n'],recorded_parent_mode=raw['mode'],first_command_exact_except_context=True,early_geometry_wait_does_not_consume_attempt=True,predicted_ready_not_reused=True))
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256=sources,simulation_started=False,collector_integrated=False,training_ready=False)
with (D/'ACTUAL_PREFIX_LOAD_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,actual_prefix_pairs=len(records))))
