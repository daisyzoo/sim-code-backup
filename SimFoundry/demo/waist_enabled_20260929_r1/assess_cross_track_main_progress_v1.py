"""Assess nominal and same-context predicted motion; never predicted task success."""
from pathlib import Path
import datetime,gzip,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_cross_track_full_stream_probe_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from audit_unloaded_wrist_prior_live import HandModel
hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();report=read(D/'RESULT.json');ep=W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin';co={r['step']:r for r in read(ep/'coordination.json')};rows=[];sources={str(Path(__file__)):sha(__file__),str(D/'RESULT.json'):sha(D/'RESULT.json'),str(ep/'coordination.json'):sha(ep/'coordination.json')}
for r in report['rows']:
 p=Path(r['detail']);assert sha(p)==r['detail_sha256'];d=json.loads(gzip.decompress(p.read_bytes()));new=d['proposal'];c=co[r['step']];old=c['joint_transport_clearance']['proposal'];normal=Rotation.from_quat(new['scene']['target_quat']).as_matrix()[:,2];center=np.array(c['active_support_reference']['center_local']);q=np.array(new['current'])
 def point(v):
  T=hand.fk(v,'right');n=T[:3,:3].T@normal;off=center+n*(min(hand.vertices['right']@n)-center@n);return T[:3,3]+T[:3,:3]@off
 current=point(q);deltas={label:((point(state)-current)*1000).tolist() for label,state in [('old_nominal',old['command']),('new_nominal',new['command']),('old_predicted',old['predicted_q']),('new_predicted',new['predicted_q'])]};request=np.array(c['task_inputs']['error'][3:5]);rows.append(dict(step=r['step'],request_xy_mm=(request*1000).tolist(),delta_xyz_mm=deltas,new_nominal_y_reversed=bool(np.sign(request[1])*deltas['new_nominal'][1]<-.0002),new_predicted_x_reversed=bool(np.sign(request[0])*deltas['new_predicted'][0]<-.0002),new_predicted_y_reversed=bool(np.sign(request[1])*deltas['new_predicted'][1]<-.0002)))
summary=dict(contexts=len(rows),new_nominal_y_reversed=sum(r['new_nominal_y_reversed'] for r in rows),new_predicted_x_reversed=sum(r['new_predicted_x_reversed'] for r in rows),new_predicted_y_reversed=sum(r['new_predicted_y_reversed'] for r in rows),mean_signed_right_y_mm={label:float(np.mean([-r['delta_xyz_mm'][label][1] for r in rows])) for label in ['old_nominal','new_nominal','old_predicted','new_predicted']},maximum_new_predicted_positive_x_mm=max(r['delta_xyz_mm']['new_predicted'][0] for r in rows))
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,summary=summary,rows=rows,source_sha256=sources,installed=False,training_ready=False,limitations=['Candidate nominal command is constrained; predicted motion is not included in that additional constraint.','Prediction uses original recorded causal decay/bias; actual next state under candidate has never been observed.','No claim of improved parcel displacement, contact retention, or elimination of recovery.'])
with (D/'MAIN_PROGRESS_AND_PREDICTION_V1.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(summary))
for r in rows:
 if r['step'] in [1009,1147]:print(json.dumps(r))
