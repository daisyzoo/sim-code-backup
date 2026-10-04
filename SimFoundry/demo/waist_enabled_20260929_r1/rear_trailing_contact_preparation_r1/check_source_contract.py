"""Source/settings archive-only fixture. No invented raw or physics success."""
from pathlib import Path
import sys,json,hashlib,datetime,tempfile,copy
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_rear_trailing_contact_v1';sys.path[:0]=[str(D),str(W),str(ROOT)]
from source_binding import verify_preparation,verify_trial_provenance
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();expected,bound=verify_preparation();negative=[]
def reject(label,fn):
 try:fn()
 except (AssertionError,ValueError,KeyError,FileNotFoundError):negative.append(label)
 else:raise AssertionError('Invalid source contract accepted '+label)
for run in ['front_box_recenter_physical_r2','joint_transport_physical_r1']:reject('old_run_'+run,lambda:verify_trial_provenance(W/run/'case_841011'))
parent=W/'joint_transport_physical_r1/case_841011/provenance.json';prov=json.loads(parent.read_text());old_prefix='demo/waist_enabled_20260929_r1/staged_joint_transport_v1/';prefix=str(S.relative_to(ROOT))+'/'
prov['source_sha256']={n:h for n,h in prov['source_sha256'].items() if not n.startswith(old_prefix)};prov['source_sha256'].update({prefix+n:h for n,h in expected.items()});prov['args']['rear_box_trailing_preference']=True
with tempfile.TemporaryDirectory(prefix='rear_trailing_source_only_',dir='/tmp') as td:
 case=Path(td);prov['args']['out_dir']=str(case);source_names=sorted(prov['source_sha256'])
 for n,h in prov['source_sha256'].items():
  p=ROOT/n;assert sha(p)==h;dest=case/'source_snapshot'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 p=case/'provenance.json'
 def write(a):p.write_text(json.dumps(a,indent=2))
 write(prov);verified,_=verify_trial_provenance(case);assert verified==prov
 for label in ['missing_runtime','bad_hash','disabled','changed_step_budget','wrong_role','wrong_collector']:
  bad=copy.deepcopy(prov)
  if label=='missing_runtime':bad['source_sha256'].pop(prefix+'trailing_offset_solver.py')
  elif label=='bad_hash':bad['source_sha256'][prefix+'trailing_contact_plan.py']='0'*64
  elif label=='disabled':bad['args']['rear_box_trailing_preference']=False
  elif label=='changed_step_budget':bad['args']['steps']=2400
  elif label=='wrong_role':bad['args']['role']='pilot'
  elif label=='wrong_collector':bad['source_sha256'][old_prefix+'collect_paired_sorting.py']=sha(ROOT/old_prefix/'collect_paired_sorting.py')
  write(bad);reject(label,lambda:verify_trial_provenance(case))
 write(prov);snapshot=case/'source_snapshot'/prefix/'trailing_contact_plan.py';original=snapshot.read_bytes();snapshot.write_bytes(original+b'\n# altered\n');reject('changed_archived_bytes',lambda:verify_trial_provenance(case));snapshot.write_bytes(original);verify_trial_provenance(case)
 fixture_path=str(case)
assert not Path(fixture_path).exists()
for p in [Path(__file__),D/'source_binding.py',parent]:bound[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,active_stage_sources=len(expected),archived_source_count=len(source_names),old_sources_and_mutations_rejected=negative,fixture_removed=True,no_raw_fixture=True,source_sha256=bound,full_physical_stream_audit_pending=True,physical_launch_ready=False,training_ready=False)
with (D/'SOURCE_CONTRACT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,active_stage_sources=len(expected),negative=len(negative),fixture_removed=True)),flush=True)
