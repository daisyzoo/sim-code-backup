"""Separately verified intermediates for original control-math consumers.
Actual raw commands/history stay unchanged; no physical task/admission claim.
"""
from pathlib import Path
import json,hashlib
import numpy as np
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load_transport_ledger(ep,*,allow_source_fixture=False):
 ep=Path(ep).resolve();fixture=any((ep.parent/n).exists() for n in ['SOURCE_CONTRACT_FIXTURE.json','DIAGNOSTIC_ONLY.json'])
 assert type(allow_source_fixture) is bool and (not fixture or allow_source_fixture)
 proof=json.loads((ep/'FRONT_NORMAL_NATIVE_STREAM_V1_AUDIT.json').read_text())
 assert proof['passed'] is True and proof['fixture_only'] is fixture and proof['command_chain_verified'] is True
 assert proof['actual_final_history_preserved'] is True and proof['original_parent_control_math_audits_required'] is True and proof['training_ready'] is False
 for p,h in proof['source_sha256'].items():assert sha(p)==h,p
 files=['raw.npz','joint_transport_clearance.json','front_loaded_z_priority.json']
 for p in [*(ep/n for n in files),W/'audit_front_normal_native_stream_v1.py',W/'audit_front_normal_command_stream_v1.py',W/'audit_front_normal_command_record_v1.py',W/'audit_effective_height_transport_records_v1.py']:
  assert proof['source_sha256'][str(p)]==sha(p)
 enabled=json.loads((ep.parent/'provenance.json').read_text())['args']['front_normal_nondegradation']
 normal=None
 if enabled:
  p=ep/'front_normal_nondegradation.json';assert proof['source_sha256'][str(p)]==sha(p);normal=json.loads(p.read_text())['rows']
 with np.load(ep/'raw.npz',allow_pickle=False) as z:q=z['q'][:,12:23].copy();actual=z['action'][:,12:23].copy()
 rows=json.loads((ep/'joint_transport_clearance.json').read_text())['rows'];loaded=json.loads((ep/'front_loaded_z_priority.json').read_text())['rows'];n=len(q)
 assert proof['frames']==len(actual)==len(rows)==len(loaded)==n
 for rs in [rows,loaded,proof['rows']]+([] if normal is None else [normal]):assert [r['step'] for r in rs]==list(range(n))
 parents=[]
 for t,(r,l,p) in enumerate(zip(rows,loaded,proof['rows'])):
  assert r['applied'] is p['transport_applied'] and p['final_guard_passed'] is True
  assert np.array_equal(r['parent_command'],l['output_command'])
  if enabled:
   nr=normal[t];assert nr['applied'] is p['normal_applied'];assert np.array_equal(nr['parent_command'],r['output_command']) and np.array_equal(nr['output_command'],actual[t])
  else:assert p['normal_applied'] is False and np.array_equal(r['output_command'],actual[t])
  parent=np.asarray(r['parent_command']);assert parent.shape==(11,) and np.isfinite(parent).all() and np.array_equal(parent,parent.astype(np.float32))
  c=r['collector_context'];assert np.array_equal(c['current'],q[t]) and np.array_equal(c['previous_command'],np.zeros(11) if t==0 else actual[t-1])
  if t:assert np.array_equal(c['previous_q'],q[t-1])
  else:assert c['previous_q'] is None
  parents.append(parent)
 parent_array=np.asarray(parents,dtype=np.float32);parent_array.setflags(write=False)
 return parent_array,dict(passed=True,frames=n,applied=sum(r['applied'] for r in rows),stream_report_sha256=sha(ep/'FRONT_NORMAL_NATIVE_STREAM_V1_AUDIT.json'),actual_history_preserved=True,fixture_only=fixture,training_ready=False)
