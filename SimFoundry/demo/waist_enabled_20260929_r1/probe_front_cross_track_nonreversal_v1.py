"""Uninstalled nonreversal constraint at two actual harmful command contexts.
No simulated successor state, no training admission, no physical safety proof.
"""
from pathlib import Path
import datetime,hashlib,json,sys,time
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_cross_track_nonreversal_probe_r1';D.mkdir(exist_ok=False);sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_cross_track_nonreversal_solver_candidate_v1 import propose
from joint_transport_effective_height_certificate_v1 import verify
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());ep=W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin';co={c['step']:c for c in read(ep/'coordination.json')};fr={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};guard=ClearanceGuard(ROOT,S);hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');rows=[]
for t in [1009,1147]:
 c=co[t];tc=c['joint_transport_clearance']['collector_context'];sc=tc['scene'];assert fr[t]['route_stage']=='lateral_y';assert c['joint_transport_clearance']['applied'];scene=RecontactScene(guard,sc['side'],sc['target_xyz'],sc['target_quat'],sc['core_size'],sc['other_xyz'],sc['other_quat'],sc['other_size']);kwargs=dict(step=t,side=sc['side'],scene=scene,current=tc['current'],previous_q=tc['previous_q'],previous_command=tc['previous_command'],parent_command=c['joint_transport_clearance']['parent_command'],decay=tc['decay'],coordinate=c,elbow_reserve_m=.0015,quarter_enabled=True)
 start=time.monotonic();command,proposal=propose(**kwargs,cross_track_nonreversal=True,route_stage=fr[t]['route_stage']);elapsed=time.monotonic()-start
 certificate=None;nonreversal=None
 if command is not None:
  certificate=verify(proposal,c['task_inputs'],c,guard=guard,elbow_reserve_m=.0015,quarter_enabled=True)
  normal=Rotation.from_quat(sc['target_quat']).as_matrix()[:,2];center=np.array(c['active_support_reference']['center_local'])
  def ipoint(q):
   T=hand.fk(q,'right');n=T[:3,:3].T@normal;off=center+n*(min(guard.model.vertices['right']@n)-center@n);return T[:3,3]+T[:3,:3]@off
  actual_delta=ipoint(command)[0]-ipoint(tc['current'])[0];direction=float(np.sign(c['task_inputs']['error'][3]));assert direction*actual_delta>=-2e-7
  nonreversal=dict(independent_nominal_dx_m=float(actual_delta),signed_dx_m=float(direction*actual_delta),passed=True)
 row=dict(step=t,proposal_exists=command is not None,elapsed_s=elapsed,proposal=proposal,original_certificate=certificate,independent_nonreversal=nonreversal);rows.append(row)
 with (D/f'CONTEXT_{t}.json').open('x') as f:json.dump(row,f,indent=2)
 print(json.dumps(dict(step=t,proposal_exists=command is not None,solver_status=proposal['solver_status'],original_certificate_passed=None if certificate is None else certificate['passed'],nonreversal=nonreversal)),flush=True)
sources={str(p):sha(p) for p in [Path(__file__),W/'front_cross_track_nonreversal_solver_candidate_v1.py',ep/'coordination.json',ep/'frontal_bypass.json']}
for p in S.iterdir():
 if p.is_file():sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,installed=False,physics_started=False,training_ready=False,remaining=['Full defaultoff parity, nonlinear path and independent new-constraint stationarity validation, all directions/context selection and source/native/action audits.','If constraint is infeasible reject proposal; do not relax original pressure/geometry/quality gates.','This command test does not establish contact retention, improved task score or closed-loop dynamics.'])
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2)
