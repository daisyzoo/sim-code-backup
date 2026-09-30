"""Independent recorded dynamic supporting-point coordinate check."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
run=Path(sys.argv[1]);mesh=json.loads((root.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'];rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';vertices=np.array(mesh[side]);raw=np.load(ep/'raw.npz');ori=np.load(ep/'parcel_orientation.npz');log=json.loads((ep/'frontal_bypass.json').read_text())['rows'];errors=[];excess=[];offsets=[]
 if not log:
  plan=json.loads((ep/'frontal_bypass.json').read_text())['plan']
  if plan.get('required') is not False:raise ValueError('Missing required frontal support trace')
  with np.load(ep/'trace.npz') as tr:palm_trace=tr['palm_'+side]
  for t in range(len(raw['q'])):
   q=dict(zip(names,raw['q'][t,12:23]));m=np.eye(4);m[:3,3]=[.08,0,.793]
   for name,orig,axis in chains[side]:
    m=m@orig
    if axis is not None:r=np.eye(4);r[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@r
   errors.append(float(np.max(abs((m@np.array([.20,0.,.007,1.]))[:3]-palm_trace[t]))))
  rows.append(dict(episode=ep.name,reference='fixed palm: frontal bypass not required',frames=len(errors),max_fk_error_m=max(errors),support_vertex_check_applicable=False,max_support_plane_excess_m=None,max_control_vertex_change_m=None,vertex_changes=None,zero_first_state=bool(np.max(abs(raw['q'][0,12:23]))<1e-4),zero_first_action=bool(np.max(abs(raw['action'][0,12:23]))<1e-4)))
  continue
 for row in log:
  t=row['step'];q=dict(zip(names,raw['q'][t,12:23]));m=np.eye(4);m[:3,3]=[.08,0,.793]
  for name,orig,axis in chains[side]:
   m=m@orig
   if axis is not None:r=np.eye(4);r[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@r
  normal=Rotation.from_quat(ori[key][t]).as_matrix()[:,2];world=vertices@m[:3,:3].T+m[:3,3];idx=int(np.argmin(world@normal));off=row.get('control_offset_local',None);off=row.get('observed_support_offset_local') if off is None else off
  if off is None:
   # Historical rear phase did not record the observer offset. Validate that
   # observed point is an actual mesh vertex; exact-min assumption is invalid
   # when a diagnostic near-support selector is used. Active offsets remain
   # independently checked from their explicitly recorded coordinates.
   idx=int(np.argmin(np.linalg.norm(world-np.array(row['observed_support_xyz']),axis=1)));off=vertices[idx]
  else:off=np.array(off)
  expected=m[:3,:3]@off+m[:3,3]
  errors.append(float(np.max(abs(expected-row['observed_support_xyz']))));excess.append(float(expected@normal-np.min(world@normal)))
  if row.get('control_offset_local') is not None:offsets.append(off)
 jumps=np.linalg.norm(np.diff(offsets,axis=0),axis=1) if len(offsets)>1 else np.zeros(1)
 rows.append(dict(episode=ep.name,projected_reference_frames=sum('projected_support_reference' in r for r in log),reference_kind='continuous virtual plane plus separately recorded physical support' if any('projected_support_reference' in r for r in log) else 'recorded actual vertex',max_control_reference_change_m=float(max(jumps)),legacy_vertex_change_field_is_reference_alias=any('projected_support_reference' in r for r in log),frames=len(errors),max_fk_error_m=max(errors),max_support_plane_excess_m=max(excess),max_control_vertex_change_m=float(max(jumps)),vertex_changes=int((jumps>1e-6).sum()),zero_first_state=bool(np.max(abs(raw['q'][0,12:23]))<1e-4),zero_first_action=bool(np.max(abs(raw['action'][0,12:23]))<1e-4)))
report=dict(rows=rows,scope='Independent URDF FK of fixed palm when bypass is not required, otherwise explicitly recorded active/observer offsets and hull-plane height against actual parcel top normal. Historical rear rows with no recorded offset check nearest actual mesh vertex to observation, not independent selector identity; exact-min is not assumed for hysteresis. Pre-action samples. For projected reference rows the point is virtual, not a mesh vertex; legacy vertex-change fields are reference-change aliases, with explicit kind/count. Real support and hybrid Jacobian need PROJECTED_SUPPORT_LIVE_AUDIT. Reported jumps are not physical hand teleportation. Does not certify forces or full-arm clearance.',training_ready=False)
(run/'SUPPORT_MAPPING_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
