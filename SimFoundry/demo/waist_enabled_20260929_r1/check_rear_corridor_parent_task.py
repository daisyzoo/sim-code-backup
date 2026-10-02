"""Original task KKT on real same-step inputs in sparse synthetic native files.
Not a complete trajectory or new physics; final pose/pressure audits remain mandatory.
"""
from pathlib import Path
import sys,json,hashlib,datetime,tempfile,shutil,os
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_recovery_guarded';sys.path[:0]=[str(W),str(ROOT)]
from audit_rear_corridor_stage_pose_task_optimality import verify_task_rows,IndependentElbows
from audit_joint_edge_stage_task_optimality import verify_task_rows as original
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dest=W/'REAR_CORRIDOR_PARENT_TASK_CHECK.json';assert not dest.exists();tmp=Path(tempfile.mkdtemp(prefix='rear_parent_task_NO_PHYSICS_'));rows=[];negative=[];sources={}
geom=IndependentElbows(S/'elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf')
def save(status,**extra):
 p=dest.with_suffix('.tmp');p.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,negative_checks=negative,source_sha256=sources,fixture_root=str(tmp),training_ready=False,**extra),indent=2));p.replace(dest)
try:
 save('running');fixture=json.loads((W/'REAR_CORRIDOR_NATIVE_FIXTURE_CHECK.json').read_text())
 for case in fixture['cases']:
  if case['kind']=='wait':continue
  src=Path(case['fixture']);ep=tmp/src.name;shutil.copytree(src,ep);t=case['source_step'];coord=json.loads((ep/'coordination.json').read_text());actual=next(r for r in coord if r['step']==t);full=(ep/'coordination.json').read_bytes()
  # Native verifier requires full ordered coordinates. Run it before the sparse
  # independent original task function via a separate derived fixture below.
  from rear_corridor_audit_inputs import verify_inputs
  verified=verify_inputs(ep,ROOT,S)
  # Original task rows require valid task inputs for every row; all real previous
  # inputs are available in source history up to t. Use the original recorded
  # prefix and swap only this step's final expert goal to the emitted recovery.
  real=W/case['source_episode'];real_cs=json.loads((real/'coordination.json').read_text());real_ex=json.loads((real/'expert_control.json').read_text())
  from audit_rear_corridor_stage_pose_task_optimality import __file__ as audit_file
  # Exercise the exact function body with supplied, independently verified boundary
  # through AST extraction, replacing only the file-boundary constructor call.
  import ast,types
  import audit_rear_corridor_stage_pose_task_optimality as module
  tree=ast.parse(Path(audit_file).read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify_task_rows')
  assert ast.unparse(fn.body[1])=="recovery = verify_inputs(ep, repo, w / 'staged_rear_corridor_recovery_guarded')"
  fn.body[1]=ast.parse('recovery = supplied_boundary').body[0]
  # Its source assert hashes run against original synthetic boundary files. The
  # math-only fixture uses a separate path; no boundary file is edited.
  math_ep=tmp/(src.name+'_math');math_ep.mkdir()
  for n in ['raw.npz','expert_control.json']:shutil.copy2(ep/n,math_ep/n)
  (math_ep/'coordination.json').write_text(json.dumps([actual]));(math_ep/'self_clearance.json').write_text(json.dumps(dict(failure=None)))
  namespace=dict(vars(module),supplied_boundary=verified);exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(audit_file),'exec'),namespace)
  result=namespace['verify_task_rows'](math_ep,geom,{})
  assert result['passed'] and result['frames']==1,result
  ex=json.loads((math_ep/'expert_control.json').read_text());bad_bytes=(math_ep/'expert_control.json').read_bytes()
  parent=verified.parent_expert(t,ex[0]);(math_ep/'expert_control.json').write_text(json.dumps([parent]));baseline=original(math_ep,geom,{})
  for k in ['passed','errors','frames','overrides','max_kkt_residual','records']:assert result[k]==baseline[k],k
  (math_ep/'expert_control.json').write_bytes(bad_bytes)
  try:original(math_ep,geom,{})
  except AssertionError:negative.append(src.name+'_final_goal_cannot_replace_parent_task')
  else:raise AssertionError('expected changed task objective rejection')
  bad=json.loads((math_ep/'coordination.json').read_text());bad[0]['task_inputs']['previous'][0]+=.001;(math_ep/'coordination.json').write_text(json.dumps(bad))
  try:namespace['verify_task_rows'](math_ep,geom,{})
  except AssertionError:negative.append(src.name+'_actual_previous_action_tamper')
  else:raise AssertionError('previous action corruption accepted')
  verified.assert_unchanged();rows.append(dict(kind=case['kind'],key=case['key'],step=t,original_task_equal=True,stationarity=result['max_kkt_residual'],sparse_math_only=True));save('running');print(src.name,flush=True)
 for p in [Path(__file__),W/'audit_rear_corridor_stage_pose_task_optimality.py',W/'rear_corridor_audit_inputs.py',W/'REAR_CORRIDOR_NATIVE_FIXTURE_CHECK.json',W/'REAR_CORRIDOR_COMMAND_AUDITS_PREPARATION.json']:sources[str(p)]=sha(p)
 save('complete',passed=True)
except BaseException as e:save('check_failed',error=repr(e));raise
