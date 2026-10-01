"""Exercise the actual isolated coordination function and final/runtime gates.
Tensor-backed fake robot tests controller integration; not physical evidence.
"""
from pathlib import Path
import ast,sys,json,hashlib,types,copy
import numpy as np
import torch
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;root=w.parents[1];stage=w/'staged_self_clearance_task_ik';sys.path[:0]=[str(root),str(stage)]
from clearance_runtime import ClearanceGuard
from simfoundry.robots.g1_assets import G1_U1_23DOF_JOINT_NAMES
from simfoundry.data.sorting_quality import PALM_OFFSET
import task_ik
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def qa(q,v):
    xyz=q[...,:3];t=2*torch.cross(xyz,v,dim=-1)
    return v+q[...,3:]*t+torch.cross(xyz,t,dim=-1)
def load(path):
    tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='coordinated_step');ns=dict(np=np,torch=torch,quat_apply=qa,PALM_OFFSET=PALM_OFFSET,G1_U1_23DOF_JOINT_NAMES=G1_U1_23DOF_JOINT_NAMES)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),'exec'),ns);return ns['coordinated_step']
original=load(root/'simfoundry/data/waist_coordination.py');candidate=load(stage/'waist_coordination_clearance.py');guard=ClearanceGuard(root,stage);rng=np.random.default_rng(931)
records=[]
for i in range(64):
    q=rng.uniform(-.006,.006,11).astype(np.float32);full=np.r_[np.zeros(12,dtype=np.float32),q]
    pos=np.array([[.40,.14,.83],[.40,-.14,.83]],dtype=np.float32)
    quats=Rotation.from_rotvec(rng.normal(0,.02,(2,3))).as_quat().astype(np.float32)
    jac=rng.normal(0,.15,(1,2,6,23)).astype(np.float32)
    robot=types.SimpleNamespace(joint_names=list(G1_U1_23DOF_JOINT_NAMES),num_base_dofs=0,is_fixed_base=False,data=types.SimpleNamespace(joint_pos=types.SimpleNamespace(torch=torch.tensor(full[None])),body_pos_w=types.SimpleNamespace(torch=torch.tensor(pos[None])),body_quat_w=types.SimpleNamespace(torch=torch.tensor(quats[None])),body_link_jacobian_w=types.SimpleNamespace(torch=torch.tensor(jac))))
    side='left' if i%2 else 'right';hand=0 if side=='left' else 1
    anchor={s:(pos[k]+Rotation.from_quat(quats[k]).apply(PALM_OFFSET)).tolist() for k,s in enumerate(['left','right'])}
    state=types.SimpleNamespace(side=side,last_target_xyz=(np.array(anchor[side])+rng.normal(0,.005,3)).tolist())
    kwargs=dict(state=state,anchor=anchor,default=np.zeros(23,dtype=np.float32),waist_limit=1.,bounded=bool(i%3),active_point_offset=[.18,.003,.01] if i%4==0 else None,trace_jacobian=bool(i%2),waist_preference=.1 if i%5==0 else None)
    a=np.zeros(23,dtype=np.float32);b=a.copy();r1=original(robot,dict(left=0,right=1),a,**kwargs);r2=candidate(robot,dict(left=0,right=1),b,**kwargs)
    assert np.array_equal(a,b) and r1==r2
    kwargs['bounded']=True;cmd=np.zeros(23,dtype=np.float32)
    r3=candidate(robot,dict(left=0,right=1),cmd,clearance_geometry=guard.geometry,previous_command=q,**kwargs)
    inp=r3['task_inputs'];expected,meta=task_ik.solve(enabled=True,geometry=guard.geometry,**inp)
    if expected is None:assert r3['no_verified_command']
    else:
        assert np.array_equal(cmd[12:23],expected.astype(np.float32))
        assert guard.command(cmd[12:23],q,q)['accepted']
    records.append(dict(case=i,default_off_equal=True,enabled_accepted=expected is not None))
