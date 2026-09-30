import unittest
from simfoundry.data.front_clearance_progress import FrontClearanceProgress
class Tests(unittest.TestCase):
 def test_stable_nominal_clearance_can_resume_without_unreachable_reserve(self):
  s=FrontClearanceProgress(.012,.12,confirm_nominal_clearance=True)
  self.assertEqual(s.update(.01249,.12)['route_stage'],'front_x')
  self.assertEqual(s.update(.01248,.12)['route_stage'],'front_x')
  r=s.update(.01247,.12);self.assertEqual(r['route_stage'],'lateral_y');self.assertEqual(r['clearance_resume_reason'],'nominal_clearance_confirmed_3')
 def test_old_default_preserved(self):
  s=FrontClearanceProgress(.012,.12)
  for _ in range(100):self.assertEqual(s.update(.01249,.12)['route_stage'],'front_x')
 def test_unsafe_sample_breaks_consecutive_confirmation(self):
  s=FrontClearanceProgress(.012,.12,confirm_nominal_clearance=True)
  for g in (.0124,.0124,.01199,.0124,.0124):self.assertEqual(s.update(g,.12)['route_stage'],'front_x')
  self.assertEqual(s.update(.0124,.12)['route_stage'],'lateral_y')
 def test_no_timeout_exit_when_below_required_clearance(self):
  s=FrontClearanceProgress(.012,.12,confirm_nominal_clearance=True)
  for _ in range(2000):self.assertEqual(s.update(.01199,.12)['route_stage'],'front_x')
 def test_recovery_relatches_current_y_and_requires_fresh_confirmation(self):
  s=FrontClearanceProgress(.012,.12,confirm_nominal_clearance=True);s.update(.02,.12)
  r=s.update(.0119,-.1);self.assertEqual(r['front_hold_y'],-.1);self.assertEqual(r['safe_clearance_observations'],0)
  for i in range(3):r=s.update(.01249,-.101)
  self.assertEqual(r['route_stage'],'lateral_y');self.assertEqual(r['front_hold_y'],-.1)
if __name__=='__main__':unittest.main()
