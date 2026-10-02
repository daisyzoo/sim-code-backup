"""Synthetic provenance-only archive of actual current sources, no simulated observations.
Positive source binding and changed argument/archive rejection do not certify physics.
"""
from pathlib import Path
import sys,json,hashlib,tempfile,datetime,copy,ast
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_initial_center';sys.path[:0]=[str(W),str(ROOT)]
from front_initial_center_stage_source_binding import verify_trial_provenance
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=W/'FRONT_INITIAL_CENTER_SOURCE_POSITIVE_CHECK.json';assert not out.exists()
parent=W/'terminal_margin_physical_r1/case_840014/provenance.json';original=json.loads(parent.read_text());prep=json.loads((S/'PREPARATION.json').read_text());sources={};old=str((W/'staged_terminal_release_margin').relative_to(ROOT))+'/';new=str(S.relative_to(ROOT))+'/'
for name in original['source_sha256']:
 name=new+name[len(old):] if name.startswith(old) else name;sources[name]=sha(ROOT/name)
for name,h in prep['stage_sha256'].items():sources[new+name]=h
args=copy.deepcopy(original['args']);args['front_initial_center_landing']=True
record=dict(status='running',scope=__doc__,source_files=len(sources),positive=False,negative_cases=[],simulation_started=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),parent,S/'PREPARATION.json',W/'front_initial_center_stage_source_binding.py']})
def save():record['updated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();out.write_text(json.dumps(record,indent=2))
try:
 with tempfile.TemporaryDirectory(prefix='front-source-fixture-') as temp:
  case=Path(temp);prov=dict(args=args,source_sha256=sources,fixture_only=True,physics='NONE: synthetic provenance source fixture')
  for name in sources:
   dest=case/'source_snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
  def write(): (case/'provenance.json').write_text(json.dumps(prov))
  write();verify_trial_provenance(case);record['positive']=True;save()
  for label in ['flag_disabled','waist_range_changed','horizon_changed','assistance_enabled','archive_changed','helper_missing']:
   prov=dict(args=copy.deepcopy(args),source_sha256=copy.deepcopy(sources),fixture_only=True)
   target=case/'source_snapshot'/new/'front_initial_center_runtime.py';original_bytes=target.read_bytes()
   if label=='flag_disabled':prov['args']['front_initial_center_landing']=False
   if label=='waist_range_changed':prov['args']['waist_limit_rad']=1.1
   if label=='horizon_changed':prov['args']['steps']=1199
   if label=='assistance_enabled':prov['args']['push_assist']=True
   if label=='archive_changed':target.write_bytes(original_bytes+b'\n# forged fixture\n')
   if label=='helper_missing':del prov['source_sha256'][new+'front_initial_center_runtime.py']
   write();rejected=False
   try:verify_trial_provenance(case)
   except (AssertionError,ValueError,KeyError):rejected=True
   finally:target.write_bytes(original_bytes)
   assert rejected,label;record['negative_cases'].append(dict(case=label,rejected=True));save()
 record.update(status='complete',passed=True);save();print('source archive positive and six corruptions passed',flush=True)
except Exception as e:record.update(status='failed',error=repr(e));save();raise
