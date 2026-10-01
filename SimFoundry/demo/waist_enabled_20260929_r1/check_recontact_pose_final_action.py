"""Actual collector final clipping/refinement/clearance code on all new proposals.
Also checks terminal hold cannot override top_cross/top_press even when latched.
This is a synthetic action-chain test, not a physics rollout.
"""
from pathlib import Path
import ast,sys,json,hashlib,types
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_recontact_pose';sys.path[:0]=[str(stage),str(repo)]
from clearance_runtime import ClearanceGuard
from simfoundry.data.terminal_joint_hold import TerminalJointHold
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage)
tree=ast.parse((stage/'collect_paired_sorting.py').read_text())
slew=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and ast.unparse(n)=='action = np.clip(action, previous - 0.055, previous + 0.055)')
loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and any(isinstance(x,ast.Assign) and ast.unparse(x).startswith('action = np.clip(default + action,') for x in n.body))
start=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and ast.unparse(n).startswith('action = np.clip(default + action,'))
end=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and ast.unparse(n)=='previous = action.copy()')
body=[slew]+loop.body[start:end]
program=compile(ast.fix_missing_locations(ast.Module(body=[ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.List(elts=[ast.Constant(value=0)],ctx=ast.Load()),body=body,orelse=[])],type_ignores=[])),'<actual final command chain>','exec')
class Tensor:
 def __init__(self,x):self.x=np.asarray(x)
 def __getitem__(self,i):return Tensor(self.x[i])
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.x
fixture=w/'staged_recontact_pose_probe/LIFECYCLE_CHECK.json';data=json.loads(fixture.read_text());counts=dict(events=0,handovers=0,terminal_rejections=0)
for case in data['rows']:
 for plant in case['plants']:
  for event in plant['trace']:
   ctx=event['context'];q=np.array(ctx['current']);previous=np.r_[np.zeros(12),ctx['previous_command']].astype(np.float32);expected=np.array(event['command'],dtype=np.float32);mode='top_press' if event['kind']=='handover' else 'top_cross'
   for latched in [False,True]:
    hold=TerminalJointHold(consecutive=5 if latched else 0,command=tuple(previous[12:23]) if latched else None)
    output=hold.observe(mode=mode,target_confirmed=True,hand_clearance_m=.1,load_n=0.,active_error_m=0.,inactive_error_m=0.,other_max_xy_m=0.,current_upper_q=q,previous_upper_command=previous[12:23]);assert output is None and hold.command is None;counts['terminal_rejections']+=1
   coordinate=dict(upper_q=q.tolist(),region_joint_override=None,terminal_joint_hold=False)
   ns=dict(np=np,action=np.r_[np.zeros(12),expected].astype(np.float32),previous=previous,default=np.zeros(23,dtype=np.float32),U1_JOINT_LIMIT_LO=U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI=U1_JOINT_LIMIT_HI,args=types.SimpleNamespace(motion_protocol='waist_yaw_enabled_v1',waist_probe=False,waist_limit_rad=1.,rear_joint_edge_command=True,rear_joint_edge_analytic_retry=True),step=ctx['step'],frontal_plan=dict(rear_joint_edge_command=dict(enabled=True),region_causal_response=dict(actual_core=dict(collision_core_size_xyz=ctx['scene']['core_size']))),coordination_log=[dict(step=ctx['step'],**coordinate)],frontal_log=[dict(step=ctx['step'],mode=mode,rear_joint_xy_progress=dict(override=False))],robot=types.SimpleNamespace(data=types.SimpleNamespace(joint_pos=types.SimpleNamespace(torch=Tensor([np.r_[np.zeros(12),q]])))),ordered_ids=list(range(23)),parcel_xyz=lambda *a:ctx['scene']['target_xyz'],env=None,target_actor='parcel_box' if ctx['scene']['side']=='right' else 'mailer',target_quat=ctx['scene']['target_quat'],region_model=guard.model,side=ctx['scene']['side'],clearance_guard=guard,clearance_rows=[],clearance_failure=None)
   exec(program,ns)
   assert ns['clearance_failure'] is None and len(ns['clearance_rows'])==1 and ns['clearance_rows'][0]['accepted'] is True
   assert np.array_equal(ns['action'][12:23],expected) and np.array_equal(ns['action'][:12],np.zeros(12))
   assert ns['coordination_log'][0]['joint_edge_refinement']['override'] is False
   counts['events']+=1;counts['handovers']+=int(event['kind']=='handover')
assert counts==dict(events=1768,handovers=16,terminal_rejections=3536)
sources=[Path(__file__),stage/'collect_paired_sorting.py',stage/'joint_edge_adapter.py',stage/'joint_edge_command.py',stage/'clearance_runtime.py',repo/'simfoundry/data/terminal_joint_hold.py',repo/'simfoundry/robots/g1_assets.py']
out=dict(passed=True,scope=__doc__,counts=counts,fixture_sha256=sha(fixture),source_sha256={str(p):sha(p) for p in sources},physical_validation=False,training_ready=False)
(stage/'FINAL_ACTION_CHECK.json').write_text(json.dumps(out,indent=2));print(counts,flush=True)
