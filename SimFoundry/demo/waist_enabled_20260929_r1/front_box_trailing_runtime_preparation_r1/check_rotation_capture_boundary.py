"""Reproduce an integration rejection for target rotation below original motion gate.
This is a constructed admissible adapter boundary, not a recorded physical handover.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_joint_transport_reserve_v1';sys.path[:0]=[str(D),str(S),str(ROOT)]
from trailing_adapter import apply
from recontact_scene import RecontactScene
from clearance_runtime import ClearanceGuard
src=W/'front_box_trailing_landing_reserve_probe_r1/RESULT.json';case=json.loads(src.read_text())['contexts'][0];p=case['planning'];z=p['scene'];guard=ClearanceGuard(ROOT,S);old=RecontactScene(guard,**z);newz=dict(z,target_quat=(Rotation.from_rotvec([0,0,.001])*Rotation.from_quat(z['target_quat'])).as_quat().tolist());new=RecontactScene(guard,**newz);motion=new.moved_since(old);assert not motion['changed'];frozen=np.asarray(p['landing_preference_local_xy']);actual=(new.rotation.T@np.array([0,.020,0]))[:2];assert max(abs(frozen-actual))<.0020002
state=SimpleNamespace(recontacts=1,size=np.asarray(z['core_size']));event=dict(kind='handover',context=dict(recontacts=1),measured_ready_count=3,reference={},observed_support_xyz=new.target.tolist(),selected_surface_local_xy=frozen.tolist(),landing_preference_local_xy=frozen.tolist(),planning_xy_reserve_m=.0005)
try:apply({},state,{},event,object_xyz=new.target,object_rotation=new.rotation)
except ValueError as e:reason=str(e)
else:raise AssertionError('Expected reproduced mismatch')
assert reason=='Trailing handover preference differs from actual object rotation'
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest();out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,reproduced=True,original_motion_gate=motion,desired_offset_difference_m=float(max(abs(frozen-actual))),actual_xy_gate_would_pass=True,adapter_rejected=reason,source_sha256={str(x):sha(x) for x in [Path(__file__),D/'trailing_adapter.py',D/'trailing_lifecycle.py',src,S/'recontact_scene.py']},physical_launch_ready=False,training_ready=False)
with (D/'ROTATION_CAPTURE_BOUNDARY.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='source_sha256'}))
