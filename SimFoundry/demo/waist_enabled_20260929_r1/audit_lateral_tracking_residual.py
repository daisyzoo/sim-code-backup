"""Recorded actuator target versus state, FK only; no controller changes."""
from pathlib import Path
import sys,ast,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent;repo=root.parents[1];sys.path.insert(0,str(repo))
s=(root/'audit_terminal_reach.py').read_text();exec(compile(s.split("p=root/'contact_x_ablation")[0],'<cached_fk>','exec'))
tree=ast.parse((root/'audit_front_short_recovery_kinematics.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fk'],type_ignores=[]),'<fk>','exec'))
from simfoundry.data.top_contact_bypass import support_vertex
r=root/'fresh_lateral_00_pilot_r1';results=[]
for ep in sorted(r.glob('case_840001/layout_*')):
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);a=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 controls=json.loads((ep/'expert_control.json').read_text());coord=json.loads((ep/'coordination.json').read_text());fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];side='right' if 'push_box' in ep.name else 'left';other='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';by_step={x['step']:x for x in coord};t=1199;rec=by_step[t];offset=np.array(rec['active_point_offset_local'] or [.20,0,.007]);goal=np.array(controls[t]['target_xyz']);targetnormal=ori[key][t];points={};fk_error={}
 for label,qs in [('measured',q[t]),('commanded',a[t])]:
  m,_,_=fk(side,qs);point=m[:3,3]+m[:3,:3]@offset
  support=support_vertex(side,Rotation.from_matrix(m[:3,:3]).as_quat(),targetnormal);physical=m[:3,3]+m[:3,:3]@np.array(support)
  points[label]=dict(fixed_control_point=point.tolist(),goal_minus_point=(goal-point).tolist(),actual_selected_support_point=physical.tolist(),fixed_point_goal_error_m=float(np.linalg.norm(goal-point)))
 for side_ in ['left','right']:
  m,_,_=fk(side_,q[t]);fk_error[side_]=float(np.linalg.norm(m[:3,3]+m[:3,:3]@np.array([.20,0,.007])-tr['palm_'+side_][t]))
 assert max(fk_error.values())<.0001
 tailq=q[-120:];taila=a[-120:]
 result=dict(episode=ep.name,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),recorded_fk_error_m=fk_error,actual_final_mode=controls[t]['mode'],goal_xyz=goal.tolist(),points=points,tail_state_max_drift_rad=np.max(np.abs(tailq-tailq[0]),axis=0).tolist(),tail_action_minus_state_mean_rad=(taila-tailq).mean(0).tolist(),final_action_minus_state_rad=(a[t]-q[t]).tolist(),final_waist_rad=float(q[t,0]),final_waist_command_rad=float(a[t,0]),last_frontal=fr[-1])
 results.append(result);print(json.dumps({k:v for k,v in result.items() if k not in ['last_frontal','raw_sha256']}),flush=True)
(r/'LATERAL_TRACKING_RESIDUAL.json').write_text(json.dumps(dict(rows=results,scope='Real upper11 target/state and independently matched FK. Commanded-pose FK is hypothetical instantaneous tracking, not replay or physical proof. Cannot uniquely distinguish gravity/friction/IK saturation; no actuator/controller changes or quality relaxation.',training_ready=False),indent=2))
