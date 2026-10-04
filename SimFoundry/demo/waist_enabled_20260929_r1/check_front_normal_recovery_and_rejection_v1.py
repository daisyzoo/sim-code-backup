"""Real original recovery method and no-command failure lifecycle, no simulation."""
from pathlib import Path
import copy,datetime,hashlib,json,sys
from unittest.mock import patch
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_normal_recovery_checks_r1';D.mkdir(exist_ok=False);sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_initial_center_top_contact import TopContactBypassState
import front_normal_nondegradation_runtime_candidate_v1 as runtime
import front_normal_nondegradation_solver_candidate_v1 as solver
from joint_transport_effective_height_solver_v1 import propose as original_propose
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ep=W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin';cs={c['step']:c for c in read(ep/'coordination.json')};fr={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};g=ClearanceGuard(ROOT,S);on=runtime.FrontNormalNondegradation(g,ROOT,S,enabled=True)
def kwargs(t):
 c=cs[t];old=c['joint_transport_clearance'];tc=old['collector_context'];s=tc['scene'];scene=RecontactScene(g,s['side'],s['target_xyz'],s['target_quat'],s['core_size'],s['other_xyz'],s['other_quat'],s['other_size'])
 return dict(step=t,selected=True,side='right',row=fr[t],coordinate=c,scene=scene,current=tc['current'],previous_q=tc['previous_q'],previous_command=tc['previous_command'],parent_command=old['output_command'],decay=tc['decay'])
def state_for(t):
 s=TopContactBypassState(None,'right',tuple(cs[t]['joint_transport_clearance']['collector_context']['scene']['core_size']));s.top_mode='top_push';s.mode='top_push';s.mode_step=12;s.recontacts=fr[t]['recontacts'];s.lost_contact_steps=t-681;s.command=tuple(fr[t]['target_xyz']);s.load.bias_m=-.006;s.settled=9;s.selected_surface_local_xy=(.01,.02);s.descent_z=.81;s.corner_local=(.01,.02,.03);s.approach_xy_bias=[.02,.03];return s
recoveries=[]
for t in [682,683]:
 kw=kwargs(t);u,r=on.refine(**kw);assert r['requires_recovery'] and not r['requires_stop'];assert u is not None;fg=g.command(u,kw['current'],kw['previous_command']);s=state_for(t)
 before=copy.deepcopy(s.__dict__);bad=dict(fg,accepted=False)
 try:runtime.commit_original_recovery(r,s,bad)
 except ValueError:pass
 else:raise AssertionError('Rejected final guard committed recovery')
 assert s.__dict__==before and not r['recovery_committed']
 event=runtime.commit_original_recovery(r,s,fg);assert s.top_mode=='top_lift' and s.recontacts==before['recontacts']+1 and s.command is None and s.descent_z is None and s.selected_surface_local_xy is None and s.load.bias_m==0 and s.lost_contact_steps==0 and s.mode_step==0
 stable=copy.deepcopy(s.__dict__)
 try:runtime.commit_original_recovery(r,s,fg)
 except ValueError:pass
 else:raise AssertionError('Duplicate recovery accepted')
 assert s.__dict__==stable
 recoveries.append(dict(step=t,record=r,transition=event,final_guard_rejection_no_mutation=True,duplicate_rejection_no_mutation=True))
# Faults use separately solved immutable proposals; no artificial physical state.
kw=kwargs(1009);detail=read(W/'front_normal_standalone_probe_r1/CONTEXT_1009.json');u=np.array(detail['proposal']['command']);proposal=detail['proposal'];failures=[]
for name in ['solver','certificate','path','parent_guard','final_guard']:
 local=runtime.FrontNormalNondegradation(g,ROOT,S,enabled=True)
 returned=(None,dict(requires_recovery=False,reason='injected')) if name=='solver' else (u.copy(),copy.deepcopy(proposal))
 actual_guard=g.command
 def command_check(command,*args,**kwargs):
  v=actual_guard(command,*args,**kwargs)
  is_parent=np.array_equal(command,kw['parent_command'])
  if (name=='parent_guard' and is_parent) or (name=='final_guard' and not is_parent):return dict(v,accepted=False)
  return v
 with patch.object(runtime,'propose',return_value=returned),patch.object(g,'command',side_effect=command_check):
  if name=='certificate':
   with patch.object(runtime,'verify',return_value=dict(passed=False)):command,record=local.refine(**kw)
  elif name=='path':
   with patch.object(local.paths,'certify',return_value=dict(passed=False)):command,record=local.refine(**kw)
  else:command,record=local.refine(**kw)
 assert command is None and record['requires_stop'] and record['output_command'] is None and not record['requires_recovery']
 failures.append(dict(case=name,reason=record['reason'],no_command=True))
# Failed hold must not authorize an expert-state transition.
local=runtime.FrontNormalNondegradation(g,ROOT,S,enabled=True)
with patch.object(local.paths,'certify',return_value=dict(passed=False)):command,record=local.refine(**kwargs(682))
assert command is None and record['requires_stop'] and not record['requires_recovery'];failures.append(dict(case='recovery_hold_path',reason=record['reason'],no_command=True))
off=[]
for t in [1009,682]:
 kw=kwargs(t);c=cs[t];sk=dict(step=t,side='right',scene=kw['scene'],current=kw['current'],previous_q=kw['previous_q'],previous_command=kw['previous_command'],parent_command=c['joint_transport_clearance']['parent_command'],decay=kw['decay'],coordinate=c,elbow_reserve_m=.0015,quarter_enabled=True)
 a,ar=solver.propose(normal_nondegradation=False,**sk);b,br=original_propose(**sk)
 assert (a is None)==(b is None) and ar==br
 if a is not None:np.testing.assert_array_equal(a,b)
 off.append(dict(step=t,command_and_full_record_equal=True))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,recoveries=recoveries,failure_injections=failures,solver_default_off=off,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'front_normal_nondegradation_runtime_candidate_v1.py',W/'front_normal_nondegradation_solver_candidate_v1.py',S/'front_initial_center_top_contact.py',ep/'coordination.json',ep/'frontal_bypass.json']},training_ready=False,physics_started=False,limitations=['Original recovery method on a prepared state fixture, not full native collector replay or actual next-frame trajectory.','No source/stream audit consumer integration and no physical launch.'])
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2,allow_nan=False)
print(json.dumps(dict(recovery_cases=len(recoveries),fault_injections=len(failures),default_off=len(off))),flush=True)
