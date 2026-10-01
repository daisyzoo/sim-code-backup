"""Prove unchanged numerical audit bodies and reject mislabeled retry provenance.
Source fixtures contain synthetic metadata only; they are not physical data.
"""
from pathlib import Path
import ast,json,hashlib,sys,copy,tempfile,shutil,datetime
import numpy as np
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w));stage=w/'staged_precise_parent_seed';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();mapping=json.loads((w/'PARENT_SEED_AUDIT_VERSION_MAP.json').read_text())
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s
pairs=[];sources={}
for a,b in mapping.items():
 if a.endswith('.json') or a.startswith('staged_') or a in ['verify_precision_source','audit_precision_source_contract']:continue
 before=rename((w/(a+'.py')).read_text());after=(w/(b+'.py')).read_text()
 if a=='audit_precise_interior_pose_loaded_execution':
  # Only source path, declared metadata verifier and count fields may differ.
  after=after.replace('from audit_parent_seed_retry_metadata import verify_parent_seed_retry_metadata\n','')
  after=after.replace("else w/'staged_precise_parent_seed'/name","else w/'staged_micro_clearance_return'/name")
  after=after.replace("  verify_parent_seed_retry_metadata(trace,enabled=args['rear_joint_edge_parent_seed_retry'],analytic_enabled=retry_enabled,eligible=bool(eligible),mode=f['mode'],original_verifier=verify_retry_metadata)","  verify_retry_metadata(trace,retry_enabled,eligible,f['mode'])")
  after=after.replace(' from audit_parent_seed_source_contract import verify_parent_seed_source\n verify_parent_seed_source(ep)\n','')
  after=after.replace(",parent_seed_retry_attempts=sum(bool(c.get('joint_edge_refinement',{}).get('parent_seed_retry')) for c in coords)",'')
 assert ast.dump(ast.parse(before),include_attributes=False)==ast.dump(ast.parse(after),include_attributes=False),(a,b)
 pairs.append([a,b]);sources[str(w/(a+'.py'))]=sha(w/(a+'.py'));sources[str(w/(b+'.py'))]=sha(w/(b+'.py'))
assert len(pairs)==15
from audit_parent_seed_source_contract import verify_parent_seed_source
root=Path(tempfile.mkdtemp(prefix='parent_seed_METADATA_ONLY_'));case=root/'case';ep=case/'SYNTHETIC_NOT_PHYSICS';ep.mkdir(parents=True);snap=case/'source_snapshot';snap.mkdir();filenames=['collect_paired_sorting.py','waist_coordination_clearance.py','task_ik.py','task_ik_precision.py','joint_edge_command.py','joint_edge_adapter.py'];source={}
for name in filenames:
 dst=snap/'candidate'/name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(stage/name,dst);source['candidate/'+name]=sha(dst)
baseprov=dict(args=dict(rear_joint_edge_parent_seed_retry=True,rear_joint_edge_analytic_retry=True,precise_clearance_task_ik=True,self_clearance_task_ik=True,unloaded_recontact_pose=True,recontact_interior_preference=True),source_sha256=source)
basemeta=dict(rear_joint_edge_parent_seed_retry=True,task_ik_optimizer_ftol=1e-13,self_clearance_task_ik=True,unloaded_recontact_pose=True,recontact_interior_preference=True)
config=dict(enabled=True,prior_solver_status=8,finite_endpoint_required=True,maximum_extra_retries=1,initializer='bounded_parent_delta',original_attempts_preserved=True,objective_bounds_tolerances_unchanged=True,failed_retry='preserve_parent_command');baseplan=dict(rear_joint_edge_command=dict(enabled=True),rear_joint_edge_parent_seed_retry=config)
def write(prov,meta,plan):
 (case/'provenance.json').write_text(json.dumps(prov));np.savez(ep/'raw.npz',collect_meta=json.dumps(meta));(ep/'frontal_bypass.json').write_text(json.dumps(dict(plan=plan)))
