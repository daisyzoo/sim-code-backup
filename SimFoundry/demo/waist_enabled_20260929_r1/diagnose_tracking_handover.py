"""Measured handover window and actual one-step forecast error, no gate edits."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;sys.path[:0]=[str(w/'staged_contact_patch_approach'),str(w.parents[1])]
from articulated_hand_geometry import ArticulatedHandGeometry
p=Path(sys.argv[1]).resolve();repo=w.parents[1]
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
with np.load(p/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float);task=str(z['task_id'])
with np.load(p/'trace.npz') as z:tr={k:z[k] for k in z.files}
with np.load(p/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
side='right' if task=='push_box_to_bin' else 'left';key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';size=np.array([.14,.09,.045] if side=='right' else [.15,.145,.04]);osize=(.15,.145,.04) if side=='right' else (.14,.09,.045)
rows=json.loads((p/'region_approach.json').read_text())['rows'];by={r['step']:r for r in rows};forecasts=[];window=[]
def measure(q,t):
 g=model.scene_geometry(side,q,target_xyz=tr[key][t],target_quat=ori[key][t],other_xyz=tr[other][t],other_quat=ori[other][t],other_size=osize)
 points=(g['vertices']@g['hand_rotation'].T+g['hand_xyz']-g['target_xyz'])@g['target_rotation'];point=points[points[:,2].argmin()]
 return dict(top_gap_m=float(point[2]-size[2]/2),physical_point_local_xyz=point.tolist())
for r in rows:
 s=r['solver'];t=r['step']
 if not s:continue
 if s['top_gap_m']<=.012:window.append(dict(step=t,top_gap_m=s['top_gap_m'],inactive_error_m=s['inactive_error_m'],height_window_met=.003<=s['top_gap_m']<=.005,inactive_met=s['inactive_error_m']<.002,reason=s['reason']))
 if not s.get('joint_override') or s.get('handover') or t+1>=len(q):continue
 predicted=measure(u[t]+q[t]-u[t-1],t);actual=measure(q[t+1],t+1)
 forecasts.append(dict(step=t,predicted=predicted,actual=actual,height_forecast_error_m=actual['top_gap_m']-predicted['top_gap_m'],target_step_m=float(np.linalg.norm(tr[key][t+1]-tr[key][t])),nominal=measure(u[t],t)))
err=np.array([x['height_forecast_error_m'] for x in forecasts]);late=[x for x in forecasts if x['actual']['top_gap_m']<.012]
report=dict(episode=str(p),window=window,forecasts=forecasts,forecast_height_error_range_m=[float(err.min()),float(err.max())] if len(err) else None,late_forecast_error_range_m=[min(x['height_forecast_error_m'] for x in late),max(x['height_forecast_error_m'] for x in late)] if late else None,raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Independent recorded FK. Errors measure this rollout only, not a guaranteed disturbance bound. Handover windows and original guards unchanged.',training_ready=False)
(p/'TRACKING_HANDOVER_DIAGNOSIS.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='forecasts'},indent=2))
