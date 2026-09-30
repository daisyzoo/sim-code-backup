"""Recorded-cycle contact geometry verification, independent of planner helper."""
from pathlib import Path
import sys,json
import numpy as np
from scipy.spatial.transform import Rotation
run=Path(sys.argv[1]).resolve();assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 key='box' if 'push_box' in ep.name else 'mailer';direction=-1 if key=='box' else 1;d=json.loads((ep/'frontal_bypass.json').read_text());p=d['plan']['top_recontact'];half=np.array(p['contact_geometry']['collision_core_size_xyz'])/2;required=p['forward_margin_m'];ori=np.load(ep/'parcel_orientation.npz')[key];tr=np.load(ep/'trace.npz')[key];cycles={};latch_errors=[];surface_errors=[];margin_errors=[]
 for r in d['rows']:
  local=r.get('corner_local');t=r['step'];R=Rotation.from_quat(ori[t]).as_matrix()
  if local is not None:
   local=np.array(local);cycle=r['recontacts'];world=tr[t]+R@local;surface_errors.append(float(np.max(abs(world-r['parcel_top_xyz']))))
   if cycle not in cycles:
    advance=np.array([0.,direction*required,0.])@R;endpoint=local+advance
    cycles[cycle]=dict(first_step=t,local_point=local.tolist(),initial_xy_edge_margins_m=(half[:2]-abs(local[:2])).tolist(),forward_endpoint_xy_margins_m=(half[:2]-abs(endpoint[:2])).tolist())
   latch_errors.append(float(np.max(abs(local-np.array(cycles[cycle]['local_point'])))))
  if r.get('observed_forward_edge_distance_m') is not None:
   observed=(np.array(r['observed_support_xyz'])-tr[t])@R;vector=np.array([0.,direction,0.])@R
   distance=min((half[i]-np.sign(vector[i])*observed[i])/abs(vector[i]) for i in (0,1) if abs(vector[i])>1e-8)
   margin_errors.append(abs(float(distance)-r['observed_forward_edge_distance_m']))
 passed=bool(cycles and all(min(c['initial_xy_edge_margins_m'])>=.01-1e-7 and min(c['forward_endpoint_xy_margins_m'])>=-1e-7 for c in cycles.values()) and max(latch_errors)<1e-8 and max(surface_errors)<1e-6 and margin_errors and max(margin_errors)<1e-6)
 rows.append(dict(episode=ep.name,passed=passed,cycles=cycles,max_local_latch_change_m=max(latch_errors),max_planned_world_point_error_m=max(surface_errors),max_logged_forward_distance_error_m=max(margin_errors)))
out=dict(rows=rows,passed=len(rows)==2 and all(r['passed'] for r in rows),scope='Actual recorded parcel pose/core dimensions: each newly latched point starts inside10mm XY inset and its configured worldY forward-margin endpoint remains inside core XY; point remains fixed in local coordinates per contact cycle. Forward margin after object rotation/motion is measured, not guaranteed by initial latch. No contact/tilt/task success guarantee.',training_ready=False)
(run/'FORWARD_CONTACT_GEOMETRY_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
if not out['passed']:raise SystemExit(1)
