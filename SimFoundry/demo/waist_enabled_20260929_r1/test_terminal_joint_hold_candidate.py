import unittest
from terminal_joint_hold_candidate import TerminalJointHold
class HoldTests(unittest.TestCase):
 def fixture(self):return dict(mode='top_release',target_confirmed=True,hand_clearance_m=.03,load_n=0.,active_error_m=.003,inactive_error_m=.003,other_max_xy_m=0.,current_upper_q=[.2]*11,previous_upper_command=[.201]*11)
 def test_confirm_and_latch_existing_command_no_jump(self):
  s=TerminalJointHold();a=self.fixture()
  for _ in range(4):self.assertIsNone(s.observe(**a))
  self.assertEqual(s.observe(**a),tuple(a['previous_upper_command']));a['previous_upper_command']=[.3]*11;self.assertEqual(s.observe(**a),tuple([.201]*11))
 def test_each_unready_condition_prevents_hold(self):
  for change in [dict(mode='hold'),dict(mode='front_guard_lift'),dict(target_confirmed=False),dict(hand_clearance_m=.019),dict(load_n=.2),dict(active_error_m=.013),dict(inactive_error_m=.016),dict(other_max_xy_m=.016),dict(current_upper_q=[.3]*11)]:
   s=TerminalJointHold()
   for _ in range(8):self.assertIsNone(s.observe(**dict(self.fixture(),**change)))
 def test_confirmation_must_be_consecutive(self):
  s=TerminalJointHold();a=self.fixture()
  for _ in range(4):s.observe(**a)
  s.observe(**dict(a,load_n=1.))
  for _ in range(4):self.assertIsNone(s.observe(**a))
  self.assertIsNotNone(s.observe(**a))
 def test_guard_or_new_contact_revokes_hold(self):
  for change in [dict(mode='front_guard_lift'),dict(load_n=.3),dict(target_confirmed=False)]:
   state=TerminalJointHold()
   for _ in range(5):state.observe(**self.fixture())
   self.assertIsNotNone(state.command)
   self.assertIsNone(state.observe(**dict(self.fixture(),**change)));self.assertIsNone(state.command)
 def test_invalid_measurements_rejected(self):
  for change in [dict(load_n=float('nan')),dict(current_upper_q=[0.]*10),dict(previous_upper_command=[float('inf')]*11)]:
   with self.assertRaises(ValueError):TerminalJointHold().observe(**dict(self.fixture(),**change))
if __name__=='__main__':unittest.main()
