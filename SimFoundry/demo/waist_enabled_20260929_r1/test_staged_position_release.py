"""Runs only under staged loader; no production integration or physics claim."""
import unittest
from simfoundry.data.top_contact_bypass import TopContactBypassState
from simfoundry.data.frontal_bypass import FrontalBypassState,frontal_bypass_plan
from simfoundry.data.front_top_route import FrontTopRouteState
class StagedReleaseTests(unittest.TestCase):
 def state(self,enabled=True):
  plan=frontal_bypass_plan((.46,-.15,.77),(.43,.15,.7725),(.15,.145),(.14,.09),0.,0.,1)
  return TopContactBypassState(FrontalBypassState(plan),'left',(.15,.145,.04),top_mode='top_push',command=(.56,.18,.79),guarded_descent=True,continuous_drag=True,confirm_terminal_release=enabled)
 def call(self,s,y=.203,tip=(.56,.18,.79),**extra):
  return s.update(tip,(.62,y,.77),(.43,.15,.7725),.075,.07,tip=tip,quat=(0,0,0,1),control_offset_local=(.2,0,0),load_n=3.,**extra)
 def test_ten_confirmed_frames_release_current_xy_and_unload(self):
  s=self.state()
  for _ in range(9):self.assertEqual(self.call(s)['mode'],'top_push')
  r=self.call(s);self.assertEqual(r['mode'],'top_release');self.assertEqual(r['target_xyz'],(.56,.18,.91))
  self.assertEqual(r['release_reason'],'confirmed_original_target_position');self.assertEqual(r['contact_load']['applied_z_bias_m'],0.)
 def test_default_keeps_old_margin(self):
  s=self.state(False)
  for _ in range(30):self.assertEqual(self.call(s)['mode'],'top_push')
 def test_original_margin_is_not_delayed(self):
  r=self.call(self.state(),y=.21)
  self.assertEqual(r['mode'],'top_release');self.assertEqual(r['release_reason'],'original_margin')
 def test_recovery_descend_can_finish_without_new_contact(self):
  s=self.state();s.top_mode='top_descend';s.descent_z=.86
  for _ in range(10):r=self.call(s,tip=(.56,.18,.86))
  self.assertEqual(r['mode'],'top_release');self.assertEqual(r['target_xyz'],(.56,.18,.91))
 def test_temporary_zone_crossing_does_not_release(self):
  s=self.state()
  for _ in range(9):self.call(s)
  self.assertEqual(self.call(s,y=.199)['mode'],'top_push')
  for _ in range(9):self.assertEqual(self.call(s)['mode'],'top_push')
  self.assertEqual(self.call(s)['mode'],'top_release')
 def test_release_remains_latched(self):
  s=self.state()
  for _ in range(10):self.call(s)
  r=self.call(s,y=.18,tip=(.56,.18,.89));self.assertEqual(r['mode'],'top_release');self.assertEqual(r['target_xyz'],(.56,.18,.91))
 def test_top_edge_guard_precedes_new_release(self):
  s=self.state();s.corner_contact=True;s.forward_margin_m=.04;s.edge_guard_m=.012
  for _ in range(9):self.call(s)
  r=self.call(s,loaded_contact=dict(valid=True,normal_load_n=3.,weighted_forward_edge_distance_m=.001))
  self.assertEqual(r['mode'],'top_lift');self.assertEqual(r['last_recontact_reason'],'loaded_edge_margin')
  self.assertIsNone(r['release_reason'])
 def test_invalid_unguarded_combination_rejected(self):
  s=self.state();s.guarded_descent=False
  with self.assertRaisesRegex(ValueError,'guarded continuous'):self.call(s)
 def test_front_existing_emergency_guard_precedes_confirmation(self):
  for guard,reason in [('hand','hand_obstacle_gap_5mm'),('other','non_target_motion_10mm')]:
   plan=frontal_bypass_plan((.4,.12,.7725),(.55,-.12,.77),(.14,.09),(.15,.145),0.,0.,-1)
   s=FrontTopRouteState(FrontalBypassState(plan),'right',(.14,.09,.045),guarded_descent=True,continuous_drag=True,confirm_terminal_release=True,route_clearance_m=.012,recover_clearance=True,confirm_nominal_clearance=True,recovery_hysteresis_m=.0005)
   def call(target=(.4,.12,.7725),gap=.1,other=(.55,-.12,.77)):
    tip=(.332,target[1],.795)
    return s.update(tip,target,other,.07,.075,tip=tip,quat=(0,0,0,1),obstacle_quat=(0,0,0,1),control_offset_local=(.2,0,0),load_n=5.,hand_obstacle_gap_m=gap)
   call();s.top_mode='top_push';s.command=(.332,-.203,.795)
   for _ in range(9):self.assertEqual(call((.382,-.203,.7725))['mode'],'top_push')
   r=call((.382,-.203,.7725),gap=.004 if guard=='hand' else .1,other=(.55,-.108,.77) if guard=='other' else (.55,-.12,.77))
   self.assertEqual(r['mode'],'front_guard_lift');self.assertEqual(r['route_stop_reason'],reason)
