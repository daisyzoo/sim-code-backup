import math,unittest
from simfoundry.data.cross_axis_admittance import CrossAxisAdmittance

class CrossAxisAdmittanceTests(unittest.TestCase):
 def test_force_sign_slew_and_total_bounds(self):
  for force in (-4.,4.):
   s=CrossAxisAdmittance();prior=0.
   for _ in range(100):
    r=s.update(force,True);self.assertLessEqual(abs(r['command_bias_x_m']-prior),.000500001);self.assertLessEqual(abs(r['command_bias_x_m']),.01);self.assertLessEqual(r['command_bias_x_m']*force,0);prior=r['command_bias_x_m']
   self.assertAlmostEqual(abs(s.bias_m),.01)
 def test_inactive_does_not_change_reference_and_reset_clears_history(self):
  s=CrossAxisAdmittance();s.update(2.,True);b=s.bias_m
  for _ in range(10):s.update(-4.,False)
  self.assertEqual(b,s.bias_m);s.reset();self.assertEqual(s.bias_m,0);self.assertEqual(s.filtered_force_n,0)
 def test_synthetic_spring_contact_converges_without_overshooting_bound(self):
  # Only a sign/stability check on a simple linear spring; not simulator proof.
  s=CrossAxisAdmittance();unwanted_preload_m=.005
  for _ in range(100):s.update(300*(unwanted_preload_m+s.bias_m),True)
  self.assertLess(abs(unwanted_preload_m+s.bias_m),1e-7)
 def test_nonfinite_force_rejected_before_mutation(self):
  s=CrossAxisAdmittance()
  for value in (math.nan,math.inf):
   with self.assertRaises(ValueError):s.update(value,True)
  self.assertEqual(s.bias_m,0)

if __name__=='__main__':unittest.main()
