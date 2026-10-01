"""Observed refined-action response; fixed current virtual reference, not future COP.
No fitted controller or causal gain claim. Joint contributions are first-order
URDF Jacobian terms; FK remainder is measured separately, not silently dropped.
"""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];ep=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0,str(repo))
a=json.loads((ep/'JOINT_EDGE_EXECUTION_LIVE_AUDIT.json').read_text());assert a['passed'] and a['selected'] and a['auditor_sha256']==sha(w/'audit_joint_edge_execution_live.py')
for n,h in a['source_sha256'].items():assert sha(ep/n)==h
tr=json.loads((ep/'JOINT_XY_ACTUAL_RESPONSE.json').read_text());assert tr['checker_sha256']==sha(w/'diagnose_joint_xy_actual_response.py')
for n,h in tr['source_sha256'].items():assert sha(ep/n)==h
prov=json.loads((ep.parent/'provenance.json').read_text());gp=next(n for n in prov['source_sha256'] if n.endswith('/articulated_hand_geometry.py'));gp=ep.parent/'source_snapshot'/gp
spec=importlib.util.spec_from_file_location('edge_tracking_fk',gp);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);model=m.ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';fr={f['step']:f for f in json.loads((ep/'frontal_bypass.json').read_text())['rows']};cs={c['step']:c for c in json.loads((ep/'coordination.json').read_text())};refined={r['step'] for r in a['records'] if r['refined']}
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:rots=Rotation.from_quat(z[key]).as_matrix()
rows=[]
for v in tr['rows']:
 t=v['step'];f=fr[t];offset=np.asarray(f['control_offset_local']);T,jl,jw=model.fk(side,q[t]);r=T[:3,:3]@offset;x,y,z=r;skew=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);J=jl-skew@jw
 inward=-np.sign(v['cop_local_x_mm']);axis=inward*rots[t,:,0];grad=axis@J;du=u[t]-q[t];dq=q[t+1]-q[t];nominal_joint=grad*du*1000;actual_joint=grad*dq*1000
 rows.append(dict(**v,refined=t in refined,command_joint_delta_rad=du.tolist(),observed_joint_delta_rad=dq.tolist(),nominal_joint_local_x_inward_mm=nominal_joint.tolist(),actual_joint_local_x_inward_mm=actual_joint.tolist(),nominal_linearization_remainder_mm=float(v['nominal_fixed_object_local_x_inward_mm']-nominal_joint.sum()),actual_linearization_remainder_mm=float(v['actual_fixed_object_local_x_inward_mm']-actual_joint.sum())))
summary={}
for name,group in [('all_joint_xy',[r for r in rows]),('final_joint_refined',[r for r in rows if r['refined']]),('parent_preserved',[r for r in rows if not r['refined']])]:
 assert group
 numeric=['nominal_fixed_object_local_x_inward_mm','actual_fixed_object_local_x_inward_mm','actual_relative_local_x_inward_mm','object_translation_contribution_inward_mm','axis_rotation_contribution_inward_mm']
 d=dict(frames=len(group),actual_fixed_outward_over_0_05mm=sum(r['actual_fixed_object_local_x_inward_mm']<-.05 for r in group),actual_relative_outward_over_0_05mm=sum(r['actual_relative_local_x_inward_mm']<-.05 for r in group),nominal_outward_over_0_05mm=sum(r['nominal_fixed_object_local_x_inward_mm']<-.05 for r in group),median={k:float(np.median([r[k] for r in group])) for k in numeric})
 for field in ['nominal_joint_local_x_inward_mm','actual_joint_local_x_inward_mm','command_joint_delta_rad','observed_joint_delta_rad']:d['median_'+field]=np.median([r[field] for r in group],axis=0).tolist()
 d['max_abs_actual_linearization_remainder_mm']=max(abs(r['actual_linearization_remainder_mm']) for r in group)
 summary[name]=d
out=dict(episode=ep.name,summary=summary,joint_order=['waist_yaw','left_shoulder_pitch','left_shoulder_roll','left_shoulder_yaw','left_elbow','left_wrist_roll','right_shoulder_pitch','right_shoulder_roll','right_shoulder_yaw','right_elbow','right_wrist_roll'],rows=rows,source_sha256={n:sha(ep/n) for n in ['JOINT_EDGE_EXECUTION_LIVE_AUDIT.json','JOINT_XY_ACTUAL_RESPONSE.json','raw.npz','coordination.json','frontal_bypass.json','parcel_orientation.npz']},checker_sha256=sha(Path(__file__)),training_ready=False,scope=__doc__)
(ep/'JOINT_EDGE_TRACKING_DIAGNOSIS.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(episode=ep.name,summary=summary),indent=2))
