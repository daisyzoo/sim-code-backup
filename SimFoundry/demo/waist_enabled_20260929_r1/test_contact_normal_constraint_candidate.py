import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from contact_normal_constraint_candidate import contact_normal_constraint
class NormalConstraintTests(unittest.TestCase):
 def test_finite_difference_world_angular_jacobian(self):
  rng=np.random.default_rng(913)
  for _ in range(8):
   r=Rotation.random(random_state=rng).as_matrix();j=rng.normal(size=(3,11));target=r.T@np.array([0.,0.,1.]);result=contact_normal_constraint(r,j,target);eps=1e-7
   fd=np.column_stack([.15*((Rotation.from_rotvec(eps*j[:,i]).as_matrix()@r).T[:,2]-(Rotation.from_rotvec(-eps*j[:,i]).as_matrix()@r).T[:,2])/(2*eps) for i in range(11)])
   np.testing.assert_allclose(result['jacobian'],fd,atol=1e-8);np.testing.assert_allclose(result['error'],0,atol=1e-10)
 def test_global_yaw_free_but_tilt_detected(self):
  r=Rotation.from_euler('xyz',[.2,-.1,.5]).as_matrix();n=r.T@np.array([0.,0.,1.]);yaw=Rotation.from_euler('z',1.1).as_matrix()@r
  result=contact_normal_constraint(yaw,np.eye(3),n);np.testing.assert_allclose(result['error'],0,atol=1e-12);np.testing.assert_allclose(result['jacobian'][:,2],0,atol=1e-12)
  tilt=Rotation.from_euler('x',.1).as_matrix()@r;self.assertAlmostEqual(contact_normal_constraint(tilt,np.eye(3),n)['angle_error_rad'],.1)
 def test_invalid_inputs(self):
  for r,j,t,w in [(np.eye(3),np.eye(3),[0,0,2],.15),(np.zeros((3,3)),np.eye(3),[0,0,1],.15),(np.eye(3),np.ones((2,11)),[0,0,1],.15),(np.eye(3),np.eye(3),[0,0,1],float('nan'))]:
   with self.assertRaises(ValueError):contact_normal_constraint(r,j,t,w)
 def test_bounded_correction_direction(self):
  r=Rotation.from_euler('x',.3).as_matrix();result=contact_normal_constraint(r,np.eye(3),[0,0,1]);step=np.linalg.lstsq(result['jacobian'],result['error'],rcond=None)[0];new=Rotation.from_rotvec(step).as_matrix()@r
  self.assertLess(contact_normal_constraint(new,np.eye(3),[0,0,1])['angle_error_rad'],result['angle_error_rad']);self.assertLessEqual(np.max(abs(result['error'])),.015+1e-12)
if __name__=='__main__':unittest.main()
