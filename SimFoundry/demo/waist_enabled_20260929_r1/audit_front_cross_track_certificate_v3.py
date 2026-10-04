"""Strict metadata plus independent support branch checks around original KKT FD.
Never import candidate solver or its support function. No physical certificate.
"""
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from audit_unloaded_wrist_prior_live import HandModel
from audit_front_cross_track_nonreversal_candidate_v1 import verify as original_verify

def verify(record,task,coordinate,*,guard,elbow_reserve_m,quarter_enabled=False):
 spec=record.get('cross_track_nonreversal');side=record['side'];xr=0 if side=='left' else 3;direction=float(np.sign(task['error'][xr]))
 import math
 if not isinstance(spec,dict) or type(spec.get('axis')) is not int:raise ValueError('Noninteger cross-track axis')
 for name in ['requested_direction','original_requested_x_m','parent_signed_nominal_dx_m','proposal_signed_nominal_dx_m','threshold_m','rounding_tolerance_m']:
  value=spec.get(name)
  if type(value) not in (int,float) or not math.isfinite(value):raise ValueError('Invalid finite cross-track metadata '+name)
 if not isinstance(spec,dict) or spec.get('enabled') is not True or spec.get('axis')!=0 or spec.get('threshold_m')!=0. or spec.get('rounding_tolerance_m')!=2e-7 or direction==0 or spec.get('requested_direction')!=direction or spec.get('original_requested_x_m')!=task['error'][xr]:raise ValueError('Unbound nonreversal contract')
 root=Path(__file__).resolve().parents[2];hand=HandModel(root/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',root/'assets/robots/g1_hand_support_vertices.json');normal=Rotation.from_quat(record['scene']['target_quat']).as_matrix()[:,2];center=np.array(coordinate['active_support_reference']['center_local']);q=np.array(record['current']);u=np.array(record['command']);parent=np.array(record['parent_command']);vertices=hand.vertices[side]
 def point(x):
  T=hand.fk(x,side);n=T[:3,:3].T@normal;values=vertices@n;idx=int(np.argmin(values));off=center+n*(values[idx]-center@n);return T[:3,3]+T[:3,:3]@off,idx,float(np.partition(values,1)[1]-values[idx])
 current=point(q)[0];actual=direction*(point(u)[0][0]-current[0]);old=direction*(point(parent)[0][0]-current[0])
 if abs(actual-spec['proposal_signed_nominal_dx_m'])>1e-10 or abs(old-spec['parent_signed_nominal_dx_m'])>1e-10:raise ValueError('Incorrect recorded independent cross-track margin')
 checks=[point(x) for x in [u,*[u+sign*np.eye(11)[j]*2e-7 for j in range(11) for sign in [-1,1]]]];regular=dict(fd_step=2e-7,stable_index=len({x[1] for x in checks})==1,minimum_separation_m=min(x[2] for x in checks));regular['passed']=bool(regular['stable_index'] and regular['minimum_separation_m']>1e-12)
 if not regular['passed']:return dict(passed=False,reason='unverified_support_minimum_branch',regularity=regular)
 result=original_verify(record,task,coordinate,guard=guard,elbow_reserve_m=elbow_reserve_m,quarter_enabled=quarter_enabled)
 return dict(result,strict_metadata_checked=True,support_branch_regularity=regular,independent_signed_dx_m=float(actual))
