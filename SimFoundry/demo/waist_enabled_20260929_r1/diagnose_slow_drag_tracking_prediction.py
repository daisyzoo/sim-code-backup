"""Causal one-step tracking predictions scored on already-recorded physics.
All predictors use only observations/commands available at command step t.
No dynamics replay, future-contact certification, fitting to held-out model data,
controller edits or data admission. Fixed observed contact offset is used for
FK of every prediction and the next measured q; no future recapture is used.
"""
from pathlib import Path
import json,sys,hashlib,datetime
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_rear_slow_drag';sys.path[:0]=[str(stage),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
r=w/'rear_slow_drag_groups_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();geom=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');episodes=[]
for ep in sorted(r.glob('case_*/layout_*')):
 if not (ep/'SLOW_DRAG_NUMERIC_REVIEW.json').exists() or 'wait_no_package' in ep.name:continue
 nr=json.loads((ep/'SLOW_DRAG_NUMERIC_REVIEW.json').read_text());fr=json.loads((ep/'frontal_bypass.json').read_text());fs={x['step']:x for x in fr['rows']};side='right' if 'push_box' in ep.name else 'left'
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 loss_windows={t for b in nr['bouts'] if b['exit_reason']=='lost_contact' for t in range(max(b['start'],b['end']-11),b['end']+1)};rows=[];start=None
 for t in range(1,len(q)-1):
  f=fs[t]
  if f['mode']!='top_push':start=None;continue
  if start is None:start=t
  if t-start<5 or f['contact_load']['observed_vertical_load_n']<.3:continue
  offset=np.array(f['control_offset_local'])
  def point(x):
   T,_,_=geom.fk(side,x);return T[:3,3]+T[:3,:3]@offset
  p=point(q[t]);observed=np.array(f['observed_support_xyz']);assert np.max(abs(p-observed))<1e-6
  future=point(q[t+1]);hist=np.arange(max(start,t-20),t);assert hist[-1]+1==t
  # Per-joint affine first-order actuator approximation, fitted only to prior transitions.
  X=u[hist]-q[hist];Y=q[hist+1]-q[hist];xc=X-X.mean(0);yc=Y-Y.mean(0);den=np.sum(xc*xc,axis=0);alpha=np.clip(np.divide(np.sum(xc*yc,axis=0),den,out=np.full(11,.5),where=den>1e-12),0,1);bias=Y.mean(0)-alpha*X.mean(0)
  predictions={'nominal_target':u[t],'previous_tracking_residual':u[t]+q[t]-u[t-1],'causal_affine20':q[t]+alpha*(u[t]-q[t])+bias}
  entry=dict(step=t,near_loss=t in loss_windows,history_start=int(hist[0]),history_last_observed_state=t,loaded_n=f['contact_load']['observed_vertical_load_n'],actual_next_virtual_point_delta_mm=((future-p)*1000).tolist(),desired_point_delta_mm=((np.array(f['target_xyz'])-p)*1000).tolist(),predictions={})
  for name,pred in predictions.items():
   pp=point(pred);entry['predictions'][name]=dict(delta_mm=((pp-p)*1000).tolist(),point_error_mm=((pp-future)*1000).tolist(),joint_error_rad=(pred-q[t+1]).tolist())
  rows.append(entry)
 def summary(group):
  out={}
  for name in ['nominal_target','previous_tracking_residual','causal_affine20']:
   if not group:out[name]=None;continue
   e=np.array([v['predictions'][name]['point_error_mm'] for v in group]);actual=np.array([v['actual_next_virtual_point_delta_mm'] for v in group]);pred=np.array([v['predictions'][name]['delta_mm'] for v in group]);out[name]=dict(median_point_error_mm=float(np.median(np.linalg.norm(e,axis=1))),p90_point_error_mm=float(np.quantile(np.linalg.norm(e,axis=1),.9)),median_abs_z_error_mm=float(np.median(abs(e[:,2]))),predicted_upward_gt_0_1mm=int(sum(pred[:,2]>.1)),actual_upward_gt_0_1mm=int(sum(actual[:,2]>.1)))
  return out
 episodes.append(dict(episode=ep.name,rows=len(rows),loss_window_rows=sum(x['near_loss'] for x in rows),summary=summary(rows),loss_summary=summary([x for x in rows if x['near_loss']]),records=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','frontal_bypass.json','SLOW_DRAG_NUMERIC_REVIEW.json']}));print(ep.name,'rows',len(rows),'loss',json.dumps(episodes[-1]['loss_summary']),flush=True)
report=dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),episodes=episodes,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'articulated_hand_geometry.py',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json']},runtime_unchanged=True,training_ready=False,limitations=['Nominal up/down sign is not observed physical up/down; gravity, joint tracking and contacts matter.','In-sample logged-trajectory diagnostics only; causal history prevents future leakage but does not certify changed-action behavior.','Predicted q is not an executable or certified-safe command.'])
(r/'TRACKING_PREDICTION_DIAGNOSTIC.json').write_text(json.dumps(report,indent=2))
