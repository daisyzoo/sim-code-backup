import math
import unittest
from simfoundry.data.reach_sweep import retreating_sweep_x, ready_to_release, sweep_exit_y

class ReachSweepTests(unittest.TestCase):
    def test_contact_start_and_mirrored_terminal_positions(self):
        for direction in (-1,1):
            self.assertEqual(retreating_sweep_x(.60,-direction*.12,direction,.30,.08),.60)
            self.assertEqual(retreating_sweep_x(.60,direction*.08,direction,.30,.08),.60)
            self.assertAlmostEqual(retreating_sweep_x(.60,direction*.30,direction,.30,.08),.52)
            self.assertAlmostEqual(retreating_sweep_x(.60,direction*.50,direction,.30,.08),.52)

    def test_near_contact_is_not_pulled_through_floor(self):
        self.assertEqual(retreating_sweep_x(.39,.3,1,.3,.08),.39)
        self.assertEqual(retreating_sweep_x(.52,.3,1,.3,.08),.50)
        self.assertEqual(retreating_sweep_x(.60,.3,1,.3,0),.60)

    def test_invalid_geometry_is_rejected(self):
        for args in [(math.nan,.1,1,.3,.08),(.6,.1,0,.3,.08),(.6,.1,1,.08,.08),(.6,.1,1,.3,.11)]:
            with self.assertRaises(ValueError):retreating_sweep_x(*args)

    def test_release_preserves_both_original_goal_requirements(self):
        for direction in (-1,1):
            self.assertFalse(ready_to_release(0,direction*.200,direction))
            self.assertTrue(ready_to_release(0,direction*.206,direction))
            self.assertFalse(ready_to_release(direction*.15,direction*.25,direction))
            self.assertTrue(ready_to_release(direction*.15,direction*.32,direction))

    def test_nonfinite_release_feedback_rejected(self):
        with self.assertRaises(ValueError):ready_to_release(0,math.nan,1)

    def test_far_endpoint_does_not_extend_near_paths(self):
        self.assertEqual(sweep_exit_y(.39,.30,.34),.30)
        self.assertEqual(sweep_exit_y(.60,.30,.34),.34)
        self.assertEqual(sweep_exit_y(.60,.30,0),.30)
        with self.assertRaises(ValueError):sweep_exit_y(.60,.30,.40)
