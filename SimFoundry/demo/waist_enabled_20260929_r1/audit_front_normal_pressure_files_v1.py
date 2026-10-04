"""Native source/contact/pressure file binding for final-normal recovery.
Retains original24tick extraction, peak/bias math, original phase-report gate.
No pressure-only result certifies whole task, new dynamics or training admission.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from audit_front_normal_pressure_stream_v1 import verify_stream,independent_loads
from audit_front_normal_contacts_v2 import audit as audit_contacts
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def audit(ep,*,allow_source_fixture=False):
 ep=Path(ep).resolve();fixture=any((ep.parent/n).exists() for n in ['SOURCE_CONTRACT_FIXTURE.json','DIAGNOSTIC_ONLY.json'])
 assert type(allow_source_fixture) is bool and (not fixture or allow_source_fixture),'Synthetic fixture is not physical evidence'
 observer=audit_contacts(ep)
 with np.load(ep/'raw.npz',allow_pickle=False) as z:
  task=str(z['task_id']);q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
 n=len(q);assert task in ('push_box_to_bin','nudge_mailer_to_bin','wait_no_package');wait=task=='wait_no_package';assert n==(70 if wait else 1200),'short attempt cannot pass pressure audit'
 enabled=json.loads((ep.parent/'provenance.json').read_text())['args']['front_normal_nondegradation'];assert type(enabled) is bool
 pressure=json.loads((ep/'peak_load_updates.json').read_text());frontal=None if wait else json.loads((ep/'frontal_bypass.json').read_text());meta=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text())['metadata']
 with np.load(ep/'substep_contacts.npz',allow_pickle=False) as z:arrays={k:z[k] for k in z.files}
 loads={} if wait else independent_loads(arrays,meta,task,n)
 normal=json.loads((ep/'front_normal_nondegradation.json').read_text())['rows'] if enabled else None
 guards=[r for r in json.loads((ep/'self_clearance.json').read_text())['rows'] if r['phase']=='final_command'] if enabled else None
 out=verify_stream(pressure,frontal,loads,frames=n,wait=wait,enabled=enabled,normal_records=normal,current=q,actions=u,side='right' if task=='push_box_to_bin' else 'left',final_guards=guards)
 native=ep/('WAIT_STABILITY_AUDIT.json' if wait else 'FRONT_NORMAL_POSE_LIVE_V1_AUDIT.json');phase=json.loads(native.read_text());assert phase['passed'] is True
 if wait:assert phase['raw_sha256']==sha(ep/'raw.npz') and phase['trace_sha256']==sha(ep/'trace.npz')
 else:
  for name,h in phase['source_sha256'].items():assert sha(ep/name)==h,name
  assert phase['source_sha256']['raw.npz']==sha(ep/'raw.npz') and phase['provenance_sha256']==sha(ep.parent/'provenance.json')
  assert phase['auditor_sha256']==sha(W/'audit_front_normal_pose_live_v1.py')
  for name,h in phase['dependent_auditors_sha256'].items():assert sha(W/name)==h,name
 files=['peak_load_updates.json','raw.npz','SUBSTEP_CONTACT_RECORDING.json','substep_contacts.npz',native.name,'quality.json']
 if not wait:files.append('frontal_bypass.json')
 if enabled:files.extend(['front_normal_nondegradation.json','self_clearance.json'])
 out.update(scope=__doc__,fixture_only=fixture,independent_substep_audit=observer,original_native_phase_audit_sha256=sha(native),source_sha256={str(ep/name):sha(ep/name) for name in files},auditor_sha256=sha(__file__),math_auditor_sha256={name:sha(W/name) for name in ['audit_front_normal_pressure_stream_v1.py','audit_front_normal_pressure_finalization_v1.py','audit_peak_load_update_math.py','audit_front_normal_contacts_v2.py','audit_front_effective_height_r1_v1_stage_pressure.py']},training_ready=False)
 return out

if __name__=='__main__':
 ep=Path(sys.argv[1]);out=audit(ep);p=ep/'FRONT_NORMAL_PRESSURE_FILES_V1_AUDIT.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['records','independent_substep_audit','source_sha256','scope']})
