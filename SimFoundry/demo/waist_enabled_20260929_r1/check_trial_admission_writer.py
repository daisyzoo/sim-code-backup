"""Synthetic writer-only tests: source checker is stubbed, never data admission.
Uses disposable /tmp roots. Real full-group positive source audit remains pending.
"""
from pathlib import Path
import tempfile,json,hashlib,datetime
from unittest.mock import patch
import approve_closed_peak_trial_group as module
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
results=[]
def fixture(root):
 roots=[root/f'case_{i}' for i in range(3)]
 for p in roots:p.mkdir();(p/'waist_pilot_contract.json').write_text('synthetic writer fixture only')
 reviews=[dict(approved=True,scope='synthetic writer fixture, not real source review') for _ in roots]
 records=[dict(path=roots[i%3]/f'episode_{i}/raw.npz',waist_pilot_contract_sha256=sha(roots[0]/'waist_pilot_contract.json')) for i in range(5)]
 return roots,reviews,records,dict(ready=True,group_review_sha256='synthetic')
for case in ['path_serialization','source_rejection','summary_serialization_rejection','partial_review_write','existing_summary']:
 with tempfile.TemporaryDirectory(prefix='trial_admission_writer_') as tmp:
  root=Path(tmp);roots,reviews,records,report=fixture(root);dest=root/'GROUP_ADMISSIONS'/'synthetic.json'
  if case=='summary_serialization_rejection':records[-1]['invalid']=object()
  if case=='existing_summary':dest.parent.mkdir();dest.write_text('preserve existing record')
  original_open=Path.open
  class Partial:
   def __init__(self,f):self.f=f
   def __enter__(self):return self
   def __exit__(self,*args):self.f.close()
   def write(self,text):self.f.write(text[:12]);self.f.flush();raise OSError('injected partial write')
  def opening(path,*args,**kwargs):
   f=original_open(path,*args,**kwargs)
   if case=='partial_review_write' and path==roots[1]/'review.json' and args and args[0]=='x':return Partial(f)
   return f
  with patch.object(module,'checked_sources',side_effect=ValueError('injected source rejection') if case=='source_rejection' else None,return_value=records),patch.object(Path,'open',opening):
   try:out=module.apply_prepared(root,'synthetic',report,(roots,reviews))
   except (ValueError,TypeError,OSError,AssertionError):
    assert case!='path_serialization'
    assert all(not (p/'review.json').exists() for p in roots)
    if case=='existing_summary':assert dest.read_text()=='preserve existing record'
    else:assert not dest.exists()
   else:
    assert case=='path_serialization' and out['full_group_source_admitted'];d=json.loads(dest.read_text());assert len(d['records'])==5 and all(isinstance(x['path'],str) for x in d['records'])
  results.append(dict(case=case,passed=True))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,checks=results,scope=__doc__,quality_checker_stubbed=True,real_positive_source_admission_tested=False,temporary_fixtures_deleted=True,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'approve_closed_peak_trial_group.py']},training_ready=False)
with (W/'TRIAL_ADMISSION_WRITER_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
