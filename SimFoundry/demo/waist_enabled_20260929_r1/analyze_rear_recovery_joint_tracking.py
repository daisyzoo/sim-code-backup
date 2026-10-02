"""Observed tracking-error contribution to frozen material-point X motion.
Finite-difference URDF FK, actual pre/post joint states and emitted commands.
This is a local kinematic decomposition, not an actuator/friction causal proof.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_unloaded_wrist_prior_live import HandModel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();model=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');ep=Path(sys.argv[1]).resolve();out=ep/'REAR_RECOVERY_JOINT_TRACKING_FINDINGS.json';assert not out.exists()
rr=json.loads((ep/'rear_corridor_recovery.json').read_text())['rows'];post={r['step']:r for r in json.loads((ep/'self_clearance.json').read_text())['rows'] if r['phase']=='post'}
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
side='right' if 'push_box' in ep.name else 'left';records=[];h=2e-7
for r in rr:
 if r['kind']!='loaded_recovery':continue
 t=r['step'];offset=np.asarray(r['parent_row']['control_offset_local']);actual=np.asarray(post[t]['upper_q']);current=q[t];command=u[t]
 def point(x):
  T=model.fk(x,side);return T[:3,3]+T[:3,:3]@offset
 origin=point(current);nominal=point(command)-origin;real=point(actual)-origin
 J=np.column_stack([(point(current+np.eye(11)[j]*h)-point(current-np.eye(11)[j]*h))/(2*h) for j in range(11)])
 loss=J[0]*(actual-command)*1000
 records.append(dict(step=t,nominal_x_mm=float(nominal[0]*1000),actual_x_mm=float(real[0]*1000),actual_minus_command_q_rad=(actual-command).tolist(),linearized_x_loss_by_joint_mm=loss.tolist(),nonlinear_residual_mm=float((real[0]-nominal[0])*1000-loss.sum())))
a=np.asarray([x['linearized_x_loss_by_joint_mm'] for x in records]);err=np.asarray([x['actual_minus_command_q_rad'] for x in records]);joints=[dict(joint=name,mean_x_loss_mm=float(a[:,i].mean()),median_x_loss_mm=float(np.median(a[:,i])),mean_tracking_error_rad=float(err[:,i].mean()),median_tracking_error_rad=float(np.median(err[:,i]))) for i,name in enumerate(model.names)];joints.sort(key=lambda x:x['mean_x_loss_mm']);summary=dict(recovery_steps=len(records),nominal_x_median_mm=float(np.median([r['nominal_x_mm'] for r in records])),actual_x_median_mm=float(np.median([r['actual_x_mm'] for r in records])),max_abs_nonlinear_residual_mm=max(abs(r['nonlinear_residual_mm']) for r in records),joint_contributions=joints)
sources=['raw.npz','rear_corridor_recovery.json','self_clearance.json'];report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,summary=summary,records=records,source_sha256={n:sha(ep/n) for n in sources},independent_fk_sha256=sha(W/'audit_unloaded_wrist_prior_live.py'),analyzer_sha256=sha(__file__),training_ready=False);out.write_text(json.dumps(report,indent=2));print(json.dumps(summary,indent=2))
