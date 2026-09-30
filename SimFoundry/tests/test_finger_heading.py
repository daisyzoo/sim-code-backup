"""Check heading derivative against independent finite rotations, plus DLS bounds."""
import unittest
import numpy as np
import torch
from scipy.spatial.transform import Rotation
from test_bounded_servo import controller

class HeadingTests(unittest.TestCase):
 def test_angular_derivative(self):
  fn=controller()['finger_heading_row'];rng=np.random.default_rng(42)
  for _ in range(100):
   a=rng.normal(size=3);a/=np.linalg.norm(a)
   if np.linalg.norm(a[:2])<.2:continue
   omega=rng.normal(size=3);eps=1e-6
   b=Rotation.from_rotvec(eps*omega).apply(a);c=Rotation.from_rotvec(-eps*omega).apply(a)
   numeric=np.arctan2(np.sin(np.arctan2(b[1],b[0])-np.arctan2(c[1],c[0])),np.cos(np.arctan2(b[1],b[0])-np.arctan2(c[1],c[0])))/(2*eps)
   self.assertAlmostEqual(float(fn(torch.tensor(a))@torch.tensor(omega)),numeric,places=6)
 def test_step_finite_and_bounded(self):
  f=controller()['heading_position_step'];g=torch.Generator().manual_seed(41)
  for a in [[0.,0.,1.],[1.,0.,0.],[-1.,.01,0.]]:
   dq=f(torch.randn(3,5,generator=g),torch.randn(3,5,generator=g),torch.ones(3)*.035,torch.tensor(a),.08)
   self.assertTrue(torch.isfinite(dq).all());self.assertLessEqual(float(dq.abs().max()),.055001)
if __name__=='__main__':unittest.main()
