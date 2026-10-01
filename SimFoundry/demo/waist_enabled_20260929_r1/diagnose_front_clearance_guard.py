"""Recompute first actual front stop; retain motion and command decomposition."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from scipy.spatial.transform import Rotation
p=Path(sys.argv[1]).resolve();log=json.loads((p/'frontal_bypass.json').read_text());assert log['plan']['front_route_selected'];rows={x['step']:x for x in log['rows']};guard=next(x for x in log['rows'] if x['mode']=='front_guard_lift');t=guard['step'];key='box' if 'push_box' in p.name else 'mailer';other='mailer' if key=='box' else 'box';sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])}
with np.load(p/'trace.npz') as z:tr={k:z[k].astype(float) for k in sizes}
with np.load(p/'parcel_orientation.npz') as z:radii={k:abs(Rotation.from_quat(z[k]).as_matrix())@sizes[k]/2 for k in sizes}
e=[]
for k in range(max(1,t-5),t+1):
 r=rows[k];dx=tr[other][k,0]-tr[key][k,0]-radii[other][k,0]-radii[key][k,0];dy=abs(tr[other][k,1]-tr[key][k,1])-radii[other][k,1]-radii[key][k,1];a=dict(step=k,mode=r['mode'],route_stage=r['route_stage'],aabb_gap_x_mm=dx*1000,aabb_gap_y_mm=dy*1000,max_axis_gap_mm=max(dx,dy)*1000,target_x_m=tr[key][k,0],target_radius_x_m=radii[key][k,0],hand_obstacle_gap_mm=r['hand_obstacle_gap_m']*1000,non_target_delta_mm=np.linalg.norm(tr[other][k,:2]-tr[other][0,:2])*1000)
 f=r.get('cop_slip_following',{})
 if f.get('override'):
  a.update(goal_x_m=r['route_goal_x'],goal_error_x_mm=(r['route_goal_x']-tr[key][k,0])*1000,route_anchor_reset=f.get('route_anchor_reset'),drive_xy_mm=(np.asarray(f['drive_xy'])*1000).tolist(),anchor_feed_xy_mm=(np.asarray(f['object_anchor_translation_xy'])*1000).tolist(),slip_correction_xy_mm=(np.asarray(f['slip_correction_xy'])*1000).tolist(),command_delta_xy_mm=(np.asarray(f['command_delta_xy'])*1000).tolist())
 e.append(a)
if guard['route_stop_reason']=='parcel_clearance_10mm':assert e[-1]['max_axis_gap_mm']<10 and (len(e)<2 or e[-2]['max_axis_gap_mm']>=10)
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();out=dict(first_guard_step=t,reason=guard['route_stop_reason'],rows=e,source_sha256={f:sha(p/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json']},auditor_sha256=sha(__file__),scope='Original nominal oriented-envelope AABB guard independently reconstructed from measured poses, last6 pre-action observations. COP command terms are recorded, require independent COP audit separately. No collision, all-substep safety, unique-cause or alternate-controller-success claim. Original10mm guard unchanged.',training_ready=False);(p/'FIRST_PARCEL_GUARD_DIAGNOSIS.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(first_guard_step=t,reason=guard['route_stop_reason'],rows=e),indent=2))
