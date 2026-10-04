"""Read separately audited parent intermediates; never replace actual action history.
Native independent transport stream audit must complete before parent auditors.
"""
from pathlib import Path
import json,hashlib
import numpy as np
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load_transport_ledger(ep,*,allow_source_fixture=False):
 ep=Path(ep).resolve();fixture=(ep.parent/'SOURCE_CONTRACT_FIXTURE.json').exists()
 assert type(allow_source_fixture) is bool and (not fixture or allow_source_fixture)
 proof=json.loads((ep/'REAR_TRAILING_TRANSPORT_STREAM_V1_AUDIT.json').read_text())
 assert proof['passed'] is True and proof['fixture_only'] is fixture and proof['physical_candidate_verified'] is (not fixture)
 assert proof['original_parent_control_math_audits_required'] is True and proof['training_ready'] is False
 for p,h in proof['source_sha256'].items():assert sha(p)==h,p
 for p in [ep/'raw.npz',ep/'joint_transport_clearance.json',ep/'front_loaded_z_priority.json',W/'audit_rear_trailing_transport_stream_v1.py',W/'audit_joint_transport_records_v1.py']:
  assert proof['source_sha256'][str(p)]==sha(p)
 with np.load(ep/'raw.npz',allow_pickle=False) as z:q=z['q'][:,12:23].copy();actual=z['action'][:,12:23].copy()
 rows=json.loads((ep/'joint_transport_clearance.json').read_text())['rows'];loaded=json.loads((ep/'front_loaded_z_priority.json').read_text())['rows'];n=len(q)
 assert proof['frames']==len(actual)==len(rows)==len(loaded)==n
 for records in [rows,loaded,proof['rows']]:assert [r['step'] for r in records]==list(range(n))
 parents=[]
 for t,(r,l,p) in enumerate(zip(rows,loaded,proof['rows'])):
  assert r['applied'] is p['applied'] and r['reason']==p['reason'] and p['final_guard_passed'] is True
  assert np.array_equal(r['output_command'],actual[t]) and np.array_equal(r['parent_command'],l['output_command'])
  parent=np.asarray(r['parent_command']);assert parent.shape==(11,) and np.isfinite(parent).all() and np.array_equal(parent,parent.astype(np.float32))
  c=r['collector_context'];assert np.array_equal(c['current'],q[t]) and np.array_equal(c['previous_command'],np.zeros(11) if t==0 else actual[t-1])
  if t:assert np.array_equal(c['previous_q'],q[t-1])
  else:assert c['previous_q'] is None
  if r['applied']:
   assert c['side'] in ('left','right') and p['geometry_certified'] is True
   certificate=r['certificate'];assert certificate['passed'] is True and all(v is True for v in certificate['checks'].values())
   assert certificate['certificate']['passed'] is True and certificate['certificate']['stationarity_residual']<=1e-6
   assert r['proposal']['parent_height_task_preserved'] is True and r['proposal']['original_contact_primal_preserved'] is True
   assert set(r['paths'])=={'nominal','predicted'} and all(v['passed'] is True for v in r['paths'].values())
  else:assert np.array_equal(parent,actual[t])
  parents.append(parent)
 parent_array=np.asarray(parents,dtype=np.float32);parent_array.setflags(write=False)
 return parent_array,dict(passed=True,frames=n,applied=sum(r['applied'] for r in rows),stream_report_sha256=sha(ep/'REAR_TRAILING_TRANSPORT_STREAM_V1_AUDIT.json'),actual_history_preserved=True,fixture_only=fixture,training_ready=False)
