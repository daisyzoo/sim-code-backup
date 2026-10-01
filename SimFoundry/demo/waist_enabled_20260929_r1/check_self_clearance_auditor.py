"""Real preflight positive and tampered copies; original artifacts remain unchanged."""
from pathlib import Path
import sys,json,tempfile,copy,hashlib
import numpy as np
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w))
from audit_self_clearance_live import audit
source=w/'self_clearance_runtime_preflight_r1/case';original=source/'layout_841000_wait_no_package';results=[]
def write(p,d):
 if p.is_symlink():p.unlink()
 p.write_text(json.dumps(d))
def record(ep,fn):
 p=ep/'self_clearance.json';d=json.loads(p.read_text());fn(d);write(p,d)
def raw(ep,fn):
 p=ep/'raw.npz'
 with np.load(p) as z:d={k:z[k].copy() for k in z.files}
 fn(d);p.unlink();np.savez(p,**d)
with tempfile.TemporaryDirectory(prefix='clearance_auditor_') as temp:
 for name,edit in [
 ('positive',None),
 ('changed_final_action',lambda ep:raw(ep,lambda d:d['action'].__setitem__((10,13),.002))),
 ('faked_gap',lambda ep:record(ep,lambda d:d['rows'][1]['gaps_m'].__setitem__(0,.1))),
 ('shifted_actual_body',lambda ep:record(ep,lambda d:d['rows'][0]['runtime_link_poses']['left_elbow_link'][0].__setitem__(3,1.))),
 ('missing_post',lambda ep:record(ep,lambda d:d['rows'].pop(2))),
 ('changed_previous',lambda ep:record(ep,lambda d:d['rows'][4]['previous'].__setitem__(0,.01))),
 ('changed_intrinsics',lambda ep:raw(ep,lambda d:d['intrinsics'].__setitem__(2,326.))),
 ('missing_failure_claim',lambda ep:record(ep,lambda d:d.__setitem__('failure',dict(reason='injected')))),
 ('incorrect_length',lambda ep:record(ep,lambda d:d.__setitem__('recorded_frames',69)))]:
  case=Path(temp)/name;case.mkdir();ep=case/original.name;ep.mkdir()
  for p in source.iterdir():
   if p.name!=original.name:(case/p.name).symlink_to(p,target_is_directory=p.is_dir())
  for p in original.iterdir():(ep/p.name).symlink_to(p,target_is_directory=p.is_dir())
  if edit:edit(ep)
  try:out=audit(ep)
  except (AssertionError,ValueError,KeyError):accepted=False
  else:accepted=out['passed']
  assert accepted==(edit is None),name
  results.append(dict(case=name,accepted=accepted));print(name,accepted)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();out=dict(all_passed=True,cases=results,source_sha256={str(p):sha(p) for p in [Path(__file__),w/'audit_self_clearance_live.py',original/'raw.npz',original/'self_clearance.json']},training_ready=False);(w/'staged_self_clearance_task_ik/AUDITOR_CHECK.json').write_text(json.dumps(out,indent=2))