# Force a solver refusal through the real coordinator: caller receives no command.
old=task_ik.solve
try:
    task_ik.solve=lambda **kw:(None,dict(accepted=False,reason='injected_no_command'))
    untouched=rng.normal(0,.01,23).astype(np.float32);before=untouched.copy()
    r=candidate(robot,dict(left=0,right=1),untouched,clearance_geometry=guard.geometry,previous_command=q,**kwargs)
    assert r['no_verified_command'] and np.array_equal(untouched,before)
finally:task_ik.solve=old
# Verify real nominal hull geometry in independent explicit frame transforms.
pose_cases=[]
for i in range(80):
    q=rng.uniform(-.1,.1,11);poses=guard.transforms(q);r=guard.observe_poses(q,poses)
    assert max(abs(np.array(r['runtime_support_gaps_m'])-guard.geometry.constraints(q)))<1e-12
    if i==0:
        shifted=copy.deepcopy(poses);shifted['left_elbow_link'][0,3]+=.002
        assert not guard.observe_poses(q,shifted)['accepted']
        assert not guard.observe_poses(q,shifted)['model_coherent']
    pose_cases.append(dict(gaps=r['runtime_support_gaps_m'],coherent=r['model_coherent']))
zero=np.zeros(11);assert guard.command(zero,zero,zero,first=True)['accepted'];assert guard.observe_poses(zero,guard.transforms(zero))['accepted']
for name,cmd,current,prev,first,failed in [
 ('nonzero_first',np.r_[.001,np.zeros(10)],zero,zero,True,'first_zero'),
 ('waist_step',np.r_[.016,np.zeros(10)],zero,zero,False,'measured_step'),
 ('slew',zero,zero,np.r_[.056,np.zeros(10)],False,'previous_slew'),
 ('waist_bound',np.r_[.981,np.zeros(10)],np.r_[.97,np.zeros(10)],np.r_[.97,np.zeros(10)],False,'joint_bounds')]:
    r=guard.command(cmd,current,prev,first=first);assert not r['accepted'] and not r['checks'][failed],name
historical=w/'joint_edge_retry_groups_r1/case_840004/layout_840004_push_box_to_bin/raw.npz'
with np.load(historical) as z:bad=z['q'][400,12:23].copy()
assert not guard.command(bad,bad,bad)['checks']['nominal_margin']
assert not guard.observe_poses(bad,guard.transforms(bad))['accepted']
# Invalid records must not be silently accepted.
invalid=0
for callback in [lambda:guard.command(np.full(11,np.nan),zero,zero),lambda:guard.command(zero[:10],zero,zero),lambda:guard.command(zero,zero,zero,first=1),lambda:guard.observe_poses(np.full(11,np.nan),{}),lambda:guard.observe_poses(zero,dict.fromkeys(['torso_link','left_elbow_link','right_elbow_link'],np.zeros((4,4))))]:
    try:callback()
    except (ValueError,KeyError):invalid+=1
    else:raise AssertionError('Invalid record accepted')
# Inspect real collector placement, not a stand-alone mock of control flow.
s=(stage/'collect_paired_sorting.py').read_text();ast.parse(s)
assert s.index('final_clearance = clearance_guard.command')>s.index('action[12:23]=refined')
assert s.index('final_clearance = clearance_guard.command')<s.index('previous = action.copy()')<s.index('acts.append(default + action)')<s.index('obs, _, terminated, truncated, _ = env.step')
assert "if args.self_clearance_task_ik and not (args.role=='diagnostic'" in s and 'not args.policy_port' in s
report=dict(kind='controller_integration_and_gate_tests_not_physics',default_off_cases=64,enabled_cases=records,pose_transform_cases=80,invalid_records_rejected=invalid,no_command_keeps_action_untouched=True,zero_wait_passed=True,historical_overlap_rejected=True,final_override_order_verified=True,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),root/'simfoundry/data/waist_coordination.py',historical,*[stage/n for n in ['collect_paired_sorting.py','waist_coordination_clearance.py','task_ik.py','clearance_runtime.py','self_clearance.py','elbow_torso_hulls.json']]]})
(stage/'INTEGRATION_CHECK.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','enabled_cases']},indent=2));print('enabled accepted',sum(r['enabled_accepted'] for r in records))
