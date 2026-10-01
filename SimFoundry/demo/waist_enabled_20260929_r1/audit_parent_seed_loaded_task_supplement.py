"""Supplemental full loaded execution audit with independently checked task IK.
Never changes the frozen run/auditor or its rejected official report. This
separate diagnostic adds a checked task-candidate->slew->edge->raw chain.
All original loaded reconstruction/refinement mathematics remain unchanged.
"""
from pathlib import Path
import ast,copy,json,sys,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
import audit_parent_seed_pose_loaded_execution as original
from audit_parent_seed_pose_task_optimality import verify_task_rows,IndependentElbows
from audit_parent_seed_pose_live import inspect as inspect_pose,source_contract
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def extended_replay(ep):
 ep=Path(ep).resolve();stage=source_contract(ep);pose=inspect_pose(ep);assert pose==json.loads((ep/'PARENT_SEED_POSE_LIVE_AUDIT.json').read_text())
 geometry=json.loads((ep/'PARENT_SEED_POSE_SELF_CLEARANCE_AUDIT.json').read_text());assert geometry['passed'] and geometry['episode_clearance_passed'];assert geometry['auditor_sha256']==sha(w/'audit_parent_seed_pose_self_clearance.py')
 for name,h in geometry['source_sha256'].items():assert sha(ep/name)==h
 events={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'recontact_pose.json').read_text())['rows'] if r['kind'] in ('command','handover')};assert set(events)=={r['step'] for r in pose['records']}
 geom=IndependentElbows(stage/'elbow_torso_hulls.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf');task=verify_task_rows(ep,geom,events);assert task['passed'],task['errors'];task_records={r['step']:r for r in task['records']};checked=[]
 def loaded_parent(c,f,expert,q,previous,parent,side,solver):
  tr=c['self_clearance_task'];assert tr['accepted'] is True and type(tr['override']) is bool
  if not tr['override']:return original.replay_record(c,f,expert,q,previous,parent,side,solver)
  proof=task_records[c['step']];assert proof['override'] and proof['stationary'] and proof['kkt_residual']<=1e-6
  inp=c['task_inputs'];candidate=np.asarray(tr['candidate_command'],dtype=np.float32);assert np.array_equal(candidate,np.asarray(tr['candidate_command']));assert tr['solver_success'] is True and tr['status']==0
  # Original replay independently reconstructs all loaded inputs and final
  # float32 slew/limits. Callback accepts only exactly bound task inputs.
  def task_delta(J,E,current,lower,upper,limits,damping,*,preferred_step):
   for value,key in [(J,'jacobian'),(E,'error'),(current,'current'),(lower,'lower'),(upper,'upper'),(limits,'step_limits'),(damping,'damping'),(preferred_step,'preferred_step')]:original.near(value,inp[key],0)
   baseline=(current+solver(J,E,current,lower,upper,limits,damping,preferred_step=preferred_step)).astype(np.float32);original.near(baseline,tr['parent_command'],0);original.near(previous,tr['previous_command'],0)
   return (candidate-current).astype(np.float32)
  out=original.replay_record(c,f,expert,q,previous,parent,side,task_delta)
  checked.append(dict(step=c['step'],task_kkt_residual=proof['kkt_residual'],task_to_parent_max_action_error_rad=out['max_action_error_rad']))
  return out
 # The sole code difference is a verified extension at the original explicit
 # rejection point. Structural checks ensure no other audit mathematics change.
 path=w/'audit_parent_seed_pose_loaded_execution.py';tree=ast.parse(path.read_text());func=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='replay'));before=copy.deepcopy(func);matches=[]
 for node in ast.walk(func):
  if isinstance(node,ast.If) and ast.unparse(node.test)=="f['mode'] == 'top_push'":matches.append(node)
 assert len(matches)==1;block=matches[0];assert len(block.body)==3 and isinstance(block.body[0],ast.Assert) and block.body[0].msg.value=='Changed loaded task IK requires dedicated nonlinear task execution audit'
 assert ast.unparse(block.body[1])=='replay_record(c, f, ex[t], q[t], u[t - 1], parent, side, solver)';assert ast.unparse(block.body[2])=='parent_count += 1'
 old_body=copy.deepcopy(block.body);block.body=ast.parse('loaded_parent(c,f,ex[t],q[t],u[t-1],parent,side,solver)\nparent_count+=1').body;modified=copy.deepcopy(func);block.body=old_body;assert ast.dump(func)==ast.dump(before)
 ns=vars(original).copy();ns['loaded_parent']=loaded_parent;exec(compile(ast.fix_missing_locations(ast.Module(body=[modified],type_ignores=[])),str(Path(__file__)), 'exec'),ns);out=ns['replay'](ep,stage/'collect_paired_sorting.py')
 # Corrupt the new branch at each connection. Full task numerical proof was
 # separately recomputed above; no candidate nonlinear solver imported/run.
 cs={c['step']:c for c in json.loads((ep/'coordination.json').read_text())};fs={f['step']:f for f in json.loads((ep/'frontal_bypass.json').read_text())['rows']};es={e['step']:e for e in json.loads((ep/'expert_control.json').read_text())};rejections=[]
 if checked:
  from simfoundry.data.bounded_ik import bounded_damped_step
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(np.float32);u=z['action'][:,12:23].astype(np.float32)
  t=checked[0]['step'];c0=cs[t];parent=np.asarray(c0['joint_edge_refinement']['parent_final_upper_command'],dtype=np.float32);side='right' if 'push_box' in ep.name else 'left'
  cases=['candidate','task_error','parent_baseline','previous','actual_parent','task_status']
  for name in cases:
   c=copy.deepcopy(c0);actual=parent.copy()
   if name=='candidate':c['self_clearance_task']['candidate_command'][1]=float(np.float32(c['self_clearance_task']['candidate_command'][1]+.001))
   elif name=='task_error':c['task_inputs']['error'][0]+=.001
   elif name=='parent_baseline':c['self_clearance_task']['parent_command'][1]+=.001
   elif name=='previous':c['self_clearance_task']['previous_command'][1]+=.001
   elif name=='actual_parent':actual[1]+=.001
   elif name=='task_status':c['self_clearance_task']['status']=8
   try:loaded_parent(c,fs[t],es[t],q[t],u[t-1],actual,side,bounded_damped_step)
   except (AssertionError,ValueError):rejections.append(name)
   else:raise AssertionError(('corruption not rejected',name))
 out.update(scope=__doc__,supplemental_only=True,original_official_audit_unchanged=True,loaded_task_overrides_checked=checked,independent_task_frames=task['frames'],independent_task_max_kkt=task['max_kkt_residual'],branch_corruption_rejections=rejections,source_version_sha256={str(p):sha(p) for p in [Path(__file__),path,w/'audit_parent_seed_pose_task_optimality.py',w/'audit_parent_seed_pose_live.py',w/'audit_rear_coupled_execution_live.py']})
 return out
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=extended_replay(ep);dest=w/'PARENT_SEED_LOADED_TASK_SUPPLEMENT.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['records','source_sha256','scope']})
