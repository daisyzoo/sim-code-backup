"""Independent FK and old-response calibration for all34 proposed contexts."""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_xy_height_band_probe_r2';sys.path[:0]=[str(S),str(W),str(ROOT)]
from audit_unloaded_wrist_prior_live import HandModel
urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=ROOT/'assets/robots/g1_hand_support_vertices.json';hand=HandModel(urdf,vertices)
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin';cs={r['step']:r for r in read(ep/'coordination.json')};report=read(D/'RESULT.json');rows=[]
with np.load(ep/'raw.npz') as raw:qs=raw['q'][:,12:23].astype(float);actions=raw['action'][:,12:23].astype(float)
for r in report['rows']:
 t=r['step'];c=cs[t];old=c['joint_transport_clearance'];tc=old['collector_context'];q=np.array(tc['current']);qp=np.array(tc['previous_q']);prev=np.array(tc['previous_command']);a=np.array(tc['decay']);np.testing.assert_array_equal(q,qs[t]);np.testing.assert_array_equal(old['output_command'],actions[t]);normal=Rotation.from_quat(tc['scene']['target_quat']).as_matrix()[:,2];center=np.array(c['active_support_reference']['center_local'])
 def point(v):
  T=hand.fk(v,'right');n=T[:3,:3].T@normal;off=center+n*(min(hand.vertices['right']@n)-center@n);return T[:3,3]+T[:3,:3]@off
 def pred(v):return (1-a)*v+a*q+q-prev-a*(qp-prev)
 base=point(q);old_pred=(point(pred(actions[t]))-base)*1000;observed=(point(qs[t+1])-base)*1000
 row=dict(step=t,original_predicted_xyz_mm=old_pred.tolist(),original_next_observed_xyz_mm=observed.tolist(),original_prediction_error_xyz_mm=(old_pred-observed).tolist(),selection_rejected=r.get('selection_rejected',False))
 if r['command'] is not None:
  u=np.array(r['command']);v=pred(u);nom=(point(u)-base)*1000;newpred=(point(v)-base)*1000;sgn=np.sign(np.array(c['task_inputs']['error'])[3:5]);np.testing.assert_allclose(nom,r['nominal_delta_mm'],atol=1e-7,rtol=0);np.testing.assert_allclose(newpred,r['predicted_delta_mm'],atol=1e-7,rtol=0)
  row.update(new_nominal_xyz_mm=nom.tolist(),new_predicted_xyz_mm=newpred.tolist(),predicted_z_change_vs_old_mm=float(newpred[2]-old_pred[2]),independent_nominal_xy_nonreversal=bool(np.min(sgn*nom[:2])>=-.0002),independent_predicted_xy_nonreversal=bool(np.min(sgn*newpred[:2])>=-.0002),nominal_downward=bool(nom[2]<0))
 rows.append(row)
err=np.array([r['original_prediction_error_xyz_mm'] for r in rows]);active=[r for r in rows if not r['selection_rejected']]
summary=dict(contexts=len(rows),proposals=len(active),independent_nominal_and_predicted_directions_passed=sum(r['independent_nominal_xy_nonreversal'] and r['independent_predicted_xy_nonreversal'] for r in active),nominal_downward=sum(r['nominal_downward'] for r in active),new_predicted_upward=sum(r['new_predicted_xyz_mm'][2]>0 for r in active),original_predicted_upward=sum(r['original_predicted_xyz_mm'][2]>0 for r in active),original_observed_upward=sum(r['original_next_observed_xyz_mm'][2]>0 for r in active),original_prediction_absolute_error_mean_xyz_mm=np.mean(abs(err),axis=0).tolist(),original_prediction_absolute_error_max_xyz_mm=np.max(abs(err),axis=0).tolist(),new_predicted_z_change_mean_mm=float(np.mean([r['predicted_z_change_vs_old_mm'] for r in active])),new_predicted_z_change_range_mm=[min(r['predicted_z_change_vs_old_mm'] for r in active),max(r['predicted_z_change_vs_old_mm'] for r in active)])
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,summary=summary,rows=rows,source_sha256={str(p):sha(p) for p in [Path(__file__),D/'RESULT.json',ep/'coordination.json',ep/'raw.npz',urdf,vertices]},training_ready=False,physics_started=False,limitations=['Observed response belongs to original commands only; no observation exists for candidates.','Changing a support center or normal after the step is intentionally excluded; these are comparable frozen-reference support points, not tracked COP.','Original forecast error means predicted direction/contact cannot be treated as guaranteed.','No independent numerical optimality or continuous-path proof in this motion check.'])
with (D/'INDEPENDENT_MOTION_AND_PREDICTION_ERROR_V1.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
print(json.dumps(summary))
