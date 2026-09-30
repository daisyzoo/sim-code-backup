import unittest
from simfoundry.data.initial_top_route_candidate import initial_top_route_candidate
Q=(0,0,0,1);BOX=(.14,.09,.045);BAG=(.15,.145,.04)
class InitialTopProposalTests(unittest.TestCase):
 def test_far_depth_slot_proposed_for_both_categories(self):
  for direction,size,other in ((-1,BOX,BAG),(1,BAG,BOX)):
   r=initial_top_route_candidate((.60,-.01,.77),(.39,.01,.77),size,other,Q,Q,direction)
   self.assertTrue(r['proposed']);self.assertGreater(r['transfer_m'],.18)
 def test_mirrored_slots_and_direction_give_same_decision(self):
  a=initial_top_route_candidate((.6,.08,.77),(.39,-.08,.77),BOX,BAG,Q,Q,-1)
  b=initial_top_route_candidate((.6,-.08,.77),(.39,.08,.77),BOX,BAG,Q,Q,1)
  self.assertEqual(a['proposed'],b['proposed']);self.assertAlmostEqual(a['transfer_m'],b['transfer_m'])
 def test_clear_minimum_progress_transfer_and_explicit_legacy_threshold(self):
  r=initial_top_route_candidate((.55,-.12,.77),(.4,.12,.77),BOX,BAG,Q,Q,-1)
  self.assertTrue(r['proposed'])
  legacy=initial_top_route_candidate((.55,-.12,.77),(.4,.12,.77),BOX,BAG,Q,Q,-1,min_transfer_m=.18)
  self.assertFalse(legacy['proposed']);self.assertIn('short transfer retains existing routing',legacy['reasons'])
 def test_blocked_direct_path_not_promoted(self):
  r=initial_top_route_candidate((.55,.15,.77),(.52,-.12,.77),BOX,BAG,Q,Q,-1)
  self.assertFalse(r['proposed']);self.assertIn('direct object envelope not clear',r['reasons'])
 def test_clear_near_transfer_can_use_top_contact(self):
  r=initial_top_route_candidate((.39,.12,.77),(.6,-.12,.77),BOX,BAG,Q,Q,-1)
  self.assertTrue(r['proposed'])
  with self.assertRaises(ValueError):initial_top_route_candidate((.6,0,.77),(.39,0,.77),BOX,BAG,Q,Q,-1,min_transfer_m=float('nan'))
 def test_failed_far_box_short_of_old_threshold_is_now_eligible(self):
  r=initial_top_route_candidate((.576972,-.026315,.772476),(.395370,-.075583,.769976),BOX,BAG,Q,Q,-1)
  self.assertTrue(r['proposed'])
  self.assertGreater(r['transfer_m'],.15)
  self.assertLess(r['transfer_m'],.18)
if __name__=='__main__':unittest.main()
