"""Original KKT math AST identity, eight frozen physical parent replays, and
explicit new-path branch admission/rejection. Preserves numerical failures.
"""
from pathlib import Path
import sys,json,hashlib,ast,copy
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_recontact_pose_task_optimality import verify_task_rows
from audit_self_clearance_task_optimality import IndependentElbows,near
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=ast.parse((w/'audit_self_clearance_task_optimality.py').read_text());new=ast.parse((w/'audit_recontact_pose_task_optimality.py').read_text());old_fn=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='inspect');new_fn=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='verify_task_rows')
start=next(i for i,n in enumerate(old_fn.body) if isinstance(n,ast.With));expected=old_fn.body[start:];actual=copy.deepcopy(new_fn.body)
loop=next(n for n in actual if isinstance(n,ast.For) and ast.unparse(n.target)=='c');branch=next(n for n in loop.body if isinstance(n,ast.If) and 'controller_kind' in ast.unparse(n.test));index=loop.body.index(branch);assert isinstance(loop.body[index+1],ast.Assert) and ast.unparse(loop.body[index+1].test)=='t not in verified_events';del loop.body[index:index+2]
assert ast.dump(ast.Module(body=actual,type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=expected,type_ignores=[]),include_attributes=False),'Original KKT math changed'
geom=IndependentElbows(w/'staged_recontact_pose/elbow_torso_hulls.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf');results=[]
for ep in sorted((w/'rear_short_recovery_groups_r1').glob('case_*/layout_*')):
 reference=ep/'SELF_CLEARANCE_TASK_OPTIMALITY_AUDIT.json'
 if not reference.exists():continue
 out=verify_task_rows(ep,geom,{});original=json.loads(reference.read_text())
 for name in ['passed','errors','frames','overrides','max_kkt_residual','records']:assert out[name]==original[name],(ep.name,name)
 results.append(dict(episode=ep.name,passed=out['passed'],frames=out['frames'],failed_frames=len(out['errors']),max_kkt_residual=out['max_kkt_residual'],frozen_audit_sha256=sha(reference)));print(results[-1],flush=True)
assert len(results)==8
# Execute actual new branch; every success requires its independently verified event.
fn=ast.FunctionDef(name='branch',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.List(elts=[ast.Constant(value=0)],ctx=ast.Load()),body=[branch],orelse=[])],decorator_list=[]);program=compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'<actual KKT declared path branch>','exec')
fixture=w/'staged_recontact_pose_probe/LIFECYCLE_CHECK.json';data=json.loads(fixture.read_text());count=0;negative=[]
for case in data['rows']:
 for plant in case['plants']:
  for event in plant['trace']:
   # Step remapping only indexes the single-event array fixture.
   c=dict(controller_kind='verified_unloaded_recontact_joint_path',recontact_pose_override=event,task_inputs=None,contact_normal_tracking=None,contact_bout_yaw_tracking=None)
   ns=dict(np=np,near=near,c=c,t=1,verified_events={1:event},experts={1:dict(mode='top_press' if event['kind']=='handover' else 'top_cross')},q=np.array([event['context']['previous_q'],event['context']['current']]),u=np.array([event['context']['previous_command'],event['command']]),records=[])
   exec(program,ns);ns['branch']();assert len(ns['records'])==1;count+=1
   if count==1:
    for kind in ['unverified','loaded_mode','changed_action','unexpected_normal_task']:
     bad={k:(copy.deepcopy(v) if k in ['c','verified_events','experts','q','u'] else v) for k,v in ns.items()};bad['records']=[]
     if kind=='unverified':bad['verified_events']={}
     if kind=='loaded_mode':bad['experts'][1]['mode']='top_push'
     if kind=='changed_action':bad['u'][1,1]+=.001
     if kind=='unexpected_normal_task':bad['c']['contact_normal_tracking']={}
     exec(program,bad)
     try:bad['branch']()
     except AssertionError:negative.append(kind)
     else:raise AssertionError('Accepted '+kind)
assert count==1768
out=dict(passed=True,scope=__doc__,original_math_ast_exact=True,parent_replays=results,preserved_failed_frames=sum(r['failed_frames'] for r in results),declared_events=count,rejected_corruptions=negative,fixture_sha256=sha(fixture),source_sha256={str(p):sha(p) for p in [Path(__file__),w/'audit_recontact_pose_task_optimality.py',w/'audit_self_clearance_task_optimality.py']},physical_validation=False,training_ready=False)
(w/'staged_recontact_pose/TASK_OPTIMALITY_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',len(results),out['preserved_failed_frames'],count,len(negative),flush=True)
