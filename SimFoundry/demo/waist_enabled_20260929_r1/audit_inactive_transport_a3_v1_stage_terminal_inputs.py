"""Independent URDF/hull/force reconstruction of terminal-hold measurements."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text();exec(compile(source.split("p=root/'contact_x_ablation")[0],'<cached_fk>','exec'))
p=Path(sys.argv[1]).resolve();mesh={k:np.asarray(v) for k,v in json.loads((root.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'].items()}
with np.load(p/'raw.npz') as z:qs=z['q']
with np.load(p/'trace.npz') as z:tr={k:z[k] for k in z.files}
with np.load(p/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
rows=json.loads((p/'terminal_joint_hold.json').read_text())['rows'];coord={x['step']:x for x in json.loads((p/'coordination.json').read_text())};ctrl={x['step']:x for x in json.loads((p/'expert_control.json').read_text())};force={x['after_action_step']:x for x in json.loads((p/'solved_contact_forces.json').read_text())['rows']}
side='right' if 'push_box' in p.name else 'left';inactive='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';actor='parcel_box' if side=='right' else 'mailer'
def transform(side,q):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,origin,axis in chains[side]:
  m=m@origin
  if axis is not None:
   a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0.)).as_matrix();m=m@a
 return m
verified_centers={}
if (p/'contact_center_calibration.json').exists():
 from audit_contact_center_live import audit
 calibration=audit(p)
 assert calibration['passed']
 verified_centers={x['step']:np.asarray(x['center_local']) for x in calibration['centers']}
from audit_inactive_transport_a3_v1_stage_region_reference import audit as audit_region_reference
region_reference=audit_region_reference(p);assert region_reference['passed']
assert not verified_centers or not region_reference['centers']
verified_centers.update({int(t):np.asarray(c) for t,c in region_reference['centers'].items()})
records=[];errors=[]
for row in rows:
 t=row['step'];q=dict(zip(names,qs[t,12:23]));ms={s:transform(s,q) for s in ('left','right')};hulls={s:mesh[s]@ms[s][:3,:3].T+ms[s][:3,3] for s in ms}
 top=max(tr[k][t,2]+float(abs(Rotation.from_quat(ori[k][t]).as_matrix()[2])@np.array(size)/2) for k,size in [('box',[.14,.09,.045]),('mailer',[.15,.145,.04])]);clearance=min(x[:,2].min() for x in hulls.values())-top
 load=sum(abs(float(x['force_world_N'][2])) for x in force[t-1]['parcel_contacts'] if any(side+'_wrist_roll' in s for s in x['shapes']) and any('/'+actor+'/' in s for s in x['shapes']))
 c=coord[t];m=ms[side]
 if c.get('active_support_reference'):
  n=Rotation.from_quat(ori[key][t]).as_matrix()[:,2];center_local=verified_centers.get(t,(mesh[side].min(0)+mesh[side].max(0))/2);center=m[:3,:3]@center_local+m[:3,3];point=center+n*((hulls[side]@n).min()-center@n)
 else:point=m[:3,:3]@np.asarray(c['active_point_offset_local'] if c.get('active_point_offset_local') is not None else [.20,0,.007])+m[:3,3]
 inactive_palm=ms[inactive][:3,:3]@np.array([.20,0,.007])+ms[inactive][:3,3]
 active_error=float(np.max(abs(point-ctrl[t]['target_xyz'])));inactive_error=float(np.max(abs(inactive_palm-c['inactive_anchor'])))
 rec=dict(step=t,held=row['held'],clearance_m=float(clearance),vertical_load_n=load,active_error_m=active_error,inactive_error_m=inactive_error,clearance_log_error_m=abs(float(clearance)-row['hand_clearance_m']),load_log_error_n=abs(load-row['load_n']),active_error_log_error_m=abs(active_error-row['active_error_m']),inactive_error_log_error_m=abs(inactive_error-row['inactive_error_m']))
 if not all(np.isfinite(v) for v in rec.values()):errors.append([t,'nonfinite_measurement'])
 if max(rec[k] for k in ('clearance_log_error_m','active_error_log_error_m','inactive_error_log_error_m'))>2e-6 or rec['load_log_error_n']>1e-8:errors.append([t,'independent_measurement_mismatch'])
 if row['held'] and not (clearance>=.02-2e-6 and load<.2 and active_error<=.012+2e-6 and inactive_error<=.015+2e-6):errors.append([t,'held_with_unready_measurements'])
 records.append(rec)
summary=dict(passed=not errors,checked_frames=len(records),held_frames=sum(x['held'] for x in records),max_clearance_log_error_m=max(x['clearance_log_error_m'] for x in records),max_load_log_error_n=max(x['load_log_error_n'] for x in records),max_active_error_log_error_m=max(x['active_error_log_error_m'] for x in records),max_inactive_error_log_error_m=max(x['inactive_error_log_error_m'] for x in records))
out=dict(auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),calibrated_reference_frames=len(verified_centers),summary=summary,errors=errors,records=records,source_sha256={f:hashlib.sha256((p/f).read_bytes()).hexdigest() for f in ('raw.npz','trace.npz','parcel_orientation.npz','solved_contact_forces.json','terminal_joint_hold.json','coordination.json','expert_control.json')},scope='Independent measured-q URDF FK, whole hand hulls and both object oriented top heights; physical projected support and inactive-palm tracking errors; previous-action target-hand vertical force sum. Two-micrometre numerical comparison tolerance only. Does not establish all-substep contacts, unobserved forces or task/model success.',training_ready=False)
out['region_reference_auditor_sha256']=hashlib.sha256((root/'audit_inactive_transport_a3_v1_stage_region_reference.py').read_bytes()).hexdigest()
(p/'INACTIVE_TRANSPORT_A3_V1_STAGE_TERMINAL_INPUT_V2_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps(summary,indent=2));print('errors',errors[:10]);sys.exit(0 if summary['passed'] else 1)
