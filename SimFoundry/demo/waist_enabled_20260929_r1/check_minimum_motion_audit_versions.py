"""New audit identity/source rejection and unchanged original mathematical bodies.
Metadata fixtures are synthetic and never physical or training evidence.
"""
from pathlib import Path
import ast,copy,json,hashlib,sys,tempfile,shutil
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_minimum_motion_recontact';sys.path[:0]=[str(w),str(repo)];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();mapping=json.loads((w/'MINIMUM_MOTION_AUDIT_VERSION_MAP.json').read_text());sources={};pairs=[]
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s
def function(s,name):return next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name==name)
for a,b in mapping.items():
 if a.endswith('.json') or a.startswith('staged_') or a=='verify_parent_seed_source':continue
 old=rename((w/(a+'.py')).read_text());new=(w/(b+'.py')).read_text();sources[str(w/(a+'.py'))]=sha(w/(a+'.py'));sources[str(w/(b+'.py'))]=sha(w/(b+'.py'))
 if a=='audit_parent_seed_source_contract':continue
 if a=='audit_parent_seed_pose_live':
  before=function(old,'verify_files');after=function(new,'verify_files');extra=[n for n in after.body if isinstance(n,ast.For) and ast.unparse(n.target)=='raw' and ast.unparse(n.iter)=='evs.values()'];assert len(extra)==1;after.body.remove(extra[0]);assert ast.dump(before)==ast.dump(after);pairs.append([a,b,'native_math_plus_required_new_metadata']);continue
 if a=='audit_parent_seed_pose_loaded_execution':
  for name in ['verify_refinement','verify_retry_metadata','near']:assert ast.dump(function(old,name))==ast.dump(function(new,name))
  restored=new.replace(" from audit_minimum_motion_loaded_parent import build_parent_verifier\n loaded_parent,task_evidence=build_parent_verifier(ep,expected_collector.parent)\n",'').replace("   loaded_parent(c,f,ex[t],q[t],u[t-1],parent,side,solver);parent_count+=1","   assert c['self_clearance_task']['accepted'] is True and c['self_clearance_task']['override'] is False, 'Changed loaded task IK requires dedicated nonlinear task execution audit'\n   replay_record(c,f,ex[t],q[t],u[t-1],parent,side,solver);parent_count+=1").replace(',nonlinear_task_execution=task_evidence','');assert ast.dump(function(old,'replay'))==ast.dump(function(restored,'replay'));assert ast.dump(function(old,'inspect'))==ast.dump(function(new,'inspect'));pairs.append([a,b,'edge_math_and_explicit_task_parent_extension']);continue
 assert ast.dump(ast.parse(old))==ast.dump(ast.parse(new)),(a,b);pairs.append([a,b,'whole_module_parity'])
assert len(pairs)==15
# New helper branch is exactly the previously checked supplementary branch.
old_tree=ast.parse((w/'audit_parent_seed_loaded_task_supplement.py').read_text());new_tree=ast.parse((w/'audit_minimum_motion_loaded_parent.py').read_text());before=copy.deepcopy(next(n for n in ast.walk(old_tree) if isinstance(n,ast.FunctionDef) and n.name=='loaded_parent'));after=next(n for n in ast.walk(new_tree) if isinstance(n,ast.FunctionDef) and n.name=='loaded_parent')
class Normalize(ast.NodeTransformer):
 def visit_Attribute(self,n):
  if isinstance(n.value,ast.Name) and n.value.id=='original' and n.attr in ['near','replay_record']:return ast.Name(id=n.attr,ctx=n.ctx)
  return self.generic_visit(n)
 def visit_Name(self,n):
  if n.id=='checked':return ast.Subscript(value=ast.Name(id='evidence',ctx=ast.Load()),slice=ast.Constant(value='loaded_task_overrides_checked'),ctx=n.ctx)
  return n
assert ast.dump(Normalize().visit(before))==ast.dump(after),'task-parent extension differs from tested supplement'
from audit_minimum_motion_source_contract import verify_minimum_motion_source
root=Path(tempfile.mkdtemp(prefix='minimum_motion_METADATA_ONLY_'));case=root/'case';ep=case/'SYNTHETIC_NOT_PHYSICS';ep.mkdir(parents=True);snap=case/'source_snapshot';source={}
filenames=['collect_paired_sorting.py','waist_coordination_clearance.py','task_ik.py','task_ik_precision.py','joint_edge_command.py','joint_edge_adapter.py','recontact_plan.py','recontact_lifecycle.py','minimum_motion_recontact.py','minimum_motion_lifecycle.py']
for n in filenames:
 dst=snap/'candidate'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(stage/n,dst);source['candidate/'+n]=sha(dst)
