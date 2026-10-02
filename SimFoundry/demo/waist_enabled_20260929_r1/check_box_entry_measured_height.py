"""Reproduce FK-vs-measured mismatch; bind measured height to observed pose exactly.
Original FK/pose tolerance, height/ready thresholds and all other gates unchanged.
"""
from pathlib import Path
import sys,json,hashlib,copy,ast
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(w));stage=w/'staged_box_entry_lift'
from audit_box_entry_lift_events import LiftAudit as Old
from audit_box_entry_lift_events_measured import LiftAudit as New
r=w/'box_entry_lift_groups_r1';ep=r/'case_840001/layout_840001_push_box_to_bin';events=[e for e in json.loads((ep/'recontact_pose.json').read_text())['rows'] if e.get('entry_lift_phase')];assert len(events)==40
old=Old(repo,stage);new=New(repo,stage);count=0;negative=[]
def args(e):
 c=e['context'];return dict(step=c['step'],current=c['current'],previous_q=c['previous_q'],previous_command=c['previous_command'],final_command=e['command'],scene=c['scene'],decay=e['proposal']['decay'],selected=c['selected'],parent_mode=c['parent_mode'],recontacts=c['recontacts'],guard_stop=c['guard_stop'],observed_load_n=c['observed_load_n'],filtered_load_n=c['filtered_load_n'])
try:old.verify(events[0],**args(events[0]))
except AssertionError:old_reproduced=True
else:raise AssertionError('Expected original mismatch not reproduced')
for e in events:new.verify(e,**args(e));count+=1
assert not new.active
for label in ['recorded_height','observed_pose','readiness_count']:
 e=copy.deepcopy(events[0])
 if label=='recorded_height':e['measured_lowest_world_z_m']+=1e-5
 elif label=='observed_pose':e['context']['observed_hand_pose'][2][3]+=.001
 else:e['measured_ready_count']=3
 try:New(repo,stage).verify(e,**args(e))
 except AssertionError:negative.append(label)
 else:raise AssertionError('Accepted corruption '+label)
a="z=a.hand.minz(q,'right');near(z,event['measured_lowest_world_z_m'],1e-8)";b="T=np.asarray(ctx['observed_hand_pose'],float);z=float(np.min((a.hand.vertices['right']@T[:3,:3].T+T[:3,3])[:,2]));near(z,event['measured_lowest_world_z_m'],1e-8)";assert ast.dump(ast.parse((w/'audit_box_entry_lift_events_measured.py').read_text().replace(b,a)))==ast.dump(ast.parse((w/'audit_box_entry_lift_events.py').read_text()))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();files=[Path(__file__),w/'audit_box_entry_lift_events.py',w/'audit_box_entry_lift_events_measured.py',w/'audit_box_entry_pose_measured_supplement.py',ep/'recontact_pose.json'];out=dict(passed=True,scope=__doc__,original_failure_reproduced=old_reproduced,actual_lift_events=count,negative_rejected=negative,only_measured_height_expression_changed=True,original_failed_reports_preserved=True,source_sha256={str(p):sha(p) for p in files},training_ready=False);(r/'MEASURED_HEIGHT_SUPPLEMENT_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS actual40, old failure reproduced, corruptions rejected3')
