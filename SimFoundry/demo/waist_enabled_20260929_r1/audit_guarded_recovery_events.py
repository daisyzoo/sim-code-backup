"""Verify recorded guard triggers and whole-hand height during recovery crossing."""
from pathlib import Path
import json,sys
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text();exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
run=Path(sys.argv[1]).resolve();assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending';mesh=json.loads((root.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'];rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';z=np.load(ep/'raw.npz');tr=np.load(ep/'trace.npz');ori=np.load(ep/'parcel_orientation.npz');d=json.loads((ep/'frontal_bypass.json').read_text());vertices=np.array(mesh[side]);events=[];cross=[];prior=0
 for r in d['rows']:
  t=r['step'];count=r.get('recontacts',0)
  if count>prior:
   c=r.get('loaded_contact_geometry');reason=r['last_recontact_reason'];valid=(reason=='loaded_edge_margin' and c and c['valid'] and c['normal_load_n']>.3 and c['weighted_forward_edge_distance_m']<d['plan']['top_recontact']['edge_guard_m']) or (reason=='incipient_tilt' and r['observed_parcel_tilt_rad']>.03) or (reason=='hand_obstacle_clearance' and r.get('hand_obstacle_gap_m') is not None and r['hand_obstacle_gap_m']<d['plan']['top_recontact'].get('hand_obstacle_guard_m',0)) or reason=='lost_contact'
   events.append(dict(step=t,reason=reason,trigger_matches_record=bool(valid),mode=r['mode'],applied_load_bias_m=r['contact_load']['applied_z_bias_m'],travel_height_m=r['travel_height_m']));prior=count
  if r['mode']!='top_cross' or not count:continue
  q=dict(zip(names,z['q'][t,12:23]));m=np.eye(4);m[:3,3]=[.08,0,.793]
  for name,origin,axis in chains[side]:
   m=m@origin
   if axis is not None:a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@a
  minimum=float((vertices@m[:3,:3].T+m[:3,3])[:,2].min());upper=[]
  for obj,size in [('box',(.14,.09,.045)),('mailer',(.15,.145,.04))]:
   rot=Rotation.from_quat(ori[obj][t]).as_matrix();upper.append(float(tr[obj][t,2]+np.dot(abs(rot[2]),np.array(size)/2)))
  cross.append(dict(step=t,whole_hand_min_z_m=minimum,highest_parcel_visual_aabb_z_m=max(upper),clearance_m=minimum-max(upper)))
 passed=bool(events and all(e['trigger_matches_record'] and e['mode']=='top_lift' and e['applied_load_bias_m']==0 for e in events))
 rows.append(dict(episode=ep.name,guard_bookkeeping_passed=passed,events=events,min_recovery_cross_clearance_m=min((x['clearance_m'] for x in cross),default=None),crossing_samples=cross));print(ep.name,'events',[(x['step'],x['reason']) for x in events],'cross min',min((x['clearance_m'] for x in cross),default=None),'bookkeeping',passed)
(run/'GUARD_EVENT_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Recorded guard reason/observation/mode/bias consistency; whole hand collision hull FK minimum worldZ vs conservative actual visual parcel AABB highest Z during recovery top_cross. Positive sampled hand clearance is not whole-arm swept-path or all-substep certification; use ARM_CONTACT and actual review separately. Lost-contact reason not re-derived from force history here.',training_ready=False),indent=2))
if not all(r['guard_bookkeeping_passed'] for r in rows):raise SystemExit(1)
