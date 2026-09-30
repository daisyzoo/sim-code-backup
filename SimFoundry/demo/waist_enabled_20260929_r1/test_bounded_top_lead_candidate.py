import unittest,math
from types import SimpleNamespace as NS
from bounded_top_lead_candidate import BoundedTopLead,route_goal
class LeadChecks(unittest.TestCase):
 def test_stalled_object_cannot_accumulate_unbounded_desired_lead(self):
  a=BoundedTopLead()
  for _ in range(100):r=a.update('top_push',(.5,.1),(.5,-.34),(.5,.1))
  self.assertAlmostEqual(r['command_xy'][1],.076);self.assertAlmostEqual(r['desired_xy'][1],.076)
 def test_motion_follows_object_in_both_directions(self):
  for sign in (-1,1):
   a=BoundedTopLead()
   for t in range(80):
    y=sign*t*.001;r=a.update('top_push',(.5,y),(.5,sign*.34),(.5,y))
    self.assertLessEqual(abs(r['command_xy'][1]-r['previous_xy'][1]),.00300000001)
    self.assertLessEqual(abs(r['desired_xy'][1]-y),.02400000001)
   self.assertAlmostEqual(r['command_xy'][1],y+sign*.024)
 def test_guard_release_resets_and_reacquires_from_measured_reference(self):
  for mode in ('front_guard_lift','top_lift','top_release','goal_release','top_press'):
   a=BoundedTopLead();a.update('top_push',(.5,.1),(.5,-.34),(.5,.1))
   self.assertIsNone(a.update(mode,(.5,.1),(.5,-.34),(.5,.1)));self.assertIsNone(a.previous)
   r=a.update('top_push',(.6,.2),(.6,-.34),(.59,.205));self.assertEqual(r['previous_xy'],(.59,.205))
 def test_sudden_object_motion_is_not_hidden_as_hard_command_bound(self):
  a=BoundedTopLead();a.update('top_push',(.5,.1),(.5,-.34),(.5,.1))
  r=a.update('top_push',(.5,.25),(.5,-.34),(.5,.1));self.assertTrue(r['slew_limited']);self.assertGreater(abs(r['command_relative_object_xy_m'][1]),.024)
 def test_route_goals_preserve_front_clearance_order(self):
  state=NS(rear=NS(plan=dict(initial_target_xyz=(.4,-.12,.77),direction=1)),route_report=dict(goal_y=.205))
  row=dict(mode='top_push',route_stage='front_x',route_goal_x=.37,clearance_progress=dict(front_hold_y=-.10))
  self.assertEqual(route_goal(state,row),(.37,-.10));row['route_stage']='lateral_y';self.assertEqual(route_goal(state,row),(.37,.205))
  row['mode']='front_guard_lift';self.assertIsNone(route_goal(state,row))
 def test_invalid_inputs_fail(self):
  for lead in (.0,.011,.031,float('nan')):
   with self.assertRaises(ValueError):BoundedTopLead(lead).update('top_push',(.5,.1),(.5,-.34),(.5,.1))
  with self.assertRaises(ValueError):BoundedTopLead().update('top_push',(.5,math.inf),(.5,-.34),(.5,.1))
if __name__=='__main__':unittest.main()
