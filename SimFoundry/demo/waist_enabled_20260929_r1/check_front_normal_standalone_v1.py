"""Compare standalone solver to prior closure-only probe on all34actual contexts."""
from pathlib import Path
import datetime,hashlib,json,sys,time
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_normal_standalone_probe_r1';D.mkdir(exist_ok=False);sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from joint_transport_paths import JointTransportPaths
from front_normal_nondegradation_solver_candidate_v1 import propose
from audit_front_exact_normal_planning_v1 import verify
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=W/'front_normal_nondegradation_probe_r1/RESULT.json';report=read(source);ep=W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin';cs={c['step']:c for c in read(ep/'coordination.json')};g=ClearanceGuard(ROOT,S);paths=JointTransportPaths(ROOT,S);rows=[]
for prior in report['rows']:
 t=prior['step'];c=cs[t];old=c['joint_transport_clearance'];tc=old['collector_context'];z=tc['scene'];scene=RecontactScene(g,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']);kw=dict(step=t,side=z['side'],scene=scene,current=tc['current'],previous_q=tc['previous_q'],previous_command=tc['previous_command'],parent_command=old['parent_command'],decay=tc['decay'],coordinate=c,elbow_reserve_m=.0015,quarter_enabled=True)
 start=time.monotonic();u,r=propose(normal_nondegradation=True,route_stage='lateral_y',**kw);cert=None;parity=None;hold=None
 if u is not None:
  assert prior['command'] is not None;parity=dict(exact_command=bool(np.array_equal(u,prior['command'])),max_command_difference_rad=float(np.max(abs(u-np.array(prior['command'])))));cert=verify(u,c,guard=g);assert cert['passed']
 else:
  assert prior['command'] is None and r['requires_recovery']
  q=np.array(tc['current']);prev=np.array(tc['previous_command']);qp=np.array(tc['previous_q']);a=np.array(tc['decay']);command=q.astype(np.float32).astype(float);forecast=(1-a)*command+a*q+q-prev-a*(qp-prev)
  hold=dict(command=command.tolist(),final_guard=g.command(command,q,prev),paths={name:paths.certify(q,end,z) for name,end in [('nominal',command),('predicted',forecast)]},predicted_q=forecast.tolist(),meaning='one-frame measured-position command before original recovery; not proof of zero actual movement')
 row=dict(step=t,proposal_exists=u is not None,proposal=r,parity=parity,certificate=cert,unloaded_hold_probe=hold,elapsed_s=time.monotonic()-start);rows.append(row)
 with (D/f'CONTEXT_{t}.json').open('x') as f:json.dump(row,f,indent=2,allow_nan=False)
 print(json.dumps(dict(step=t,proposal_exists=u is not None,parity=parity,independent_passed=None if cert is None else cert['passed'],unloaded_hold_passed=None if hold is None else hold['final_guard']['accepted'] and all(x['passed'] for x in hold['paths'].values()))),flush=True)
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,contexts=len(rows),proposals=sum(r['proposal_exists'] for r in rows),exact_parity=sum(bool(r['parity'] and r['parity']['exact_command']) for r in rows),rows=rows,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'front_normal_nondegradation_solver_candidate_v1.py',W/'audit_front_exact_normal_planning_v1.py',source,ep/'coordination.json']},installed=False,training_ready=False,physics_started=False,limitations=['Fixed actual histories only; no native collector integration or recovery state mutation here.','Measured-position command can still move under inertia/servo/contact. No physical stability claim.'])
with (D/'RESULT.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
print(json.dumps(dict(contexts=result['contexts'],proposals=result['proposals'],exact_parity=result['exact_parity'])),flush=True)
