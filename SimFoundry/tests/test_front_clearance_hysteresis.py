import unittest
from simfoundry.data.front_clearance_progress import FrontClearanceProgress
class HysteresisTests(unittest.TestCase):
 def candidate(self):return FrontClearanceProgress(.012,.12,confirm_nominal_clearance=True,recovery_hysteresis_m=.001)
 def lateral(self,s):
  for _ in range(3):r=s.update(.0121,.12)
  self.assertEqual(r['route_stage'],'lateral_y')
 def test_band_prevents_repeated_small_clearance_oscillation(self):
  s=self.candidate();self.lateral(s)
  for _ in range(100):
   for gap in (.0116,.0121):self.assertEqual(s.update(gap,-.02)['route_stage'],'lateral_y')
  self.assertEqual(s.recoveries,0)
 def test_below11mm_still_recovers_and_latches_current_y(self):
  s=self.candidate();self.lateral(s);r=s.update(.0109,-.071)
  self.assertEqual(r['route_stage'],'front_x');self.assertEqual(r['front_hold_y'],-.071)
  self.assertEqual(r['recover_clearance_m'],.011)
 def test_reentry_requires_original_nominal_three_observations(self):
  s=self.candidate();self.lateral(s);s.update(.0109,.02)
  for _ in range(100):self.assertEqual(s.update(.0119,.02)['route_stage'],'front_x')
  for _ in range(2):self.assertEqual(s.update(.0121,.02)['route_stage'],'front_x')
  self.assertEqual(s.update(.0121,.02)['route_stage'],'lateral_y')
 def test_default_behavior_is_unchanged(self):
  s=FrontClearanceProgress(.012,.12,confirm_nominal_clearance=True);self.lateral(s)
  self.assertEqual(s.update(.0119,.01)['route_stage'],'front_x')
 def test_invalid_hysteresis_rejected(self):
  for value in (-.001,.0011,float('nan')):
   with self.assertRaises(ValueError):FrontClearanceProgress(.012,.12,recovery_hysteresis_m=value).update(.02,.12)
from simfoundry.data.front_top_route import FrontTopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState,frontal_bypass_plan
class HalfMillimeterIntegrationTests(unittest.TestCase):
 def test_observed_band_then_recovery_and_original_emergency(self):
  plan=frontal_bypass_plan((.4,.12,.7725),(.55,-.12,.77),(.14,.09),(.15,.145),0.,0.,-1)
  s=FrontTopRouteState(FrontalBypassState(plan),'right',(.14,.09,.045),guarded_descent=True,continuous_drag=True,route_clearance_m=.012,recover_clearance=True,confirm_nominal_clearance=True,recovery_hysteresis_m=.0005)
  def call(x,y=.12):
   tip=(.35,y,.795)
   return s.update(tip,(x,y,.7725),(.55,-.12,.77),.07,.075,tip=tip,quat=(0,0,0,1),obstacle_quat=(0,0,0,1),control_offset_local=(.2,0,0),load_n=5.,hand_obstacle_gap_m=.1)
  call(.4)
  for _ in range(3):r=call(.3929)
  self.assertEqual(r['route_stage'],'lateral_y')
  self.assertEqual(call(.3934,-.04)['route_stage'],'lateral_y')
  r=call(.3936,-.05);self.assertEqual(r['route_stage'],'front_x')
  self.assertAlmostEqual(r['clearance_progress']['front_hold_y'],-.05)
  self.assertAlmostEqual(r['clearance_progress']['recover_clearance_m'],.0115)
  self.assertEqual(call(.3951,-.05)['route_stop_reason'],'parcel_clearance_10mm')
 def test_half_millimeter_boundary_requires_original_confirmation(self):
  s=FrontClearanceProgress(.012,.12,confirm_nominal_clearance=True,recovery_hysteresis_m=.0005)
  for _ in range(3):s.update(.0121,.12)
  self.assertEqual(s.update(.0116,.0)['route_stage'],'lateral_y')
  self.assertEqual(s.update(.0114,.0)['route_stage'],'front_x')
  for _ in range(20):self.assertEqual(s.update(.0119,.0)['route_stage'],'front_x')
  for _ in range(2):self.assertEqual(s.update(.0121,.0)['route_stage'],'front_x')
  self.assertEqual(s.update(.0121,.0)['route_stage'],'lateral_y')
if __name__=='__main__':unittest.main()
