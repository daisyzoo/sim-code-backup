"""Can all5 X-only main-direction failures satisfy both nominal directions?
Same actual histories, original objective/height/normal/safety constraints.
Feasibility screen only, no new KKT/continuous-path/native certification.
"""
from pathlib import Path
import datetime,hashlib,json,sys,time
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_xy_nonreversal_probe_r1';D.mkdir(exist_ok=False);sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_xy_nonreversal_solver_candidate_v1 import propose
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();m=W/'front_cross_track_full_stream_probe_r1/MAIN_PROGRESS_AND_PREDICTION_V1.json';steps=[r['step'] for r in read(m)['rows'] if r['new_nominal_y_reversed']];assert len(steps)==5;ep=W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin';cs={c['step']:c for c in read(ep/'coordination.json')};g=ClearanceGuard(ROOT,S);rows=[]
for t in steps:
 c=cs[t];old=c['joint_transport_clearance'];tc=old['collector_context'];s=tc['scene'];scene=RecontactScene(g,s['side'],s['target_xyz'],s['target_quat'],s['core_size'],s['other_xyz'],s['other_quat'],s['other_size']);start=time.monotonic();u,p=propose(step=t,side=s['side'],scene=scene,current=tc['current'],previous_q=tc['previous_q'],previous_command=tc['previous_command'],parent_command=old['parent_command'],decay=tc['decay'],coordinate=c,elbow_reserve_m=.0015,quarter_enabled=True,cross_track_nonreversal=True,route_stage='lateral_y');summary=dict(step=t,proposal_exists=u is not None,solver_success=p['solver_success'],solver_status=p['solver_status'],iterations=p['iterations'],min_margin_m=p['min_constraint_margin_m'],signed_dx_m=p['cross_track_nonreversal']['proposal_signed_nominal_dx_m'],signed_dy_m=p['main_direction_nonreversal']['proposal_signed_nominal_dy_m'],elapsed_s=time.monotonic()-start);rows.append(dict(summary=summary,proposal=p))
 with (D/f'CONTEXT_{t}.json').open('x') as f:json.dump(rows[-1],f,indent=2)
 print(json.dumps(summary),flush=True)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'front_xy_nonreversal_solver_candidate_v1.py',m,ep/'coordination.json']},installed=False,physics_started=False,training_ready=False,limitations=['Solver status/primal feasibility is not independent stationarity or whole trajectory evidence.','Failure to find a feasible solution is not a mathematical proof of infeasibility.','Both zero nominal directions can still stall the task. The main sorting objective is not satisfied merely by no reversal.','If these constraints conflict with parent height, examine the expert objective explicitly; never relax original physical/task quality gates.'])
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2)