args={k:True for k in ['minimum_motion_recontact','rear_joint_edge_parent_seed_retry','rear_joint_edge_analytic_retry','precise_clearance_task_ik','self_clearance_task_ik','unloaded_recontact_pose','recontact_interior_preference']};prov=dict(args=args,source_sha256=source);meta=dict(minimum_motion_recontact=True,rear_joint_edge_parent_seed_retry=True,task_ik_optimizer_ftol=1e-13,self_clearance_task_ik=True,unloaded_recontact_pose=True,recontact_interior_preference=True)
retry=dict(enabled=True,prior_solver_status=8,finite_endpoint_required=True,maximum_extra_retries=1,initializer='bounded_parent_delta',original_attempts_preserved=True,objective_bounds_tolerances_unchanged=True,failed_retry='preserve_parent_command');motion=dict(enabled=True,alignment_abs_min=.8,preferred_inset_m=.020,seed_policy=['original_endpoint','current_observed'],lift_heights_m=[.015,.030,.060],original_fallback=True,whole_sampled_path_check=True,maximum_ticks=240,training_ready=False);plan=dict(rear_joint_edge_command=dict(enabled=True),rear_joint_edge_parent_seed_retry=retry,rear_joint_xy_progress=dict(enabled=True),unloaded_recontact_pose=dict(minimum_motion_pose=motion))
def write(p,m,f):
 (case/'provenance.json').write_text(json.dumps(p));np.savez(ep/'raw.npz',collect_meta=json.dumps(m));(ep/'frontal_bypass.json').write_text(json.dumps(dict(plan=f)))
write(prov,meta,plan);assert verify_minimum_motion_source(ep)['passed'];bad=[]
changes={
 'disabled_flag':lambda p,m,f:p['args'].__setitem__('minimum_motion_recontact',False),
 'missing_flag':lambda p,m,f:p['args'].pop('minimum_motion_recontact'),
 'missing_raw':lambda p,m,f:m.pop('minimum_motion_recontact'),
 'wrong_raw':lambda p,m,f:m.__setitem__('minimum_motion_recontact',False),
 'missing_helper':lambda p,m,f:p['source_sha256'].pop('candidate/minimum_motion_recontact.py'),
 'duplicate_helper':lambda p,m,f:p['source_sha256'].__setitem__('extra/minimum_motion_recontact.py',source['candidate/minimum_motion_recontact.py']),
 'wrong_helper_hash':lambda p,m,f:p['source_sha256'].__setitem__('candidate/minimum_motion_lifecycle.py','0'*64),
 'missing_plan':lambda p,m,f:f['unloaded_recontact_pose'].pop('minimum_motion_pose'),
 'changed_alignment':lambda p,m,f:f['unloaded_recontact_pose']['minimum_motion_pose'].__setitem__('alignment_abs_min',.5),
 'future_seed':lambda p,m,f:f['unloaded_recontact_pose']['minimum_motion_pose'].__setitem__('seed_policy',['future_state']),
 'extended_budget':lambda p,m,f:f['unloaded_recontact_pose']['minimum_motion_pose'].__setitem__('maximum_ticks',400),
 'bool_budget':lambda p,m,f:f['unloaded_recontact_pose']['minimum_motion_pose'].__setitem__('maximum_ticks',True),
 'skipped_path':lambda p,m,f:f['unloaded_recontact_pose']['minimum_motion_pose'].__setitem__('whole_sampled_path_check',False),
 'not_selected_plan':lambda p,m,f:f['rear_joint_xy_progress'].__setitem__('enabled',False),
}
for name,change in changes.items():
 p,m,f=copy.deepcopy((prov,meta,plan));change(p,m,f);write(p,m,f)
 try:verify_minimum_motion_source(ep)
 except (AssertionError,KeyError):bad.append(name)
 else:raise AssertionError('corruption accepted '+name)
for n in ['collect_paired_sorting.py','recontact_plan.py']:
 dst=snap/'candidate'/n;shutil.copyfile(w/'staged_precise_parent_seed'/n,dst);p=copy.deepcopy(prov);p['source_sha256']['candidate/'+n]=sha(dst);write(p,meta,plan)
 try:verify_minimum_motion_source(ep)
 except AssertionError:bad.append('consistent_legacy_'+n)
 else:raise AssertionError('legacy accepted '+n)
 shutil.copyfile(stage/n,dst)
write(prov,meta,{});assert verify_minimum_motion_source(ep)['passed'];(ep/'frontal_bypass.json').unlink();assert verify_minimum_motion_source(ep)['passed'];legacy=[]
for e in (w/'parent_seed_groups_r1').glob('case_*/layout_*'):
 if not (e/'raw.npz').exists():continue
 try:verify_minimum_motion_source(e)
 except AssertionError as exc:assert str(exc)=='minimum-motion flag missing/disabled';legacy.append(e.name)
 else:raise AssertionError('actual legacy admitted')
assert len(legacy)==10
for p in [Path(__file__),w/'MINIMUM_MOTION_AUDIT_VERSION_MAP.json',w/'audit_minimum_motion_loaded_parent.py',w/'audit_parent_seed_loaded_task_supplement.py',w/'PARENT_SEED_LOADED_TASK_SUPPLEMENT.json',w/'PARENT_SEED_LOADED_SUPPLEMENT_CONTROL.json',stage/'INTEGRATION_CHECK.json',stage/'PRELAUNCH_CHECK.json',*[stage/n for n in filenames]]:sources[str(p)]=sha(p)
out=dict(passed=True,scope=__doc__,mathematical_version_pairs=pairs,tested_loaded_extension_ast_exact=True,synthetic_metadata_fixture=str(root),metadata_corruptions_rejected=bad,actual_parent_episodes_rejected=legacy,source_sha256=sources,physical_validation=False,training_ready=False);(stage/'AUDIT_VERSION_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS15 versions, tested task-parent parity,16 corrupt metadata,10 actual parent rejected')
