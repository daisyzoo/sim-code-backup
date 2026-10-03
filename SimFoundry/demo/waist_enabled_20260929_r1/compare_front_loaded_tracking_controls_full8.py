"""Descriptive same-run success/failure comparison; no causal or admission claim.
Only episodes with a completed independent native pose audit are included.
Compare the first25 top_push observations (24 observation intervals) as well as
whole first bouts. Supporting-point motion is not identical to palm-center
motion when orientation changes; both logged reference and object-frame
coordinates are retained. No counterfactual later states are reused.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;RUN=W/'front_initial_physical_r1';OUT=W/'FRONT_LOADED_TRACKING_SUCCESS_CONTROLS_FULL8.json';assert not OUT.exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
paths=sorted(RUN.glob('case_*/layout_*/FRONT_LOADED_TRACKING_RESIDUAL_V2_DIAGNOSTIC.json'));assert len(paths)==8
rows=[];sources={str(Path(__file__)):sha(__file__)}
for path in paths:
 d=json.loads(path.read_text());ep=path.parent;fr=json.loads((ep/'frontal_bypass.json').read_text());review=json.loads((ep/'FRONT_INITIAL_STAGE_NUMERIC_REVIEW.json').read_text());first=d['bouts'][0];key='box' if fr['plan']['direction']==-1 else 'mailer';side='right' if key=='box' else 'left';direction=fr['plan']['direction']
 for p in [path,ep/'frontal_bypass.json',ep/'FRONT_INITIAL_STAGE_NUMERIC_REVIEW.json',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'coordination.json',ep/'ACTUAL_REVIEW_BINDING.json']:
  assert p.exists();sources[str(p)]=sha(p)
 for name,value in d['source_sha256'].items():assert sha(name)==value
 with np.load(ep/'trace.npz') as z:obj=z[key].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
 observed={r['step']:r for r in fr['rows']};diag={r['step']:r for r in d['rows']};coord={r['step']:r for r in json.loads((ep/'coordination.json').read_text())}
 windows=[]
 for label,end in [('first25_observations',first['start']+24),('whole_first_bout',first['end'])]:
  assert end<=first['end'];ts=list(range(first['start'],end+1));rr=[diag[t] for t in ts];assert all(r['bout']==1 for r in rr)
  support=np.array([observed[t]['observed_support_xyz'] for t in ts]);palm=np.array([coord[t]['palm_positions'][side] for t in ts]);objects=obj[ts];rotation=rot[ts]
  local=np.einsum('nji,nj->ni',rotation,support-objects);relative=support-objects
  def motion(a):
   return dict(net_xy_mm=(1000*(a[-1,:2]-a[0,:2])).tolist(),net_xy_norm_mm=float(np.linalg.norm(a[-1,:2]-a[0,:2])*1000),xy_path_mm=float(np.linalg.norm(np.diff(a[:,:2],axis=0),axis=1).sum()*1000))
  windows.append(dict(window=label,start=ts[0],end=ts[-1],observations=len(ts),object_signed_y_progress_mm=float(direction*(objects[-1,1]-objects[0,1])*1000),object=motion(objects),support_reference=motion(support),palm_center=motion(palm),support_minus_object_world=motion(relative),support_in_object_frame=motion(local),mean_of_all24_substep_vertical_load_N=float(np.mean([r['previous_action24_load']['mean'] for r in rr])),median_kinematic_target_z_minus_observed_mm=float(np.median([r['kinematic_target_minus_observed_mm'][2] for r in rr])),median_joint_tracking_error_rad=float(np.median([r['active_joint_tracking_error_max_rad'] for r in rr])),bias_at_original_min_frames=sum(abs(r['bias_m']+.006)<1e-10 for r in rr),median_contact_tangent_L1_over_normal=float(np.median([x for r in rr for x in r['last_tick_contact_tangent_L1_over_normal']]))))
 rows.append(dict(episode=ep.name,task_and_pose_passed=review['original_task_and_pose_passed'],whole_episode_progress_mm=review['progress_mm'],non_target_max_xy_mm=review['non_target_max_xy_mm'],first_bout_exit=first['exit_reason'],first_bout_frames=first['frames'],windows=windows))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,conditions=rows,source_sha256=sources,coverage='All8 same-run pushes with completed native pose audits:2 failures and6 numeric task/pose successes. Different layouts, not matched causal interventions; full control audits still required.',findings=['Successful bag840022 and box840022 also have negative kinematic targetZ residual and original minimum pressure bias; those features alone cannot classify failure.','First-bout lost_contact occurs in successful bag840022, and incipient_tilt in successful box840022/840023; episode outcome must remain original full task/pose gates.'],next_action='Retain queued full matched material-relative cap comparison. Measure target progress, contact duration, repeat losses, posture and whole-episode non-target motion. Do not increase pressure solely based on tracking residual.',training_ready=False,quality_gates_changed=False)
OUT.write_text(json.dumps(report,indent=2))
for r in rows:
 x=r['windows'][0];print(json.dumps(dict(episode=r['episode'],passed=r['task_and_pose_passed'],first25_progress_mm=x['object_signed_y_progress_mm'],support_relative_xy_mm=x['support_minus_object_world']['net_xy_norm_mm'],load_N=x['mean_of_all24_substep_vertical_load_N'],target_z_residual_mm=x['median_kinematic_target_z_minus_observed_mm'],bias_min_frames=x['bias_at_original_min_frames']),ensure_ascii=False))
