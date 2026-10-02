"""Independent file verifier on saved synthetic repetition of real contact packets."""
from pathlib import Path
import json,copy,hashlib,datetime
import numpy as np
from audit_substep_contacts import verify_arrays
W=Path(__file__).resolve().parent;prior=json.loads((W/'SUBSTEP_RECORDING_CHECK.json').read_text());folder=Path(prior['synthetic_output_directory']);meta=json.loads((folder/'SUBSTEP_CONTACT_RECORDING.json').read_text())
with np.load(folder/'substep_contacts.npz') as z:arrays={k:z[k] for k in z.files}
ep=W/'tilt05_groups_r1/case_840001/layout_840001_push_box_to_bin';packet=next(x for x in json.loads((ep/'solved_contact_forces.json').read_text())['rows'] if x['after_action_step']==300);packets=[]
for t in range(2):p=copy.deepcopy(packet);p['after_action_step']=t;packets.append(p)
m=meta['metadata'];labels=m['shape_labels'];m.update(shape_body=[0 if '/parcel_box/' in s else 1 if '/mailer/' in s else -1 for s in labels],body_mass_kg=[.2,.1],body_com_local=[[0,0,0],[0,0,0]],body_inertia_local=np.tile(np.eye(3)*.001,(2,1,1)).tolist(),control_decimation=8,substeps_per_physics_tick=3,solver_dt_s=1/360)
# The added mass/COM values are explicitly fixture metadata, not actual model evidence.
checks=[dict(kind='saved_recorded_packet_fixture',result=verify_arrays(arrays,meta,packets,2))]
def reject(name,z,md,ps):
 try:verify_arrays(z,md,ps,2)
 except (ValueError,AssertionError,IndexError):checks.append(dict(rejected=name))
 else:raise AssertionError('accepted '+name)
for name,change in [('missing_action',lambda z:z['action_step'].__setitem__(-1,0)),('missing_substep',lambda z:z['substep_tick'].__setitem__(5,4)),('post_boundary_moved',lambda z:z['kind'].__setitem__(4,1)),('bad_offsets',lambda z:z['contact_offsets'].__setitem__(1,-1)),('duplicate_contact_id',lambda z:z['contact_id'].__setitem__(1,z['contact_id'][0])),('force_mismatch',lambda z:z['force_torque_world'].__setitem__((-1,0),99)),('nonfinite_force',lambda z:z['force_torque_world'].__setitem__((0,0),np.nan)),('pose_mismatch',lambda z:z['body_q'].__setitem__((-1,0,0),99)),('shape_out_of_range',lambda z:z['shape_ids'].__setitem__((0,0),len(labels))),('contact_count',lambda z:z['solved_contact_count'].__setitem__(-1,0)),('invalid_quaternion',lambda z:z['body_q'].__setitem__((0,0,6),8))]:
 z=copy.deepcopy(arrays);change(z);reject(name,z,meta,packets)
for name,change in [('wrong_body_ownership',lambda d:d['metadata']['shape_body'].__setitem__(next(i for i,s in enumerate(labels) if '/parcel_box/' in s),1)),('nonpositive_mass',lambda d:d['metadata']['body_mass_kg'].__setitem__(0,0)),('nonpositive_inertia',lambda d:d['metadata']['body_inertia_local'][0][0].__setitem__(0,-1)),('changed_force_tolerance',lambda d:d.__setitem__('force_comparison_atol',.1)),('multiple_worlds',lambda d:d.__setitem__('world_count',2))]:
 md=copy.deepcopy(meta);change(md);reject(name,arrays,md,packets)
ps=copy.deepcopy(packets);ps[-1]['parcel_contacts'].pop();reject('original_packet_contact_missing',arrays,meta,ps)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,checks=checks,fixture_mass_com_inertia_are_synthetic=True,actual_runtime_installed=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_substep_contacts.py',W/'SUBSTEP_RECORDING_CHECK.json',folder/'substep_contacts.npz',folder/'SUBSTEP_CONTACT_RECORDING.json',ep/'solved_contact_forces.json']})
p=W/'SUBSTEP_FILE_AUDIT_CHECK.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print('PASS',len(checks),'independent packed-file checks; fixture only')