write(baseprov,basemeta,baseplan);assert verify_parent_seed_source(ep)['passed'];reject=[]
changes={
 'disabled_flag':lambda p,m,f:p['args'].__setitem__('rear_joint_edge_parent_seed_retry',False),
 'missing_flag':lambda p,m,f:p['args'].pop('rear_joint_edge_parent_seed_retry'),
 'disabled_analytic':lambda p,m,f:p['args'].__setitem__('rear_joint_edge_analytic_retry',False),
 'disabled_precision':lambda p,m,f:p['args'].__setitem__('precise_clearance_task_ik',False),
 'wrong_raw_tolerance':lambda p,m,f:m.__setitem__('task_ik_optimizer_ftol',1e-11),
 'missing_raw_flag':lambda p,m,f:m.pop('rear_joint_edge_parent_seed_retry'),
 'false_raw_flag':lambda p,m,f:m.__setitem__('rear_joint_edge_parent_seed_retry',False),
 'missing_helper':lambda p,m,f:p['source_sha256'].pop('candidate/joint_edge_command.py'),
 'false_helper_hash':lambda p,m,f:p['source_sha256'].__setitem__('candidate/joint_edge_command.py','0'*64),
 'duplicate_helper':lambda p,m,f:p['source_sha256'].__setitem__('extra/joint_edge_command.py',source['candidate/joint_edge_command.py']),
 'missing_plan':lambda p,m,f:f.pop('rear_joint_edge_parent_seed_retry'),
 'wrong_plan_initializer':lambda p,m,f:f['rear_joint_edge_parent_seed_retry'].__setitem__('initializer','best_of_many'),
 'extra_attempts':lambda p,m,f:f['rear_joint_edge_parent_seed_retry'].__setitem__('maximum_extra_retries',2),
 'bool_attempt_count':lambda p,m,f:f['rear_joint_edge_parent_seed_retry'].__setitem__('maximum_extra_retries',True),
 'nonselected_declared_plan':lambda p,m,f:f['rear_joint_edge_command'].__setitem__('enabled',False),
}
for name,change in changes.items():
 p,m,f=copy.deepcopy((baseprov,basemeta,baseplan));change(p,m,f);write(p,m,f)
 try:verify_parent_seed_source(ep)
 except (AssertionError,KeyError):reject.append(name)
 else:raise AssertionError('Accepted '+name)
for name in ['joint_edge_command.py','joint_edge_adapter.py','collect_paired_sorting.py']:
 dst=snap/'candidate'/name;dst.write_bytes((w/'staged_interior_task_precision'/name).read_bytes());p=copy.deepcopy(baseprov);p['source_sha256']['candidate/'+name]=sha(dst);write(p,basemeta,baseplan)
 try:verify_parent_seed_source(ep)
 except AssertionError:reject.append('legacy_consistent_hash_'+name)
 else:raise AssertionError('Accepted legacy '+name)
 shutil.copyfile(stage/name,dst)
# Valid no-selected-branch and wait records still require source/CLI/raw binding.
write(baseprov,basemeta,{});assert verify_parent_seed_source(ep)['passed'];(ep/'frontal_bypass.json').unlink();assert verify_parent_seed_source(ep)['passed']
old_rejected=[]
for old_ep in sorted((w/'precise_interior_groups_r1').glob('case_*/layout_*')):
 if not (old_ep/'quality.json').exists():continue
 try:verify_parent_seed_source(old_ep)
 except AssertionError as exc:assert str(exc)=='parent-seed flag missing/disabled';old_rejected.append(old_ep.name)
 else:raise AssertionError('Relabeled actual parent accepted')
assert len(old_rejected)==10
for p in [Path(__file__),w/'PARENT_SEED_AUDIT_VERSION_MAP.json',w/'audit_parent_seed_source_contract.py',w/'audit_parent_seed_retry_metadata.py',stage/'INTEGRATION_CHECK.json',stage/'PRELAUNCH_CHECK.json',*[stage/n for n in filenames]]:sources[str(p)]=sha(p)
out=dict(passed=True,scope=__doc__,checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),mathematical_version_pairs=pairs,synthetic_metadata_fixture=str(root),source_fixture_positive=True,rejected_corruptions=reject,old_actual_precise_episodes_rejected=old_rejected,source_sha256=sources,physical_validation=False,training_ready=False);(stage/'AUDIT_VERSION_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',len(pairs),'numerical parity versions',len(reject),'corruptions',len(old_rejected),'actual parent rejected')
