"""Independent FK audit of diagnostic near-support selection and its explicit bound."""
from pathlib import Path
import sys,json
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
run=Path(sys.argv[1]).resolve()
assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
mesh=json.loads((root.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'];rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';z=np.load(ep/'raw.npz');ori=np.load(ep/'parcel_orientation.npz');d=json.loads((ep/'frontal_bypass.json').read_text());vertices=np.array(mesh[side]);bound=d['plan']['top_recontact']['support_hysteresis_m'];excesses=[];errors=[];bad_membership=0;bad_logs=0
 for row in d['rows']:
  if row.get('control_offset_local') is None:continue
  t=row['step'];q=dict(zip(names,z['q'][t,12:23]));m=np.eye(4);m[:3,3]=[.08,0,.793]
  for name,orig,axis in chains[side]:
   m=m@orig
   if axis is not None:
    a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@a
  selected=np.array(row['control_offset_local']);normal=m[:3,:3].T@Rotation.from_quat(ori[key][t]).as_matrix()[:,2];height=float(selected@normal-np.min(vertices@normal));excesses.append(height);meta=row['support_selection'];errors.append(abs(height-meta['support_plane_excess_m']));bad_membership+=int(np.min(np.linalg.norm(vertices-selected,axis=1))>1e-9);bad_logs+=int(meta['max_support_plane_excess_m']!=bound)
 passed=bool(excesses and min(excesses)>=-1e-6 and max(excesses)<=bound+1e-6 and max(errors)<1e-6 and bad_membership==0 and bad_logs==0)
 rows.append(dict(episode=ep.name,passed=passed,frames=len(excesses),configured_height_bound_m=bound,min_independent_height_excess_m=min(excesses),max_independent_height_excess_m=max(excesses),max_logged_vs_independent_error_m=max(errors),non_mesh_points=bad_membership,inconsistent_bound_logs=bad_logs))
out=dict(rows=rows,passed=len(rows)==2 and all(r['passed'] for r in rows),scope='Independent URDF FK and parcel orientation verify selected real vertex is at most configured distance above true hull supporting plane. Numerical tolerance1um, not added physical allowance. Does not certify footprint overlap, whole arm, task success or training admission.',training_ready=False)
(run/'SUPPORT_HYSTERESIS_LIVE_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
if not out['passed']:raise SystemExit(1)
