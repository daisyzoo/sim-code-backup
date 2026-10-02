"""Causal previous-command tracking residual versus NEXT realized FK residual.
Observation-only diagnostic. Same current material point used throughout each
comparison. Never claims compensation efficacy without new physical execution.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();model=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');ep=Path(sys.argv[1]).resolve();dest=ep/'RECOVERY_TRACKING_PREDICTABILITY.json';assert not dest.exists();rr={r['step']:r for r in json.loads((ep/'rear_corridor_recovery.json').read_text())['rows']};post={r['step']:r for r in json.loads((ep/'self_clearance.json').read_text())['rows'] if r['phase']=='post'}
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
side='right' if 'push_box' in ep.name else 'left';rows=[]
for t,r in rr.items():
 if r['kind']!='loaded_recovery' or rr.get(t-1,{}).get('kind')!='loaded_recovery':continue
 offset=np.asarray(r['parent_row']['control_offset_local']);qpost=np.asarray(post[t]['upper_q'])
 def point(x):
  T=model.fk(x,side);return T[:3,3]+T[:3,:3]@offset
 observed=point(q[t]);assert np.max(abs(observed-np.asarray(r['parent_row']['observed_support_xyz'])))<2e-6
 predicted=observed-point(u[t-1]);real=point(qpost)-point(u[t]);nominal=point(u[t])-observed;actual=point(qpost)-observed
 rows.append(dict(step=t,previous_observed_tracking_residual_mm=(predicted*1000).tolist(),actual_next_tracking_residual_mm=(real*1000).tolist(),prediction_error_mm=((real-predicted)*1000).tolist(),nominal_motion_mm=(nominal*1000).tolist(),actual_motion_mm=(actual*1000).tolist()))
arr=lambda key:np.asarray([r[key] for r in rows]);err=arr('prediction_error_mm');observed=arr('previous_observed_tracking_residual_mm');target=arr('actual_next_tracking_residual_mm');summary=dict(same_recovery_successor_frames=len(rows),previous_bias_median_xyz_mm=np.median(observed,axis=0).tolist(),next_bias_median_xyz_mm=np.median(target,axis=0).tolist(),prediction_mae_xyz_mm=abs(err).mean(0).tolist(),prediction_p95_abs_xyz_mm=np.quantile(abs(err),.95,axis=0).tolist(),prediction_max_abs_xyz_mm=abs(err).max(0).tolist(),zero_bias_prediction_mae_xyz_mm=abs(target).mean(0).tolist())
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,summary=summary,rows=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','self_clearance.json','rear_corridor_recovery.json']},analyzer_sha256=sha(__file__),independent_fk_sha256=sha(W/'audit_unloaded_wrist_prior_live.py'),training_ready=False);dest.write_text(json.dumps(report,indent=2));print(json.dumps(summary,indent=2))
