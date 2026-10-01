"""One-step predictions from past observations only; never executes commands."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w/'staged_contact_patch_approach'),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
cases=[w/'region_patch_groups_r1/case_840001/layout_840001_push_box_to_bin',w/'fresh_lateral_00_trial_v2_r1/case_840001/layout_840001_push_box_to_bin',w/'fresh_diagonal_02_trial_v2_r1/case_840004/layout_840004_nudge_mailer_to_bin',w/'contact_bout_yaw_groups_r1/case_898001/layout_898001_push_box_to_bin'];reports=[]
for ep in cases:
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 fr={x['step']:x for x in json.loads((ep/'frontal_bypass.json').read_text())['rows']};coord={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);half=size[:2]/2-.01;records=[];filtered=np.zeros(11)
 for t in range(1,min(len(q)-1,230)):
  residual=q[t]-u[t-1];filtered=.5*residual+.5*filtered
  row=fr.get(t,{})
  if row.get('mode') not in ['top_cross','top_descend'] or coord[t]['contact_normal_tracking'] is not None:continue
  if row.get('contact_load',{}).get('observed_vertical_load_n',0.)>=.2:continue
  rot=Rotation.from_quat(ori[key][t]).as_matrix();center=tr[key][t].astype(float)
  def point(joints):
   m,_,_=model.fk(side,joints);local=(model.vertices[side]@m[:3,:3].T+m[:3,3]-center)@rot;i=int(local[:,2].argmin());return local[i],i
  actual,index=point(q[t+1]);results={}
  for name,pred in [('command_only',u[t]),('last_tracking_residual',u[t]+residual),('filtered_tracking_residual',u[t]+filtered),('constant_velocity',q[t]+q[t]-q[t-1])]:
   predicted,pi=point(pred);results[name]=dict(joint_max_error_rad=float(np.max(abs(pred-q[t+1]))),active_joint_max_error_rad=float(np.max(abs((pred-q[t+1])[6:11] if side=='right' else (pred-q[t+1])[1:6]))),point_local_xyz_m=predicted.tolist(),point_error_mm=(1000*(predicted-actual)).tolist(),point_xy_error_mm=float(1000*np.linalg.norm(predicted[:2]-actual[:2])),support_index=pi,inside_10mm_inset=bool(np.all(abs(predicted[:2])<=half)),minimum_xy_margin_mm=float(1000*np.min(half-abs(predicted[:2]))))
  records.append(dict(step=t,mode=row['mode'],actual_next_point_local_xyz_m=actual.tolist(),actual_next_support_index=index,actual_next_inside=bool(np.all(abs(actual[:2])<=half)),actual_next_minimum_margin_mm=float(1000*np.min(half-abs(actual[:2]))),target_next_displacement_m=float(np.linalg.norm(tr[key][t+1]-tr[key][t])),causal_tracking_residual_rad=residual.tolist(),predictions=results))
 stats={}
 for name in ['command_only','last_tracking_residual','filtered_tracking_residual','constant_velocity']:
  rr=[x for x in records if x['target_next_displacement_m']<1e-5];errors=[x['predictions'][name]['point_xy_error_mm'] for x in rr];stats[name]=dict(stable_target_samples=len(rr),point_xy_error_mm={tag:float(np.quantile(errors,pct)) for tag,pct in [('median',.5),('p90',.9),('max',1.)]} if errors else {},false_safe_count=sum(x['predictions'][name]['inside_10mm_inset'] and not x['actual_next_inside'] for x in rr),false_unsafe_count=sum(not x['predictions'][name]['inside_10mm_inset'] and x['actual_next_inside'] for x in rr))
 reports.append(dict(episode=str(ep),summary=stats,records=records,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest()));print(ep.name,json.dumps(stats),flush=True)
report=dict(rows=reports,scope='Predictions at action t use q<=t and executed commands<=t only, scored against recorded q[t+1]. Object pose frozen at t for both FK evaluations; stats separately restrict next target displacement<10um. Early unloaded modes only. These are retrospective predictions of recorded commands, NOT modified-policy rollout, calibrated uncertainty guarantees, physics simulation or training admission.',training_ready=False,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),geometry_source_sha256=model.source_sha256)
(w/'CAUSAL_REGION_TRACKING_PREDICTION.json').write_text(json.dumps(report,indent=2))
