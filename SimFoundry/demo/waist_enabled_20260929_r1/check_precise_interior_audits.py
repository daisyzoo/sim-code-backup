"""Explicit mathematical parity and precision source/metadata rejection cases.
Temporary fixtures contain source files and synthetic metadata only, not robot
trajectories or new physical evidence. Old actual5N recordings must be rejected
by this precision-specific source contract. Never changes old reports or gates.
"""
from pathlib import Path
import ast,json,hashlib,sys,copy,tempfile,shutil,datetime
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)];stage=w/'staged_interior_task_precision';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();mapping=json.loads((w/'PRECISE_INTERIOR_AUDIT_VERSION_MAP.json').read_text())
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s
class StripBinding(ast.NodeTransformer):
 def visit_ImportFrom(self,n):
  if n.module=='audit_precision_source_contract':assert [(x.name,x.asname) for x in n.names]==[('verify_precision_source',None)];return None
  return n
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='verify_precision_source':assert ast.unparse(n.value)=='verify_precision_source(ep)';return None
  return self.generic_visit(n)
pairs=[];sources={}
for old,new in mapping.items():
 if old.endswith('.json') or old=='staged_recontact_interior':continue
 a=w/(old+'.py');b=w/(new+'.py');before=ast.parse(rename(a.read_text()));after=ast.parse(b.read_text());assert ast.dump(before,include_attributes=False)==ast.dump(StripBinding().visit(after),include_attributes=False),(old,new)
 pairs.append([old,new]);sources[str(a)]=sha(a);sources[str(b)]=sha(b)
from audit_precision_source_contract import verify_precision_source
root=Path(tempfile.mkdtemp(prefix='precision_source_METADATA_ONLY_'));case=root/'case';ep=case/'SYNTHETIC_NOT_PHYSICS';ep.mkdir(parents=True);snap=case/'source_snapshot';snap.mkdir();filenames=['collect_paired_sorting.py','waist_coordination_clearance.py','task_ik.py','task_ik_precision.py'];source={}
for name in filenames:
 dst=snap/'candidate'/name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(stage/name,dst);source['candidate/'+name]=sha(dst)
baseprov=dict(args=dict(precise_clearance_task_ik=True,self_clearance_task_ik=True,unloaded_recontact_pose=True,recontact_interior_preference=True),source_sha256=source)
basemeta=dict(task_ik_optimizer_ftol=1e-13,self_clearance_task_ik=True,unloaded_recontact_pose=True,recontact_interior_preference=True)
def write(prov,meta):
 (case/'provenance.json').write_text(json.dumps(prov));np.savez(ep/'raw.npz',collect_meta=json.dumps(meta))
write(baseprov,basemeta);positive=verify_precision_source(ep);assert positive['passed'];reject=[]
changes={
 'disabled_flag':lambda p,m:p['args'].__setitem__('precise_clearance_task_ik',False),
 'missing_flag':lambda p,m:p['args'].pop('precise_clearance_task_ik'),
 'inactive_clearance':lambda p,m:p['args'].__setitem__('self_clearance_task_ik',False),
 'inactive_recontact':lambda p,m:p['args'].__setitem__('unloaded_recontact_pose',False),
 'wrong_raw_tolerance':lambda p,m:m.__setitem__('task_ik_optimizer_ftol',1e-11),
 'missing_raw_tolerance':lambda p,m:m.pop('task_ik_optimizer_ftol'),
 'disabled_raw_precision_path':lambda p,m:m.__setitem__('recontact_interior_preference',False),
 'missing_solver_source':lambda p,m:p['source_sha256'].pop('candidate/task_ik_precision.py'),
 'false_solver_hash':lambda p,m:p['source_sha256'].__setitem__('candidate/task_ik_precision.py','0'*64),
 'duplicate_solver':lambda p,m:p['source_sha256'].__setitem__('extra/task_ik_precision.py',source['candidate/task_ik_precision.py']),
}
for name,change in changes.items():
 prov=copy.deepcopy(baseprov);meta=copy.deepcopy(basemeta);change(prov,meta);write(prov,meta)
 try:verify_precision_source(ep)
 except (AssertionError,KeyError):reject.append(name)
 else:raise AssertionError('Accepted '+name)
# A legacy solver relabeled with its true hash must not pass as precision code.
dst=snap/'candidate/task_ik_precision.py';dst.write_bytes((stage/'task_ik.py').read_bytes());prov=copy.deepcopy(baseprov);prov['source_sha256']['candidate/task_ik_precision.py']=sha(dst);write(prov,basemeta)
try:verify_precision_source(ep)
except AssertionError:reject.append('legacy_solver_with_consistent_hash')
else:raise AssertionError('Accepted legacy solver')
shutil.copyfile(stage/'task_ik_precision.py',dst);write(baseprov,basemeta)
old_rejected=[]
for old_ep in sorted((w/'recontact_interior_groups_r1').glob('case_*/layout_*')):
 if not (old_ep/'quality.json').exists():continue
 try:verify_precision_source(old_ep)
 except AssertionError as exc:assert str(exc)=='precision flag missing/disabled';old_rejected.append(old_ep.name)
 else:raise AssertionError('Relabeled physical parent accepted')
assert len(old_rejected)==10
for p in [Path(__file__),w/'PRECISE_INTERIOR_AUDIT_VERSION_MAP.json',w/'audit_precision_source_contract.py',stage/'INTEGRATION_CHECK.json',stage/'PRELAUNCH_CHECK.json',*[stage/n for n in filenames]]:sources[str(p)]=sha(p)
out=dict(passed=True,scope=__doc__,checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),mathematical_version_pairs=pairs,only_extra_assertions='precision source/flag/raw-metadata binding',synthetic_metadata_fixture=str(root),source_fixture_positive=True,rejected_corruptions=reject,old_actual_nonprecision_episodes_rejected=old_rejected,source_sha256=sources,physical_validation=False,training_ready=False)
(stage/'AUDIT_VERSION_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',len(pairs),'math-identical versions',len(reject),'corruptions',len(old_rejected),'actual5N mismatches rejected')
