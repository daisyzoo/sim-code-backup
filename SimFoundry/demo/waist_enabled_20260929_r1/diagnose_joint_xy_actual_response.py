"""Measured next-frame frozen-offset virtual-reference direction versus Cartesian intent.
Uses a fixed current-frame virtual hand reference, never a future support vertex.
This projected reference need not lie on the hand mesh; it is not a material or contact point.
Observed response only: no counterfactual gain, COP prediction or safety proof.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent
ep=Path(sys.argv[1]).resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tracking_path=ep/'LOADED_WAYPOINT_TRACKING_DIAGNOSIS.json'
track=json.loads(tracking_path.read_text())
for name,digest in track['source_sha256'].items():assert sha(ep/name)==digest
assert track['checker_sha256']==sha(w/'diagnose_loaded_waypoint_tracking.py')
audit_path=ep/'REAR_JOINT_XY_LIVE_AUDIT.json'
audit=json.loads(audit_path.read_text());assert audit['passed'] and audit['enabled']
for name,digest in audit['source_sha256'].items():assert sha(ep/name)==digest
protocol=json.loads((ep.parent.parent/'PROTOCOL.json').read_text())
assert audit['auditor_sha256']==protocol['rear_cop_auditor_sha256']
fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']}
key='box' if 'push_box' in ep.name else 'mailer'
with np.load(ep/'trace.npz') as z:obj=z[key].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
rows=[]
for a in track['rows']:
 t=a['step'];f=fr[t];v=f.get('rear_joint_xy_progress',{})
 if not a['loaded'] or not v.get('override'):continue
 point=np.asarray(f['observed_support_xyz']);actual=np.asarray(a['actual_delta_mm'])/1000;nominal=np.asarray(a['nominal_delta_mm'])/1000;intent=np.asarray(f['target_xyz'])-point
 current_relative=point-obj[t];next_relative=point+actual-obj[t+1]
 current_local=rot[t].T@current_relative
 measured_local=rot[t+1].T@next_relative-current_local
 hand_components=rot[t,:,0]*actual
 object_contribution=-float(rot[t,:,0]@(obj[t+1]-obj[t]))
 rotation_contribution=float((rot[t+1,:,0]-rot[t,:,0])@next_relative)
 assert abs(measured_local[0]-sum(hand_components)-object_contribution-rotation_contribution)<2e-7
 # Orient positive towards core centre using the independently audited current COP.
 cop=np.asarray(f['rear_cop_centering']['cop_world']);local_cop=rot[t].T@(cop-obj[t]);inward=-np.sign(local_cop[0])
 rows.append(dict(step=t,cop_local_x_mm=float(local_cop[0]*1000),intent_local_x_inward_mm=float(inward*(rot[t].T@intent)[0]*1000),nominal_fixed_object_local_x_inward_mm=float(inward*(rot[t].T@nominal)[0]*1000),actual_fixed_object_local_x_inward_mm=float(inward*(rot[t].T@actual)[0]*1000),actual_relative_local_x_inward_mm=float(inward*measured_local[0]*1000),actual_hand_world_xyz_contributions_inward_mm=(inward*hand_components*1000).tolist(),object_translation_contribution_inward_mm=float(inward*object_contribution*1000),axis_rotation_contribution_inward_mm=float(inward*rotation_contribution*1000),measured_point_xyz_delta_mm=(actual*1000).tolist(),nominal_point_xyz_delta_mm=(nominal*1000).tolist()))
assert rows
summary=dict(changed_loaded_next_frame_samples=len(rows),intent_inward_actual_outward=sum(r['intent_local_x_inward_mm']>=-1e-6 and r['actual_relative_local_x_inward_mm']<-.05 for r in rows),nominal_inward_actual_outward=sum(r['nominal_fixed_object_local_x_inward_mm']>.05 and r['actual_relative_local_x_inward_mm']<-.05 for r in rows))
for name in ['intent_local_x_inward_mm','nominal_fixed_object_local_x_inward_mm','actual_fixed_object_local_x_inward_mm','actual_relative_local_x_inward_mm','object_translation_contribution_inward_mm','axis_rotation_contribution_inward_mm']:
 summary[name]=dict(median=float(np.median([r[name] for r in rows])),p10=float(np.percentile([r[name] for r in rows],10)),p90=float(np.percentile([r[name] for r in rows],90)))
out=dict(episode=ep.name,summary=summary,rows=rows,source_sha256={n:sha(ep/n) for n in ['LOADED_WAYPOINT_TRACKING_DIAGNOSIS.json','REAR_JOINT_XY_LIVE_AUDIT.json','trace.npz','parcel_orientation.npz','frontal_bypass.json']},checker_sha256=sha(Path(__file__)),training_ready=False,scope=__doc__)
(ep/'JOINT_XY_ACTUAL_RESPONSE.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(episode=ep.name,summary=summary),indent=2))
