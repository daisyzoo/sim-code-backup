"""Positive complete wait audit fixture and negative new-source contract checks.
This fixture reuses old measurements with explicitly projected source metadata;
passing does not certify a new rollout, front cap physics, or training admission.
"""
from pathlib import Path
import copy,datetime,hashlib,io,json,sys
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from front_loaded_stage_source_binding import verify_observation_binding
base=W/'front_loaded_wait_source_fixture_r1';case=base/'case_841010';ep=case/'layout_841010_wait_no_package';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();out=W/'FRONT_LOADED_WAIT_SOURCE_FIXTURE_CHECK.json';assert not out.exists()
reports={n:json.loads((ep/n).read_text()) for n in ['FRONT_LOADED_STAGE_SELF_CLEARANCE_V2_AUDIT.json','WAIT_STABILITY_AUDIT.json','FRONT_LOADED_STAGE_CONTACT_AUDIT.json','FRONT_LOADED_STAGE_PRESSURE_V2_AUDIT.json','FRONT_LOADED_STAGE_RELEASE_AUDIT.json']}
assert all(r.get('passed',r.get('episode_clearance_passed')) is True for r in reports.values())
assert reports['FRONT_LOADED_STAGE_SELF_CLEARANCE_V2_AUDIT.json']['episode_clearance_passed'] is True
assert json.loads((base/'FIXTURE_ONLY.json').read_text())['audit_fixture_only'] is True
verify_observation_binding(ep)
prov=case/'provenance.json';raw=ep/'raw.npz';runtime=case/'SUBSTEP_RUNTIME_BINDING.json';p=json.loads(prov.read_text());helper=case/'source_snapshot'/next(n for n in p['source_sha256'] if n.endswith('/front_initial_loaded_reference_cap.py'))
originals={path:path.read_bytes() for path in [prov,raw,runtime,helper]};negatives=[]
for label in ['disabled_argument','integer_enable_argument','missing_raw_enable','shortened_raw','changed_archived_helper','old_observer_stage_path']:
 try:
  if label in ('disabled_argument','integer_enable_argument'):
   d=json.loads(originals[prov]);d['args']['front_loaded_reference_cap']=False if label=='disabled_argument' else 1;prov.write_text(json.dumps(d))
  elif label in ('missing_raw_enable','shortened_raw'):
   with np.load(io.BytesIO(originals[raw])) as z:arrays={k:z[k].copy() for k in z.files}
   if label=='missing_raw_enable':m=json.loads(str(arrays['collect_meta']));m.pop('front_loaded_reference_cap');arrays['collect_meta']=np.array(json.dumps(m))
   else:arrays['q']=arrays['q'][:-1]
   np.savez_compressed(raw,**arrays)
  elif label=='changed_archived_helper':helper.write_bytes(originals[helper]+b'\n# corrupted archive fixture\n')
  else:
   d=json.loads(originals[runtime]);key=next(n for n in d['source_files'] if n.endswith('/substep_contact_setup.py'));d['source_files'][key.replace('staged_front_loaded_reference','staged_front_initial_center')]=d['source_files'].pop(key);runtime.write_text(json.dumps(d))
  rejected=False
  try:verify_observation_binding(ep)
  except (AssertionError,KeyError,ValueError):rejected=True
  assert rejected,label;negatives.append(dict(case=label,rejected=True))
 finally:
  for path,data in originals.items():
   if path.read_bytes()!=data:path.write_bytes(data)
assert all(path.read_bytes()==data for path,data in originals.items());verify_observation_binding(ep)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,fixture_only=True,positive_wait_audits=list(reports),negative=negatives,original_fixture_inputs_restored=True,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'front_loaded_stage_source_binding.py',base/'FIXTURE_ONLY.json',base/'FIXTURE_GEOMETRY_AUGMENT.json',*[ep/n for n in reports],*originals]},first_missing_geometry_failure_log_sha256=sha(ep/'audit_front_loaded_stage_self_clearance.py.fixture.log'),simulation_started=False,training_ready=False)
out.write_text(json.dumps(report,indent=2));print('Passed5 complete wait audit fixtures and6 source-contract negatives; all fixture inputs restored')
