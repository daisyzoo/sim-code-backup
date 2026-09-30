import math,unittest
import test_staged_position_release as release_tests
class ContactStabilityTests(unittest.TestCase):
 def state(self,enabled=True):
  s=release_tests.StagedReleaseTests().state();s.tilt_recontact_rad=.03 if enabled else 0.;return s
 def call(self,s,tilt=.04,y=.203,tip=(.56,.18,.79)):
  return s.update(tip,(.62,y,.77),(.43,.15,.7725),.075,.07,tip=tip,quat=(math.sin(tilt/2),0,0,math.cos(tilt/2)),control_offset_local=(.2,0,0),load_n=3.)
 def test_early_tilt_withdraws_without_position_release(self):
  s=self.state();r=self.call(s)
  self.assertEqual(r['mode'],'top_lift');self.assertEqual(r['last_recontact_reason'],'incipient_tilt_independent')
  self.assertEqual(r['target_xyz'],(.56,.18,.91));self.assertEqual(r['contact_load']['applied_z_bias_m'],0.)
 def test_disabled_preserves_behavior(self):
  self.assertEqual(self.call(self.state(False))['mode'],'top_push')
 def test_below_threshold_does_not_withdraw(self):
  self.assertEqual(self.call(self.state(),tilt=.029)['mode'],'top_push')
 def test_tilt_precedes_tenth_frame_confirmation(self):
  s=self.state()
  for _ in range(9):self.call(s,tilt=0.)
  r=self.call(s);self.assertTrue(r['terminal_position_confirmed']);self.assertEqual(r['mode'],'top_lift')
  self.assertIsNone(r['release_reason'])
 def test_tilt_precedes_original_margin(self):
  self.assertEqual(self.call(self.state(),y=.21)['mode'],'top_lift')
 def test_guard_not_retriggered_while_lifting(self):
  s=self.state();self.call(s);self.call(s);self.assertEqual(s.recontacts,1)
 def test_invalid_threshold_or_unguarded_rejected(self):
  for value in [float('nan'),float('inf'),-.01,.11]:
   s=self.state();s.tilt_recontact_rad=value
   with self.assertRaises(ValueError):self.call(s)
  s=self.state();s.guarded_descent=False
  with self.assertRaises(ValueError):self.call(s)
