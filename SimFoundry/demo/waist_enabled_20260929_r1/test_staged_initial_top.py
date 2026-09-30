"""Isolated route behavior, not simulator dynamics or feasibility evidence."""
import unittest
from simfoundry.data.initial_top_route import InitialTopRouteState
from simfoundry.data.frontal_bypass import frontal_bypass_plan,FrontalBypassState
Q=(0,0,0,1)
class InitialTopTests(unittest.TestCase):
 def state(self):
  plan=frontal_bypass_plan((.6,-.01,.7725),(.39,.01,.77),(.14,.09),(.15,.145),0.,0.,-1)
  self.assertFalse(plan['required'])
  return InitialTopRouteState(FrontalBypassState(plan),'right',(.14,.09,.045),guarded_descent=True,continuous_drag=True,confirm_terminal_release=True,hold_established_x=True)
 def call(self,s,target=(.6,-.01,.7725),other=(.39,.01,.77),tip=(.3,-.1,.8),gap=.1,load=0.):
  return s.update(tip,target,other,.07,.075,tip=tip,quat=Q,obstacle_quat=Q,control_offset_local=(.2,0,0),load_n=load,hand_obstacle_gap_m=gap)
 def test_direct_eligible_starts_from_measured_support_without_rear_push(self):
  s=self.state();r=self.call(s)
  self.assertEqual(r['mode'],'top_lift');self.assertEqual(r['target_xyz'],(.3,-.1,.91))
  self.assertFalse(s.rear.plan['required']);self.assertTrue(r['initial_top_selected'])
 def test_no_load_never_enters_push(self):
  s=self.state();self.call(s);r=self.call(s,tip=(.3,-.1,.91));xy=r['target_xyz'][:2]
  self.assertEqual(self.call(s,tip=(*xy,.91))['mode'],'top_descend')
  for _ in range(10):r=self.call(s,tip=(*xy,.795))
  self.assertEqual(r['mode'],'top_press')
  for _ in range(20):self.assertNotEqual(self.call(s,tip=(*xy,.795))['mode'],'top_push')
 def test_guard_latches_and_preserves_measured_reference(self):
  for kw,reason in [({'gap':.004},'hand_obstacle_gap_5mm'),({'other':(.39,.022,.77)},'non_target_motion_10mm'),({'target':(.811,-.01,.7725)},'target_table_margin_5mm'),({'target':(.54,.01,.7725)},'parcel_clearance_10mm')]:
   s=self.state();self.call(s);s.load.bias_m=-.005
   r=self.call(s,**kw);self.assertEqual(r['mode'],'initial_top_guard_lift');self.assertEqual(r['route_stop_reason'],reason)
   self.assertEqual(r['target_xyz'],(.3,-.1,.91));self.assertEqual(r['control_offset_local'],(.2,0,0));self.assertEqual(s.load.bias_m,0.)
   self.assertEqual(self.call(s,tip=(.4,.2,.8))['target_xyz'],(.3,-.1,.91))
 def test_blocked_or_unregistered_initial_route_rejected(self):
  s=self.state();s.rear.plan['required']=True
  with self.assertRaises(ValueError):self.call(s)
  s=self.state()
  with self.assertRaises(ValueError):self.call(s,target=(.45,-.01,.7725))
 def test_nonfinite_gap_rejected(self):
  with self.assertRaises(ValueError):self.call(self.state(),gap=float('nan'))
 def test_original_and_confirmed_release_still_work(self):
  s=self.state();self.call(s);s.top_mode='top_push';s.command=(.55,-.18,.795)
  for _ in range(10):r=self.call(s,target=(.6,-.203,.7725),tip=(.55,-.18,.795),load=3.)
  self.assertEqual(r['mode'],'top_release');self.assertEqual(r['target_xyz'],(.55,-.18,.91))
