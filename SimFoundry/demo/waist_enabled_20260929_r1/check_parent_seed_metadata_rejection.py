"""Reject edited retry histories; actual26 recovered histories are positive controls."""
from pathlib import Path
import sys,json,copy,hashlib,datetime
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w))
from audit_parent_seed_retry_metadata import verify_parent_seed_retry_metadata
# Read-only original checker function avoids its unrelated simulator imports.
import ast
src=w/'audit_joint_edge_retry_execution_live.py';tree=ast.parse(src.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify_retry_metadata');env={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(src),'exec'),env);original=env['verify_retry_metadata']
hp=w/'staged_rear_edge_parent_seed_probe/HISTORY_CHECK.json';history=json.loads(hp.read_text());valid=[];source=[hp,src,w/'audit_parent_seed_retry_metadata.py',Path(__file__)]
for episode in history['episodes']:
 if not episode['changed_rows']:continue
 name=episode['episode'];layout=name.split('_')[1];p=w/'recontact_interior_groups_r1'/('case_'+layout)/name/'coordination.json';cs={c['step']:c for c in json.loads(p.read_text())};source.append(p)
 for row in episode['changed_rows']:
  old=cs[row['step']]['joint_edge_refinement'];t=copy.deepcopy(old);t.update(override=True,reason='nonlinear_joint_direction',iterations=row['retry']['retry_iterations'],parent_seed_retry=row['retry']);t.pop('solver_status',None)
  verify_parent_seed_retry_metadata(t,enabled=True,analytic_enabled=True,eligible=True,mode='top_push',original_verifier=original);valid.append(t)
assert len(valid)==26
base=dict(enabled=True,analytic_enabled=True,eligible=True,mode='top_push',original_verifier=original);rejections=[]
def reject(name,edit=None,**options):
 t=copy.deepcopy(valid[0]);kwargs=dict(base);kwargs.update(options)
 if edit:edit(t)
 try:verify_parent_seed_retry_metadata(t,**kwargs)
 except AssertionError:rejections.append(name)
 else:raise AssertionError('accepted corrupt case '+name)
reject('undeclared_third_attempt',enabled=False)
reject('analytic_disabled',analytic_enabled=False)
reject('protected_unselected',eligible=False)
reject('non_push',mode='top_release')
reject('original_failure_rewritten',lambda t:t['analytic_retry'].update(retry_solver_status=0))
reject('original_failure_missing',lambda t:t.pop('analytic_retry'))
reject('parent_status_wrong',lambda t:t['parent_seed_retry'].update(prior_solver_status=9))
reject('iteration_link_mismatch',lambda t:t['parent_seed_retry'].update(prior_iterations=301))
reject('extra_attempts',lambda t:t['parent_seed_retry'].update(maximum_extra_retries=2))
reject('boolean_attempt_count',lambda t:t['parent_seed_retry'].update(maximum_extra_retries=True))
reject('wrong_initializer',lambda t:t['parent_seed_retry'].update(initializer='chosen_best_of_many'))
reject('failed_override',lambda t:t['parent_seed_retry'].update(retry_solver_status=8))
reject('iterations_too_many',lambda t:t['parent_seed_retry'].update(retry_iterations=301))
reject('hidden_fourth_attempt',lambda t:t['parent_seed_retry'].update(fourth_solver_status=0))
reject('final_iteration_mismatch',lambda t:t.update(iterations=301))
# Explicit finite-status failure and post-float32 rejection remain admissible
# metadata, but are non-overrides and cannot stand in for successful commands.
for reason,status in [('nonlinear_solver_failed',8),('final_float32_constraint_violation',0),('nonfinite_output',0)]:
 t=copy.deepcopy(valid[0]);t.update(override=False,reason=reason);t.pop('iterations',None);t['parent_seed_retry']['retry_solver_status']=status
 if status:t['solver_status']=status
 verify_parent_seed_retry_metadata(t,**base)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=dict(passed=True,actual_recovered_history_controls=len(valid),rejected_corrupt_metadata=rejections,accepted_explicit_non_override_branches=3,scope=__doc__,source_sha256={str(p):sha(p) for p in source},created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),physical_validation=False,training_ready=False);(w/'staged_rear_edge_parent_seed_probe/METADATA_REJECTION_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',len(valid),'actual metadata controls,',len(rejections),'corrupt cases rejected')
