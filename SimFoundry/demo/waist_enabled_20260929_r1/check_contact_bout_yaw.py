from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;stage=w/'staged_contact_bout_yaw';sys.path.insert(0,str(stage))
from contact_bout_yaw import ContactBoutYaw,contact_bout_yaw_constraint
rng=np.random.default_rng(310930);max_error=0.;count=0
for _ in range(40):
 r=Rotation.random(random_state=rng).as_matrix();state=ContactBoutYaw();a=state.update('top_push',r);j=rng.normal(size=(3,11));v=contact_bout_yaw_constraint(r,j,a);assert abs(v['heading_error_rad'])<1e-12
 for col in range(11):
  h=1e-6;heads=[]
  for sign in (-1,1):
   pert=Rotation.from_rotvec(sign*h*j[:,col]).as_matrix()@r;heads.append(contact_bout_yaw_constraint(pert,j,a)['current_heading_rad'])
  derivative=np.arctan2(np.sin(heads[1]-heads[0]),np.cos(heads[1]-heads[0]))/(2*h)*.15
  max_error=max(max_error,abs(derivative-v['jacobian'][0,col]));count+=1
 assert state.update('top_push',Rotation.from_euler('z',.02).as_matrix()@r)==a
 for mode in ['top_lift','top_cross','top_descend','top_press','initial_top_guard_lift','front_guard_lift','top_release','idle']:
  state.update('top_push',r);assert state.update(mode,None) is None and state.axis is None
 assert abs(contact_bout_yaw_constraint(Rotation.from_euler('z',np.pi-.01).as_matrix(),np.eye(3),{'axis':0,'target_heading_rad':-np.pi+.01})['heading_error_rad']-.02)<1e-12
assert max_error<1e-7
for r in [np.full((3,3),np.nan),np.zeros((3,3))]:
 try:ContactBoutYaw().update('top_push',r)
 except ValueError:pass
 else:raise AssertionError('invalid rotation accepted')
report=dict(passed=True,random_rotations=40,finite_difference_columns=count,max_jacobian_error=max_error,reset_modes=8,scope='Pure helper lifecycle/angle wrap/invalid input and analytic Jacobian checks only; no robot/physics proof.',candidate_sha256=hashlib.sha256((stage/'contact_bout_yaw.py').read_bytes()).hexdigest(),training_ready=False)
(stage/'PURE_CHECK.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
