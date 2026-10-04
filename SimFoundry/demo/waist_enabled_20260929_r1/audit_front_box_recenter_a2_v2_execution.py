"""Complete-episode source, Cartesian route/COP and loaded-Z output binding.
Original full self-clearance task reconstruction and all other audits are still
required. In particular this report is not standalone task/admission evidence.
"""
from pathlib import Path
import json,hashlib,sys,datetime
import numpy as np
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from audit_front_box_recenter_a2_v2_z_execution import inspect as inspect_z
from audit_front_corridor_midpoint_cop import reconstruct
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def inspect(ep,*,allow_source_fixture=False):
 ep=Path(ep).resolve();result=inspect_z(ep,allow_source_fixture=allow_source_fixture)
 with np.load(ep/'raw.npz',allow_pickle=False) as z:task=str(z['task_id']);n=len(z['q']);meta=json.loads(str(z['collect_meta']))
 sources=dict(result['source_sha256']);route=None
 if task!='wait_no_package':
  frontal=json.loads((ep/'frontal_bypass.json').read_text())
  with np.load(ep/'trace.npz',allow_pickle=False) as z:tr={k:z[k].copy() for k in ['box','mailer']}
  with np.load(ep/'parcel_orientation.npz',allow_pickle=False) as z:ori={k:z[k].copy() for k in ['box','mailer']}
  assert all(tr[k].shape==(n,3) and ori[k].shape==(n,4) and np.isfinite(tr[k]).all() and np.isfinite(ori[k]).all() for k in tr)
  packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows']
  assert [r['after_action_step'] for r in packets]==list(range(n))
  route=reconstruct(frontal['rows'],frontal['plan'],tr,ori,{r['after_action_step']:r for r in packets},'box' if task=='push_box_to_bin' else 'mailer',midpoint_enabled=True,expected_steps=range(1,n))
  assert route['passed'],route['errors']
  assert len(route['observation_binding']['changed_steps'])==meta['front_corridor_midpoint_replanned_frames']
  for name in ['frontal_bypass.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json']:sources[str(ep/name)]=sha(ep/name)
 for name in ['audit_front_box_recenter_a2_v2_execution.py','audit_front_box_recenter_a2_v2_z_execution.py','front_box_recenter_a2_loaded_episode_inputs.py','audit_front_corridor_midpoint_cop.py','audit_front_corridor_midpoint_observations.py','audit_front_corridor_midpoint_record.py','front_box_recenter_stage_source_binding.py','FRONT_CORRIDOR_MIDPOINT_Z_EXECUTION_PREPARATION.json','FRONT_CORRIDOR_MIDPOINT_SOURCE_CONTRACT_PREPARATION.json']:sources[str(W/name)]=sha(W/name)
 return dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=ep.name,frames=n,fixture_only=result['fixture_only'],physical_execution_evidence=result['physical_execution_evidence'],loaded_z_applied=result['applied'],loaded_z_records=result['records'],additional_direct_matrix_paths=result['additional_direct_matrix_paths'],route=route,source_sha256=sources,original_full_control_audits_required=True,full_audit_closure=False,training_ready=False)

if __name__=='__main__':
 ep=Path(sys.argv[1]);out=inspect(ep)
 with (ep/'FRONT_BOX_RECENTER_A2_V2_EXECUTION_AUDIT.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps({k:out[k] for k in ['passed','episode','frames','fixture_only','physical_execution_evidence','loaded_z_applied','training_ready']},indent=2))
