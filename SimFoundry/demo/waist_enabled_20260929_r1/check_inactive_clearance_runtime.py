"""Actual-context preparation through runtime/adapter and unchanged native branch.
No future observation is substituted; two proposed commands remain unissued.
Manufactured parent bookkeeping isolates adapter behavior, not physical success.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,ast,json,datetime,hashlib,copy
import numpy as np
import torch
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_inactive_clearance';P=W/'staged_front_recontact_headroom';D=W/'inactive_hand_headroom_draft_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from front_recontact_center_runtime import FrontRecontactCenterRuntime
from clearance_runtime import ClearanceGuard
from audit_front_initial_center_planning_v2 import SelectionAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text())
for n,h in prep['stage_sha256'].items():assert sha(S/n)==h,n
assert sha(S/'waist_coordination_clearance.py')==sha(P/'waist_coordination_clearance.py')
assert sha(S/'front_recontact_center_adapter.py')==sha(P/'front_recontact_center_adapter.py')
ep=W/'front_recontact_headroom_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin';old=json.loads((ep/'front_recontact_center.json').read_text())['rows'];fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};guard=ClearanceGuard(ROOT,S);independent=SelectionAudit(ROOT,S)
with np.load(ep/'raw.npz') as z:rawq=z['q'][:,12:23];rawu=z['action'][:,12:23]
fn=next(n for n in ast.parse((S/'waist_coordination_clearance.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='coordinated_step');branch=next(n for n in fn.body if isinstance(n,ast.If) and ast.unparse(n.test)=='front_recontact_override is not None');call=ast.FunctionDef(name='native_branch',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[copy.deepcopy(branch)],decorator_list=[]);program=compile(ast.fix_missing_locations(ast.Module(body=[call],type_ignores=[])),'<unchanged final recovery branch>','exec')
class ResetFixture:
 def __init__(self):self.resets=0
 def reset(self):self.resets+=1
records=[];negative=[]
for t in [405,528]:
 original=next(r for r in old if r['step']==t);c=original['context'];sc=c['scene'];row=copy.deepcopy(fr[t]);counter=c['recontacts'];np.testing.assert_array_equal(c['current'],rawq[t]);np.testing.assert_array_equal(c['previous_command'],rawu[t-1])
 state=SimpleNamespace(recontacts=counter,size=sc['core_size'],load=SimpleNamespace(bias_m=123.),cross_axis_control=ResetFixture(),cop_slip=ResetFixture())
 reference=copy.deepcopy(row['projected_support_reference']);before=copy.deepcopy(reference);normal=original['old_normal_anchor'];anchor=original['old_inactive_anchor']
 runtime=FrontRecontactCenterRuntime(guard,'left',sc['core_size'],sc['other_size'],c['decay'],enabled=True,inactive_clearance=True)
 # Explicit entry fixture: old recovery counter completed, no active path.
 runtime.last_counter=counter-1
 kw=dict(selected=True,step=t,current=c['current'],previous_q=c['previous_q'],previous_command=c['previous_command'],target_xyz=sc['target_xyz'],target_quat=sc['target_quat'],other_xyz=sc['other_xyz'],other_quat=sc['other_quat'],observed_load_n=c['observed_load_n'],observed_hand_pose=c['observed_hand_pose'],observed_inactive_hand_pose=c['observed_inactive_hand_pose'],normal_anchor=normal,inactive_anchor=anchor)
 updated,newref,event=runtime.update(row,state,reference,**kw)
 assert event['kind']=='command' and event['phase']=='inactive_clearance_preparation' and event['real_recontact_index']==counter
 assert newref==before and runtime.center_local is None and event['old_inactive_anchor']==anchor and event['old_normal_anchor']==normal
 assert state.recontacts==counter and state.mode==state.top_mode=='top_cross' and state.load.bias_m==0 and state.cross_axis_control.resets==state.cop_slip.resets==1
 assert updated['front_recontact_center_phase']=='tracking' and updated['contact_load']['applied_z_bias_m']==0.
 for name,alias in [('command','candidate_command'),('original_command_check','command_check'),('nominal','nominal_scene'),('predicted','predicted_scene')]:assert event['proposal'][name]==event['proposal'][alias]
 for name in ['nominal','predicted']:
  for q,stored in zip(event['proposal']['sampled_paths'][name]['states'],event['proposal']['sampled_paths'][name]['checks']):
   g,_=independent.geometry(q,sc);independent.compare_geometry(stored,g);assert g['accepted']
 q=np.array(c['current']);prev=np.array(c['previous_command']);joints=torch.zeros((1,23),dtype=torch.float32);joints[0,12:23]=torch.tensor(q,dtype=torch.float32)
 ns=dict(np=np,front_recontact_override=event,robot=SimpleNamespace(data=SimpleNamespace(joint_pos=SimpleNamespace(torch=joints))),joint_ids=list(range(12,23)),bounded=True,clearance_geometry=guard.geometry,default=np.zeros(23,dtype=np.float32),indices=list(range(12,23)),previous_command=prev,state=SimpleNamespace(side='left'),action=np.zeros(23,dtype=np.float32),palms={},points={},active_point_offset=reference['reference_local'],anchor={'right':anchor},active_support_reference=reference)
 exec(program,ns);result=ns['native_branch']();emitted=ns['action'][12:23];np.testing.assert_array_equal(emitted,np.asarray(event['command'],np.float32));final=guard.command(emitted,q,prev);assert final['accepted']
 # Original collector .055 step clipping must leave proposal identical.
 clipped=np.clip(emitted,prev.astype(np.float32)-np.float32(.055),prev.astype(np.float32)+np.float32(.055));np.testing.assert_array_equal(clipped,emitted)
 for label in ['wrong_output','wrong_proposal','wrong_previous','loaded','filtered','guard','wrong_side','wrong_counter','bad_nominal','bad_predicted','bad_command_gate','not_bounded','nonzero_default']:
  test=dict(ns);test['front_recontact_override']=copy.deepcopy(event);test['action']=np.zeros(23,dtype=np.float32);test['default']=ns['default'].copy();e=test['front_recontact_override']
  if label=='wrong_output':e['command'][0]+=.001
  elif label=='wrong_proposal':e['proposal']['candidate_command'][0]+=.001
  elif label=='wrong_previous':test['previous_command']=prev+np.eye(11)[0]*.001
  elif label=='loaded':e['context']['observed_load_n']=.1
  elif label=='filtered':e['context']['filtered_load_n']=.051
  elif label=='guard':e['context']['guard_stop']=True
  elif label=='wrong_side':test['state']=SimpleNamespace(side='right')
  elif label=='wrong_counter':e['real_recontact_index']+=1
  elif label=='bad_nominal':e['proposal']['nominal_scene']['accepted']=False
  elif label=='bad_predicted':e['proposal']['predicted_scene']['accepted']=False
  elif label=='bad_command_gate':e['proposal']['command_check']['accepted']=False
  elif label=='not_bounded':test['bounded']=False
  else:test['default'][12]=.001
  exec(program,test)
  try:test['native_branch']()
  except (ValueError,AssertionError,KeyError):negative.append(dict(step=t,case=label))
  else:raise AssertionError(('invalid native command accepted',t,label))
 # New flag disabled must retain original waiting behavior and avoid adapter writes.
 disabled=FrontRecontactCenterRuntime(guard,'left',sc['core_size'],sc['other_size'],c['decay'],enabled=True);disabled.last_counter=counter-1;untouched=copy.deepcopy(fr[t]);dummy=SimpleNamespace(recontacts=counter)
 same,ref,ev=disabled.update(untouched,dummy,reference,**kw);assert same is untouched and ev['kind']=='unchanged' and ev['reason']=='waiting_for_inactive_hand_planning_headroom'
 records.append(dict(step=t,event=event,final_guard=final,native_branch_exact=True,collector_clip_unchanged=True,reference_not_captured=True,original_disabled_wait_preserved=True));print(t,'runtime/native command passed',flush=True)
files=[Path(__file__),S/'COLLECTOR_PREPARATION.json',ep/'raw.npz',ep/'front_recontact_center.json',ep/'frontal_bypass.json',W/'audit_front_initial_center_planning_v2.py',*list(S/n for n in prep['stage_sha256'])]
out=dict(passed=True,scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),records=records,negative_cases=negative,source_sha256={str(p):sha(p) for p in files},full_native_episode_audit_ready=False,physical_started=False,training_ready=False)
with (S/'RUNTIME_JOINT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,actual_contexts=len(records),native_negative_cases=len(negative))))
