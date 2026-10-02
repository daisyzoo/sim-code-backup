"""Source-bound CLI for the independently checked tracking native verifier."""
from pathlib import Path
import json,hashlib,sys
from audit_rear_recovery_tracking_native import verify_files

def main():
 w=Path(__file__).resolve().parent;ep=Path(sys.argv[1]).resolve();root=w.parents[1];stage=w/'staged_rear_transport_retry'
 from rear_transport_retry_source_binding import verify_observation_binding
 binding=verify_observation_binding(ep);out=verify_files(ep,root,stage)
 files=['raw.npz','rear_corridor_recovery.json']
 if not out['wait']:files+=['frontal_bypass.json','coordination.json','expert_control.json','recontact_pose.json','peak_load_updates.json','trace.npz','parcel_orientation.npz']
 sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 out.update(scope=__doc__,source_binding=binding,file_sha256={n:sha(ep/n) for n in files},auditor_sha256=sha(__file__))
 out['independent_source_sha256']={n:sha(w/n) for n in ['audit_rear_recovery_tracking_native.py','audit_rear_recovery_tracking_records.py','audit_rear_recovery_tracking_observation.py','rear_recovery_tracking_stationarity.py','support_vertex_stationarity.py','audit_rear_corridor_latched_phase.py','rear_corridor_latched_stationarity.py']}
 with (ep/'REAR_TRANSPORT_RETRY_NATIVE_AUDIT.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps({k:v for k,v in out.items() if k not in ['records','phase_records','source_binding','file_sha256','scope']}))
if __name__=='__main__':main()
