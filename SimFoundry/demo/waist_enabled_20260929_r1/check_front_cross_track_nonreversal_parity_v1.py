"""Two-context defaultoff equivalence and explicit original-command rejection.
No controller installation or physical claims; original gate thresholds intact.
"""
from pathlib import Path
import copy,datetime,hashlib,json,sys
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';sys.path[:0]=[str(S),str(W),str(ROOT)]
import numpy as np
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_cross_track_nonreversal_solver_candidate_v1 import propose
from joint_transport_effective_height_solver_v1 import propose as original
from audit_front_cross_track_nonreversal_candidate_v1 import verify
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();D=W/'front_cross_track_nonreversal_probe_r1';ep=W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin';co={r['step']:r for r in read(ep/'coordination.json')};positive={r['step']:r for r in read(D/'RESULT.json')['rows']};g=ClearanceGuard(ROOT,S);rows=[]
for t in [1009,1147]:
 c=co[t];record=c['joint_transport_clearance'];tc=record['collector_context'];s=tc['scene'];scene=RecontactScene(g,s['side'],s['target_xyz'],s['target_quat'],s['core_size'],s['other_xyz'],s['other_quat'],s['other_size']);kw=dict(step=t,side=s['side'],scene=scene,current=tc['current'],previous_q=tc['previous_q'],previous_command=tc['previous_command'],parent_command=record['parent_command'],decay=tc['decay'],coordinate=c,elbow_reserve_m=.0015,quarter_enabled=True)
 a,ar=original(**kw);b,br=propose(**kw,cross_track_nonreversal=False);assert ar==br and np.array_equal(a,b)
 old=copy.deepcopy(record['proposal']);old['cross_track_nonreversal']=copy.deepcopy(positive[t]['proposal']['cross_track_nonreversal']);cert=verify(old,c['task_inputs'],c,guard=g,elbow_reserve_m=.0015,quarter_enabled=True);assert cert['passed'] is False and cert['checks']['cross_track_nonreversal'] is False
 tamper=copy.deepcopy(positive[t]['proposal']);tamper['cross_track_nonreversal']['requested_direction']=1.
 try:verify(tamper,c['task_inputs'],c,guard=g,elbow_reserve_m=.0015,quarter_enabled=True)
 except ValueError:direction_tamper=True
 else:raise AssertionError('tampered direction accepted')
 row=dict(step=t,defaultoff_command_and_full_record_exact=True,original_reversing_command_rejected=True,original_rejection_checks=cert['checks'],direction_tamper_rejected=direction_tamper);rows.append(row);print(json.dumps(row),flush=True)
invalid=[]
for label,kw in [('nonboolean',dict(cross_track_nonreversal=1,route_stage='lateral_y')),('nonlateral',dict(cross_track_nonreversal=True,route_stage='front_x'))]:
 try:propose(**kw)
 except ValueError:invalid.append(label)
 else:raise AssertionError(label)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,rows=rows,invalid_cases_rejected=invalid,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'front_cross_track_nonreversal_solver_candidate_v1.py',W/'audit_front_cross_track_nonreversal_candidate_v1.py',D/'RESULT.json',ep/'coordination.json']},installed=False,physics_started=False,training_ready=False)
encoded=json.dumps(report,indent=2)
with (D/'PARITY_AND_REJECTION_V1.json').open('x') as f:f.write(encoded)
