"""Independent FK direction/height inspection of unissued diagnostic commands."""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_xy_nonlinear_conflict_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from audit_unloaded_wrist_prior_live import HandModel
hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json')
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin';cs={x['step']:x for x in read(ep/'coordination.json')};rows=[]
for t in [1008,1009,1141,1142,1143]:
 r=read(D/f'{t}_free_height_x_seed.json');c=cs[t];old=c['joint_transport_clearance'];tc=old['collector_context'];q=np.array(tc['current']);qp=np.array(tc['previous_q']);prev=np.array(tc['previous_command']);a=np.array(tc['decay']);u=np.array(r['command']);normal=Rotation.from_quat(tc['scene']['target_quat']).as_matrix()[:,2];center=np.array(c['active_support_reference']['center_local'])
 def point(v):
  T=hand.fk(v,'right');n=T[:3,:3].T@normal;off=center+n*(min(hand.vertices['right']@n)-center@n);return T[:3,3]+T[:3,:3]@off
 def predicted(v):return (1-a)*v+a*q+q-prev-a*(qp-prev)
 current=point(q); parent=np.array(old['parent_command']);actual=np.array(old['output_command'])
 deltas={k:((point(v)-current)*1000).tolist() for k,v in [('parent',parent),('actual_final',actual),('height_free',u),('height_free_predicted',predicted(u))]}
 signs=np.sign(np.array(c['task_inputs']['error'])[3:5]);signed={k:(np.array(v[:2])*signs).tolist() for k,v in deltas.items()}
 np.testing.assert_allclose(signed['height_free'],r['signed_xy_mm'],atol=1e-7,rtol=0)
 J=np.array(c['task_inputs']['jacobian']);parent_z=float(J[5]@(parent-q))*1000;new_z=float(J[5]@(u-q))*1000
 rows.append(dict(step=t,delta_xyz_mm=deltas,signed_xy_mm=signed,parent_linear_z_mm=parent_z,new_linear_z_mm=new_z,within_parent_downward_to_zero_band=bool(parent_z<=new_z<=0),nominal_downward=bool(deltas['height_free'][2]<0),predicted_xy_nonreversal=bool(min(signed['height_free_predicted'])>=-.0002)))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256={str(p):sha(p) for p in [Path(__file__),D/'RESULT.json',ep/'coordination.json']},training_ready=False,physics_started=False,limitations=['Independent FK only. No torque/contact dynamics or full-body/path proof.','Exact original parent height equality is intentionally violated by this diagnostic.','Predicted motion uses old history and is not observed response.'])
with (D/'INDEPENDENT_MOTION_V1.json').open('x') as f:json.dump(report,f,indent=2,allow_nan=False)
for r in rows:print(json.dumps(r))
