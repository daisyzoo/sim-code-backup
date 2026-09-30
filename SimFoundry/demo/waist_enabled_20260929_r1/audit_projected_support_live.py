"""Independent URDF/finite-difference verification of recorded virtual references."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent
src=(root/'audit_terminal_reach.py').read_text();exec(compile(src.split("p=root/'contact_x_ablation")[0],'<cached_fk>','exec'))
p=Path(sys.argv[1]).resolve();z=np.load(p/'raw.npz');ori=np.load(p/'parcel_orientation.npz');tr=np.load(p/'trace.npz');rows=json.loads((p/'frontal_bypass.json').read_text())['rows'];coord={r['step']:r for r in json.loads((p/'coordination.json').read_text())};side='right' if 'push_box' in p.name else 'left';key='box' if side=='right' else 'mailer'
vertices=np.asarray(json.loads((root.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'][side]);center=(vertices.min(axis=0)+vertices.max(axis=0))/2;size=np.array([.14,.09,.045] if side=='right' else [.15,.145,.04]);core=size*np.array([.96,.96,1] if side=='right' else [.90,.88,1])

verified_centers={}
if (p/'contact_center_calibration.json').exists():
 from audit_contact_center_live import audit
 calibration_audit=audit(p)
 verified_centers={r['step']:np.asarray(r['center_local']) for r in calibration_audit['centers']}

def transform(which,q):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,origin,axis in chains[which]:
  m=m@origin
  if axis is not None:
   a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*(q[names.index(name)] if name in names else 0.)).as_matrix();m=m@a
 return m

def points(q,n):
 answer=[]
 for which in ('left','right'):
  m=transform(which,q)
  if which==side:
   w=vertices@m[:3,:3].T+m[:3,3];c=m[:3,:3]@center+m[:3,3]
   answer.extend(c+n*((w@n).min()-c@n))
  else:answer.extend(m[:3,:3]@np.array([.20,0,.007])+m[:3,3])
 return np.array(answer)
records=[];jacobians=[]
for row in rows:
 if 'projected_support_reference' not in row:continue
 t=row['step'];center=verified_centers.get(t,(vertices.min(axis=0)+vertices.max(axis=0))/2);q=z['q'][t,12:23].astype(float);m=transform(side,q);rp=Rotation.from_quat(ori[key][t]).as_matrix();n=rp[:,2];w=vertices@m[:3,:3].T+m[:3,3];h=w@n;c=m[:3,:3]@center+m[:3,3];expected=c+n*(h.min()-c@n);observed=np.array(row['observed_support_xyz']);physical=np.array(row['observed_physical_support_xyz']);offset=np.array(row['control_offset_local']);v=np.array(row['physical_support_offset_local'])
 near=w[h-h.min()<=.0002];local=(near-tr[key][t])@rp
 rec=dict(step=t,mode=row['mode'],reference_world_error_m=float(np.linalg.norm(expected-observed)),reference_offset_fk_error_m=float(np.linalg.norm(m[:3,:3]@offset+m[:3,3]-expected)),physical_vertex_membership_error_m=float(np.linalg.norm(vertices-v,axis=1).min()),physical_vertex_world_error_m=float(np.linalg.norm(m[:3,:3]@v+m[:3,3]-physical)),physical_support_plane_excess_m=float(physical@n-h.min()),near_support_core_xy_margin_m=float(np.min(core[:2]/2-np.abs(local[:,:2]))),observed_load_n=row.get('contact_load',{}).get('observed_vertical_load_n'))
 records.append(rec)
 if t in coord and 'control_jacobian_world' in coord[t]:
  eps=1e-7;fd=np.empty((6,11))
  for i in range(11):
   delta=np.zeros(11);delta[i]=eps;fd[:,i]=(points(q+delta,n)-points(q-delta,n))/(2*eps)
  actual=np.array(coord[t]['control_jacobian_world']);gap=float(np.sort(h)[1]-h.min())
  jacobians.append(dict(step=t,max_abs_error_m_per_rad=float(np.max(abs(fd-actual))),support_first_second_height_gap_m=gap,near_nonsmooth_switch=gap<1e-8))
assert records,'No projected support records'
finite_regular=[v['max_abs_error_m_per_rad'] for v in jacobians if not v['near_nonsmooth_switch']]
summary=dict(frames=len(records),max_reference_world_error_m=max(r['reference_world_error_m'] for r in records),max_reference_offset_fk_error_m=max(r['reference_offset_fk_error_m'] for r in records),max_physical_vertex_membership_error_m=max(r['physical_vertex_membership_error_m'] for r in records),max_physical_vertex_world_error_m=max(r['physical_vertex_world_error_m'] for r in records),max_abs_physical_support_plane_excess_m=max(abs(r['physical_support_plane_excess_m']) for r in records),min_observed_near_support_core_margin_m=min(r['near_support_core_xy_margin_m'] for r in records),jacobian_samples=len(jacobians),nonsmooth_samples=sum(r['near_nonsmooth_switch'] for r in jacobians),max_regular_jacobian_error_m_per_rad=max(finite_regular) if finite_regular else None)
summary['mapping_passed']=all(summary[k]<1e-6 for k in ('max_reference_world_error_m','max_reference_offset_fk_error_m','max_physical_vertex_membership_error_m','max_physical_vertex_world_error_m','max_abs_physical_support_plane_excess_m')) and bool(finite_regular) and max(finite_regular)<1e-5
out=dict(summary=summary,records=records,jacobians=jacobians,raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),scope='Independent cached URDF FK, full hull minimum plane and finite differences at measured joint poses; simulator control helper not called. Physical mesh vertex distinguished from virtual supporting-plane reference. Excludes near-nonsmooth frames from scalar derivative pass threshold but retains each result. Face margin during unloaded transit is not contact/collision; review load/contact timing separately. Does not certify dynamics, all-arm clearance, task success, data admission or model performance.',training_ready=False)
(p/'PROJECTED_SUPPORT_LIVE_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps(summary,indent=2))
